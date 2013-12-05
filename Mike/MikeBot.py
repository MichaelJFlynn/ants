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
        self.max_time = 0
        for row in range(ants.rows):
            for col in range(ants.cols):
                self.unseen.append((row, col))



    # do turn is run once per turn
    # the ants class has the game state and is updated by the Ants.run method
    # it also has several helper methods to use
    def do_turn(self, ants):
        start_time = int(round(time.time()*1000))
        targets = {}
        orders = {} 
        food = ants.food()


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
            if loc in ants.my_ants():
                return True
            else:
                return False
                
        def bfs(init_loc, goalfun):
            ##millis = int(round(time.time()*10000))
            visited = []
            start = (init_loc, [], 0)
            if goalfun(init_loc):
                return []
            frontier = util.Queue()
            frontier.push(start)
            visited.append(start[0])
            while not frontier.isEmpty():
                current = frontier.pop()
                for loc, direction in get_neighbors(current[0]):
                    path = [x for x in current[1]]
                    path.append(direction)
                    if goalfun(loc):
                        ##logging.warning(str( int(round(time.time()*10000)) - millis ))
                        return (path, loc, current[2])
                    if not loc in visited:
                        visited.append(loc)
                        frontier.push((loc, path, current[2] + 1))
            ## return that there is no valid path
            return ([], None, None)

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

            '''
        # prevent stepping on own hill
        for hill_loc in ants.my_hills():
            orders[hill_loc] = None
            '''
        missions = {}
        ## Hills
        bad_hills = ants.enemy_hills()
        for hill in bad_hills:
            if hill not in self.hills:
                self.hills.append(hill)
        for hill_loc, team_num in self.hills: 
            path, ant_loc, depth = bfs(hill_loc, isMyAnt)
            if len(path) > 0:
                ## must use opposite direction because we did path in
                ## reverse (hill -> ant)
                if do_move_direction(ant_loc, opposite_direction(path[len(path)-1])):
                    missions[hill_loc] = ant_loc

        ## Food            
        for food_loc in food:
            path, ant_loc, depth = bfs(food_loc, isMyAnt)
            if len(path) > 0:
                ## must use opposite direction because we did path in
                ## reverse (food -> ant)
                if do_move_direction(ant_loc, opposite_direction(path[len(path)-1])):
                    missions[food_loc] = ant_loc

        ## Move towards an ant with orders 
        if len(missions) > 0:
            for ant_loc in ants.my_ants():
                if ant_loc not in missions.values():
                    path, goal_loc, depth = bfs(ant_loc, lambda x: x in missions.values())
                    if len(path) > 0:
                        do_move_direction(ant_loc, path[0])
        end_time = int(round(time.time()*1000))
        diff = end_time - start_time
        if self.max_time < diff:
            self.max_time = diff
        logging.warning("turn done, time: "+ str(end_time - start_time))
        '''
        ## attack enemy hills 
        for hill_loc, hill_owner in ants.enemy_hills():
            if hill_loc not in self.hills:
                self.hills.append(hill_loc)
        ant_dist = []
        for hill_loc in self.hills:
            for ant_loc in ants.my_ants():
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
        for ant_loc in ants.my_ants():
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
            if hill_loc in ants.my_ants() and hill_loc not in orders.values():
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




