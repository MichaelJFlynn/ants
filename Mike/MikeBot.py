#!/usr/bin/env python
from ants import *
import util
import sys
import logging
import time 

# define a class with a do_turn method
# the Ants.run method will parse and update bot input
# it will also run the do_turn method for us
class MyBot:
    def __init__(self):
        # define class level variables, will be remembered between turns
        pass
    
    # do_setup is run once at the start of the game
    # after the bot has received the game settings
    # the ants class is created and setup by the Ants.run method
    def do_setup(self, ants):
        # initialize data structures after learning the game settings
        self.hills = []
        self.unseen = []
        self.paths = {}
        self.max_time = 0
        self.turn_num = 1
        self.missions = {}
        self.areas = []
        for row in range(ants.rows):
            for col in range(ants.cols):
                self.unseen.append((row, col))
        self.hill_distances = {}

    # do turn is run once per turn
    # the ants class has the game state and is updated by the Ants.run method
    # it also has several helper methods to use
    def do_turn(self, ants):
        
        start_time = int(round(time.time()*1000))
        ## I decided in the end to clear areas every round because
        ## they didn't seem that expensive to calculate
        self.areas = []
        
        ## targets are used to make sure ants aren't all going towards
        ## the same food particle, which they seem to do anyways
        targets = {}

        ## keeps track of movement, makes sure no ant is commanded to
        ## move twice
        orders = {} 

        food = ants.food()
        my_ants = ants.my_ants()

        def get_neighbors(loc):
            directions = ['e', 'w', 'n', 's']
            neighbors = []
            for direction in directions:
                ## if it's not water, include it
                new_loc = ants.destination(loc, direction)
                if ants.passable(new_loc):
                    neighbors.append((new_loc, direction))
            return neighbors

        def isFood(loc):
            if loc in food:
                return True
            else:
                return False

        def isMyAnt(loc):
            if loc in my_ants:
                return True
            else:
                return False
                
        ## bfs, copied from pacman, modified a little (goalfun)
        def bfs(init_loc, goalfun):
            visited = []
            start = (init_loc, [], 0)
            if goalfun(init_loc):
                return ([], init_loc, 0)
            frontier = util.Queue()
            frontier.push(start)
            visited.append(init_loc)
            while not frontier.isEmpty():
                cur_loc, cur_path, cur_depth = frontier.pop()
                if goalfun(cur_loc):
                    return (cur_path, cur_loc, cur_depth)
                for loc, direction in get_neighbors(cur_loc):
                    path = [x for x in cur_path]
                    path.append(direction)
                    if not loc in visited:
                        visited.append(loc)
                        frontier.push((loc, path, cur_depth + 1))
            ## return that there is no valid path
            return ([], None, None)

        ## bfs that returns a path to the closest position at limited
        ## depth with the smallest distance, according to distfun
        def depth_limited_bfs(init_loc, goalfun, depth_limit, distfun):
            visited = []
            edge = util.PriorityQueue()
            edge.push(([], init_loc, 0), 99999)
            start = (init_loc, [], 0)
            if goalfun(init_loc):
                return ([], init_loc, 0)
            frontier = util.Queue()
            frontier.push(start)
            visited.append(start[0])
            while not frontier.isEmpty():
                cur_loc, cur_path, cur_depth = frontier.pop()
                ## add in a distfun call for access to the depth
                distfun(cur_loc, cur_depth)
                if goalfun(cur_loc):
                    return (cur_path, cur_loc, cur_depth)
                if cur_depth < depth_limit:
                    for loc, direction in get_neighbors(cur_loc):
                        path = [x for x in cur_path]
                        path.append(direction)
                        if not loc in visited:
                            distfun(loc, cur_depth + 1)
                            visited.append(loc)
                            frontier.push((loc, path, cur_depth + 1))
                else:
                    edge.push( (cur_path, cur_loc, cur_depth), distfun(cur_loc, cur_depth))
            return edge.pop()
            ##

        ## I never actually use this function...
        def opposite_direction(direction):
            if direction == 'n':
                return 's'
            if direction == 's':
                return 'n'
            if direction == 'e':
                return 'w'
            if direction == 'w':
                return 'e'

        ## if it can, will move to the position in the parameter
        ## direction and record that to orders
        def do_move_direction(loc, direction):
            new_loc = ants.destination(loc,direction)
            if ants.unoccupied(new_loc) and new_loc not in orders.keys() and loc not in orders.values():
                ants.issue_order((loc,direction))
                orders[new_loc] = loc
                return True
            else:
                return False

        ## executes paths that have been set before
        def exec_paths():
            for ant_loc in self.paths.keys():
                path = self.paths.pop(ant_loc)
                goal = self.missions.pop(ant_loc)
                if do_move_direction(ant_loc, path[0]):
                    if len(path) > 1:
                        new_loc = ants.destination(ant_loc, path[0])
                        self.paths[new_loc] = path[1:]
                        self.missions[new_loc] = goal
                else:
                    for direction in ['n', 'e', 'w', 's']:
                        if do_move_direction(ant_loc, direction):
                            break

        ## this function is used as a hacky "distance function"
        ## for depth limited bfs to record a distance from the
        ## enemy hills
        def record_distance(loc, depth, hill_loc):
            if loc not in self.hill_distances[hill_loc].keys():
                self.hill_distances[hill_loc][loc] = depth
            return 1

        def move_to_hill(ant_loc):
            path, hill_loc, depth = depth_limited_bfs(ant_loc, lambda x: x in self.hills, 30, lambda x,y: min([v[x] for v in self.hill_distances.values()]))
            if len(path) > 0:
                if do_move_direction(ant_loc, path[0]):
                    new_loc = ants.destination(ant_loc, path[0])
                    self.missions[new_loc] = hill_loc
                    self.paths[new_loc] = path[1:]
        
        def add_area(loc, depth, origin):
            ## check which area contains the origin
            ## add this location to that area
            for area in self.areas:
                if origin in area:
                    if not loc in area:
                        area.append(loc)
                        ## check if location is enemy or friend
                        ## and expand area
                        if loc in ants.my_ants() or loc in [enemy for enemy, team in ants.enemy_ants()]:
                            depth_limited_bfs(loc, lambda x: False, 5, lambda x,y: add_area(x,y, loc))

            ## check if location is already in one or more areas
            check_duplicates = [i for i in range(len(self.areas)) if loc in self.areas[i]]
            ## if so, merge both areas
            if len(check_duplicates) > 1:
                logging.warning("merging areas")
                zero = check_duplicates[0]
                for i in check_duplicates[1:]:
                    for moving_loc in self.areas[i]:
                        if moving_loc not in self.areas[i]:
                            self.areas[zero].append(moving_loc)
                self.areas = [self.areas[i] for i in range(len(self.areas)) if i not in check_duplicates[1:]]
            
        ## create areas for doing minimax
        def create_areas():
            for enemy_loc, team in ants.enemy_ants():
                ##self.areas = [area for area in self.areas if enemy_loc not in area]
                if not any([enemy_loc in area for area in self.areas]):
                    self.areas.append([enemy_loc])
                    depth_limited_bfs(enemy_loc, lambda x: False, 5, lambda x,y: add_area(x,y, enemy_loc))
        
        ## clean up (delete areas where there is no possibility of
        ## a fight
        def clean_areas():
            self.areas = [area for area in self.areas if any([enemy_loc in area for enemy_loc, team in ants.enemy_ants()])]
            self.areas = [area for area in self.areas if any([friendly in area for friendly in ants.my_ants()])]
 
        ## "clumpy" fighting for those not in minimax
        def fight():
            for area in self.areas:
                friendly_ants = [loc for loc in area if loc in ants.my_ants()]
                enemy_ants = [loc for loc, team in ants.enemy_ants() if loc in area]
                for ant_loc in friendly_ants:
                    if ant_loc in self.paths.keys():
                        self.paths.pop(ant_loc)
                    if len(enemy_ants) > len(friendly_ants):
                        ## if there are more enemies than us we run
                        directions = ['n', 'e', 'w', 's']
                        directions = sorted(directions, key = lambda x: 1./(min([ants.distance(ants.destination(ant_loc, x), enemy) for enemy in enemy_ants])+1))
                        for d in directions:
                            if do_move_direction(ant_loc, d):
                                break
                    else:
                        directions = ['n', 'e', 'w', 's']
                        directions = sorted(directions, key = lambda x: sum([ants.distance(ants.destination(ant_loc, x), enemy) for enemy in enemy_ants]))# + [ants.distance(ants.destination(ant_loc, x), friend_loc) for friend_loc in friendly_ants]))
                        for d in directions:
                            if do_move_direction(ant_loc, d):
                                break
   
        ## minimax fighting
        def minimax_fight():
            ## minimax for one turn in each area
            for area in self.areas:
                friendly_ants = [ant_loc for ant_loc in ants.my_ants() if ant_loc in area]
                if len(friendly_ants) < 1:
                    continue
                
                enemy_ants = [ant_loc for ant_loc, team in ants.enemy_ants() if ant_loc in area]
                ## I only take the closest 3 friendly ants and
                ## unfriendly enemies because of minimax complexity
                friendly_ants = sorted(friendly_ants, key = lambda x: min([ants.distance(x, enemy) for enemy in enemy_ants]))[:3]
                enemy_ants = sorted(enemy_ants, key = lambda x: min([ants.distance(x, friend) for friend in friendly_ants]))[:3]
                
                ## actual minimax function, 'changes' is a dictionary
                ## from ants to directions to move in
                score, changes = minimax_battle(friendly_ants, enemy_ants, len(friendly_ants) + len(enemy_ants))

                ## move according to the minimax
                for ant in friendly_ants:
                    if changes[ant] != None:
                        if not do_move_direction(ant, changes[ant]):
                            logging.warning("Something went wrong with minimax: " + str(ant) + " " + str(changes[ant]))
                    else:
                        orders[ant] = ant
                
        def minimax_battle(friendly_ants, enemy_ants, depth):
            ## want furthest ants from enemies to go first
            if(depth == 0):
                ## if we are at the bottom of the tree we simulate a
                ## turn to calculate a score
                dead = []
                score = 0
                ## basically if there are more enemies than friends
                ## close to you, you die
                for ant_loc in friendly_ants:
                    enemies_in_range = [enemy for enemy in enemy_ants if ants.distance(ant_loc, enemy) <= ants.attackradius2]
                    for enemy in enemies_in_range:
                        friends_in_range = [friend for friend in friendly_ants if ants.distance(enemy, friend) <= ants.attackradius2]
                        if len(enemies_in_range) >= len(friends_in_range):
                            dead.append(ant_loc)
                            ## dying is not good
                            score = score - 2
                            break
                for enemy_loc in enemy_ants:
                    friends_in_range = [friend for friend in friendly_ants if ants.distance(enemy_loc, friend) <= ants.attackradius2]
                    for friend in friends_in_range:
                        enemies_in_range = [enemy for enemy in enemy_ants if ants.distance(enemy, friend) <= ants.attackradius2]
                        if len(friends_in_range) >= len(enemies_in_range):
                            dead.append(enemy_loc)
                            ## killing enemies is good
                            score = score + 5
                            break
                ## score modifiers: (actually didn't get to using this)
                distances = [ants.distance(friend, enemy)**(1./2) for friend in friendly_ants for enemy in enemy_ants if enemy not in dead and friend not in dead]
                if len(distances) > 0:
                    score = score# - sum(distances)/(len(distances)*max(distances))
                else:
                    ## don't take a 1 for 1!
                    if len([friendly for friendly in friendly_ants if friendly not in dead]) < 1:
                        score = -1000
                return (score, {})
            else:
                index = len(friendly_ants) + len(enemy_ants) - depth
                directions = ['n', 'e', 'w', 's']
                ## we first act on friendly ants, then enemies
                if index < len(friendly_ants):
                    ## we are maximizing
                    ant_loc = friendly_ants[index]
                    max_score = -9999
                    scores = {}
                    final_changes = {} 
                    for direction in directions:
                        new_loc = ants.destination(ant_loc, direction)
                        ## if terrain is impassible, don't consider that move
                        if new_loc in friendly_ants or new_loc in enemy_ants or not ants.passable(new_loc):
                            continue
                        ## calculate minimax for each direction
                        new_friendlies = [x for x in friendly_ants]
                        new_friendlies[index] = new_loc
                        score, changes = minimax_battle(new_friendlies, enemy_ants, depth -1)
                        scores[direction] = score
                        if score > max_score:
                            max_score = score
                            final_changes = changes 
                            final_changes[ant_loc] = direction
                    ## consider not moving
                    score, changes = minimax_battle(friendly_ants, enemy_ants, depth - 1)
                    scores["stay"] = score
                    if score >= max_score:
                        max_score = score
                        final_changes = changes
                        final_changes[ant_loc] = None
                    ## score modifiers
                    return (max_score, final_changes)
                else: 
                    ## we are minimizing
                    index = index - len(friendly_ants)
                    enemy_loc = enemy_ants[index]
                    min_score = 9999
                    scores = {}
                    final_changes = {}
                    for direction in directions:
                        new_loc = ants.destination(enemy_loc, direction)
                        if new_loc in friendly_ants or new_loc in enemy_ants or not ants.passable(new_loc):
                            continue
                        new_enemies = [x for x in enemy_ants]
                        new_enemies[index] = new_loc
                        score, changes = minimax_battle(friendly_ants, new_enemies, depth - 1)
                        scores[direction] = score
                        if score < min_score:
                            min_score = score
                            final_changes = changes
                            final_changes[enemy_loc] = direction
                    score, changes = minimax_battle(friendly_ants, enemy_ants, depth - 1) 
                    scores["stay"] = score
                    if score < min_score:
                        min_score = score
                        final_changes = changes
                        final_changes[enemy_loc] = None
                    return (min_score, final_changes)
                    
        ## fighting:
        clean_areas()
        create_areas()
        minimax_fight()
        fight()

        ## nonfighting:
        ## remove ants that already have paths from consideration and
        ## execute paths
        my_ants = [x for x in my_ants if x not in self.paths.keys() and x not in orders.values()]
        exec_paths()
        
        ## Find hills
        bad_hills = [hill_loc for hill_loc, team_num in ants.enemy_hills()]
        for hill in self.hills:
            if ants.visible(hill) and hill not in bad_hills:
                self.hills.remove(hill)
        for hill in bad_hills:
            if hill not in self.hills:
                logging.warning("Found their hill!: " + str(hill))
                self.hills.append(hill)
                self.hill_distances[hill] = dict()
                ## create a member of self.hill_distances
                dummy = depth_limited_bfs(hill_loc, lambda x: False, 1000, lambda x,y: record_distance(x, y, hill_loc))
        ## If past critical mass then attack enemy hills
        if len(my_ants) + len(self.paths.keys()) > 5 and len(self.hills) > 0:
            for ant_loc in my_ants:
                move_to_hill(ant_loc)



        else:
            ## Set unseen for exploring
            if len(self.unseen) == 0:
                for row in range(ants.rows):
                    for col in range(ants.cols):
                        ## if we've seen everything reset
                        self.unseen.append((row, col))
            for loc in self.unseen[:]:
                if ants.visible(loc):
                    self.unseen.remove(loc)

            ## Food and explore         
            for ant_loc in my_ants:
                path, food_loc, depth = depth_limited_bfs(ant_loc, lambda x: (x in food or x in self.unseen) and x not in self.missions.keys(), 20, lambda x,y: 1/(ants.distance(x, ant_loc) + 1))
                if len(path) > 0:
                    if do_move_direction(ant_loc, path[0]):
                        new_loc = ants.destination(ant_loc, path[0])
                        self.missions[new_loc] = food_loc
                        self.paths[new_loc] = path[1:]

        ## print out the turn and turn time spent
        end_time = int(round(time.time()*1000))
        diff = end_time - start_time
        if self.max_time < diff:
            self.max_time = diff
        logging.warning("turn " + str(self.turn_num) +", time: "+ str(end_time - start_time))
        self.turn_num = self.turn_num + 1



if __name__ == '__main__':
    # psyco will speed up python a little, but is not needed
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    
    try:
        # if run is passed a class with a do_turn method, it will do the work
        # this is not needed, in which case you will need to write your own
        # parsing function and your own game state class
        bot = MyBot() 
        Ants.run(bot)
        logging.warning(str(bot.max_time))
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')




