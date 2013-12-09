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
        targets = {}
        orders = {} 
        food = ants.food()
        my_ants = ants.my_ants()

        def get_neighbors(loc):
            directions = ['e', 'w', 'n', 's']
            neighbors = []
            for direction in directions:
                ## if it's water remove it
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

        '''
        ## if it can, will move towards a destination and add it to
        ## targets, if not, will return false
        def do_move_location(loc, dest):
            direction = bfs(loc, lambda x: x == dest)[0]
            if do_move_direction(loc, direction):
                targets[dest] = loc
                return True
            return False
            '''

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
            if(ants.unoccupied(new_loc) and new_loc not in orders and loc not in orders.values()):
                ants.issue_order((loc,direction))
                orders[new_loc] = loc
                return True
            else:
                return False

        def exec_paths():
            for ant_loc in self.paths.keys():
                path = self.paths.pop(ant_loc)
                goal = self.missions.pop(ant_loc)
                if len(path) < 1: 
                    logging.warning("No path from " + str(ant_loc))
                    sys.exit()
                ##logging.warning("Taking path from: " + str(ant_loc))
                if do_move_direction(ant_loc, path[0]):
                    if len(path) > 1:
                        new_loc = ants.destination(ant_loc, path[0])
                        self.paths[new_loc] = path[1:]
                        self.missions[new_loc] = goal
                else:
                    for direction in ['n', 'e', 'w', 's']:
                        if do_move_direction(ant_loc, direction):
                            break


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
                            depth_limited_bfs(loc, lambda x: False, 3, lambda x,y: add_area(x,y, loc))

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
                for i in check_duplicates[1:]:
                    self.areas.remove(self.areas[i])
            

        def create_areas():
            for enemy_loc, team in ants.enemy_ants():
                if not any([enemy_loc in area for area in self.areas]):
                    self.areas.append([enemy_loc])
                    depth_limited_bfs(enemy_loc, lambda x: False, 5, lambda x,y: add_area(x,y, enemy_loc))
        
        def clean_areas():
            for area in self.areas:
                if not any([enemy_loc in area for enemy_loc, team in ants.enemy_ants()]):
                    self.areas.remove(area)

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
                        directions = sorted(directions, key = lambda x: sum([ants.distance(ants.destination(ant_loc, x), enemy) for enemy in enemy_ants] + [ants.distance(ants.destination(ant_loc, x), friend_loc) for friend_loc in friendly_ants]))
                        for d in directions:
                            if do_move_direction(ant_loc, d):
                                break
   
        def fight2():
            ## minimax for one turn
            for area in self.areas:
                friendly_ants = [ant_loc for ant_loc in ants.my_ants() if ant_loc in area]
                enemy_ants = [ant_loc for ant_loc, team in ants.enemy_ants() if ant_loc in area]
                minimax_battle(friendly_ants, enemy_ants)


        '''
        # prevent stepping on own hill
        for hill_loc in ants.my_hills():
            orders[hill_loc] = None
            '''
        create_areas()
        clean_areas()
        fight()
        ## remove ants that already have paths from consideration and
        ## execute paths
        my_ants = [x for x in my_ants if x not in self.paths.keys()]
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
                ##logging.warning(str(self.hill_distances))
                #sys.exit()
        ## If past critical mass then attack enemy hills
        if len(my_ants) + len(self.paths.keys()) > 5 and len(self.hills) > 0:
            for ant_loc in my_ants:
                move_to_hill(ant_loc)
                '''
                path, hill_loc, dist = depth_limited_bfs(ant_loc, lambda x: x in self.hills, 10, lambda x: ants.distance(x, self.hills[0]))
                if len(path) > 0:
                    if do_move_direction(ant_loc, path[0]):
                        ##logging.warning("Attacking Hill: " + str(ant_loc) + " -> " + str(hill_loc))
                        new_loc = ants.destination(ant_loc, path[0])
                        self.missions[new_loc] = hill_loc
                        self.paths[new_loc] = path[1:]
                        '''
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
                    ##logging.warning("Getting food: " + str(ant_loc) + " -> " + str(food_loc))
                        new_loc = ants.destination(ant_loc, path[0])
                        self.missions[new_loc] = food_loc
                        self.paths[new_loc] = path[1:]


        '''
        for ant_loc in my_ants: 
            if ant_loc not in orders.values():
                path, location, distance = bfs(ant_loc, lambda x: x in self.unseen and x not in self.missions.keys())
                if len(path) > 0:
                    if do_move_direction(ant_loc, path[0]):
                        ##logging.warning("Exploring: " + str(ant_loc) + " -> " + str(food_loc))
                        new_loc = ants.destination(ant_loc, path[0])
                        self.missions[new_loc] = location
                        self.paths[new_loc] = path[1:]
        '''

        
        end_time = int(round(time.time()*1000))
        diff = end_time - start_time
        if self.max_time < diff:
            self.max_time = diff
        logging.warning("turn " + str(self.turn_num) +", time: "+ str(end_time - start_time))
        self.turn_num = self.turn_num + 1
        '''
        ## attack enemy hills 
        for hill_loc, hill_owner in ants.enemy_hills():
            if hill_loc not in self.hills:
                self.hills.append(hill_loc)
        ant_dist = []
        for hill_loc in self.hills:
            for ant_loc in my_ants:
                if ant_loc not in orders.values():
                    dist = ants.distance(ant_loc, hill_loc)
                    ant_dist.append((dist, ant_loc, hill_loc))
        ant_dist.sort()
        for dist, ant_loc, hill_loc in ant_dist:
            do_move_location(ant_loc, hill_loc)

            ## explore
        for loc in self.unseen[:]:
            if ants.visible(loc):
                self.unseen.remove(loc)
        for ant_loc in my_ants:
            if ant_loc not in orders.values():
                unseen_dist = []
                for unseen_loc in self.unseen:
                    dist = ants.distance(ant_loc, unseen_loc)
                    unseen_dist.append((dist, unseen_loc))
                unseen_dist.sort()
                for dist, unseen_loc in unseen_dist:
                    if do_move_location(ant_loc, unseen_loc):
                        break
                        '''
        '''
        # unblock own hill
        for hill_loc in ants.my_hills():
            if hill_loc in my_ants and hill_loc not in orders.values():
                for direction in ('s','e','w','n'):
                    if do_move_direction(hill_loc, direction):
                        break
        '''
                        










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




