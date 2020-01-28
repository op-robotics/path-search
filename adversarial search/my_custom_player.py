
#from sample_players import DataPlayer
from isolation import Isolation, DebugState
import logging
import pickle
import random
from time import perf_counter 

logger = logging.getLogger(__name__)


### game board index values or cell locations in two center board regions
### referenced to in *supporting functions* vacant_sector()
center_west = [86,85,84,73,72,71,60,59,58,47,46,45,34,33,32]
center_east = [82,81,80,69,68,67,56,55,54,43,42,41,30,29,28]

### game board index values in four different corner regions
### referenced to in *supporting functions* vacant_sector()
north_west = [114,113,112,111,110,101,100,99,98,97,88,87,86,85,84,75,74,73] 
north_east = [108,107,106,105,104,95,94,93,92,91,82,81,80,79,78,67,66,65]
south_east = [41,40,39,30,29,28,27,26,17,16,15,14,13,4,3,2,1,0]
south_west = [49,48,47,36,35,34,33,32,23,22,21,20,19,10,9,8,7,6]

### cell locations in board edges and corners
edge_cells = [112,111,110,109,108,107,106,88,78,75,65,62,52,49,39,36,26,8,7,6,5,4,3,2]
corner_cells = [114,113,101,105,104,91,23,10,9,13,1,0]

### board cells to reach if target locations(cells situated around the 
### center of most available board regions)
### are too far from custom playing agent's
### location
by_way = {}
by_way[55] = [57,53,81,29]
by_way[59] = [57,33,85,61]
by_way[35] = [19,61]
by_way[87] = [61,97]
by_way[79] = [53,95]
by_way[27] = [17,53]


class CustomPlayer():
    """ Implement your own agent to play knight's Isolation

    The get_action() method is the only required method for this project.
    You can modify the interface for get_action by adding named parameters
    with default values, but the function MUST remain compatible with the
    default interface.

    **********************************************************************
    NOTES:
    - The test cases will NOT be run on a machine with GPU access, nor be
      suitable for using any other machine learning techniques.

    - You can pass state forward to your agent on the next turn by assigning
      any pickleable object to the self.context attribute.
    **********************************************************************
    """
    def __init__(self, player_id):
        self.player_id = player_id
        self.timer = None
        self.queue = None
        self.context = None
        self.data = None
    
    def get_action(self, state):
        """ Employ an adversarial search technique to choose an action
        available in the current state calls self.queue.put(ACTION) at least

        This method must call self.queue.put(ACTION) at least once, and may
        call it as many times as you want; the caller will be responsible
        for cutting off the function after the search time limit has expired.

        See RandomPlayer and GreedyPlayer in sample_players for more examples.

        **********************************************************************
        NOTE: 
        - The caller is responsible for cutting off search, so calling
          get_action() from your own code will create an infinite loop!
          Refer to (and use!) the Isolation.play() function to run games.
        **********************************************************************
        """
        # TODO: Replace the example implementation below with your own search
        #       method by combining techniques from lecture
        #
        # EXAMPLE: choose a random move without any search--this function MUST
        #          call self.queue.put(ACTION) at least once before time expires
        #          (the timer is automatically managed for you)
                
        ## +++*+++*+++
        stopwatch_start = perf_counter() ## start the timer as soon as get_action() is called
                
        if state.ply_count < 2:
            ### move into center cell 
            my_move = 57
            
            ### check if opposing agent occupied center cell
            ### if yes then occupy cell 59
            opp_pos = state.locs[1-self.player_id]
                        
            if opp_pos == 57:
                my_move = 59
            
            self.queue.put(my_move) ## make first move
        
        elif 1 < state.ply_count < 18:
            ###----- in the first 14 moves
            ###----- run mid_game_score heuristic 
            ###----- same scoring function is employed in the next 17 moves after move 17
            ###----- the purpose behind coding the first 14 moves in this way is to
            ###----- reduce game tree and increase time limit for moves 18-30
            open_game_time_limit = 22 ## in milliseconds
            self.queue.put(self.play_game(state, stopwatch_start, open_game_time_limit, 'mid game', 3))
            
        elif 17 < state.ply_count < 31:
            
            mid_game_time_limit_1 = 29 ## in milliseconds
            ###----- in the next 15 moves
            ###----- run mid_game_score heuristic 
            self.queue.put(self.play_game(state, stopwatch_start, mid_game_time_limit_1, 'mid game', 3))
            #self.queue.put(self.play_game(state, stopwatch_start, open_game_time_limit, 'base game', 3))
            #self.queue.put(self.alpha_beta_minimax(state, depth=3))
                
        elif 30 < state.ply_count < 42:
            
            mid_game_time_limit_2 = 37 
            ###----- in the next 10 moves
            ###----- use end_game_score heuristic 
            self.queue.put(self.play_game(state, stopwatch_start, mid_game_time_limit_2, 'end game', 3))
            #self.queue.put(self.play_game(state, stopwatch_start, mid_game_time_limit, 'base game', 3))
            #self.queue.put(self.alpha_beta_minimax(state, depth=4))
            
        else:
                       
            end_game_time_limit = 48
            ###------ after move 41
            ###------ run end_game_two_score heuristic
            self.queue.put(self.play_game(state, stopwatch_start, end_game_time_limit, 'end game two', 3))
            #self.queue.put(self.play_game(state, stopwatch_start, end_game_time_limit, 'base game', 3))
            #self.queue.put(self.alpha_beta_minimax(state, depth=5))
   
    def play_game(self, state, timer_start, game_time_limit, game_type, depth):
             
        ab_move = None
        best_move = None
                
        #######
        ##     execute best node search within allowed time limit
        #######
        while 1000*(perf_counter() - timer_start) < game_time_limit: ## 1000*(perf_counter() - timer_start)
                                                                     ## time expired in ms            
            ab_move = self.alpha_beta_minimax(state, depth, game_type)
           
            if ab_move != None:
                best_move = ab_move
                        
            ## increase search depth if time limit allows
            depth += 1
        
        ## sometimes alpha beta minimax search returns best_move=None in the last 1 or 2 moves.
        ## if this is the case, return first available legal move
        if best_move == None:
            return state.actions()[0]  
        
        return best_move 
    
    ##############################################################################
    #
    #                 // alpha beta mini max search functions 
    #                 // executed from play_game() 
    #
    ##############################################################################
    
    ###
    ###  use alpha beta minimax search method for best node search 
    ###
    def alpha_beta_minimax(self, state, depth, game_type):
        """ 
        
        Return the move along a branch of the game tree that
        has the best possible value.  A move is an action contained  
        in the set of legal moves generated by state.actions().
        
        
        """
        ######
        ##     supporting functions
        ######
        def select_heuristic(state, game_type):
            """
            allows using 3 different scoring functions for node evaluation
            depending on how far game has progressed 
            
            
            """
                        
            if game_type == 'mid game':
                return self.mid_game_score(state) ##----> evaluate game nodes for moves 1-31
        
            elif game_type == 'end game':
                return self.end_game_score(state) ##---- evaluate game nodes for moves 31-41
                
            elif game_type == 'end game two':
                return self.end_game_score_two(state) ##---- evaluate game nodes past move 41
                
            else:
                return self.score(state) ##-----> evaluate position with baseline heuristic
            
        def min_value(state, alpha, beta, depth):
            """ return the minimum value over all legal child
            nodes.
            """
            if state.terminal_test():
                return state.utility(self.player_id)
        
            if depth <= 0:
                ###  evaluate bottom node using specified heuristic  
                return select_heuristic(state, game_type)
             
            v = float("inf")
            for a in state.actions():
                v = min(v, max_value(state.result(a), alpha, beta, depth-1))
                if v <= alpha:
                    return v
                beta = min(beta, v)
            return v
        
        def max_value(state, alpha, beta, depth):
            """ return the maximum value over all legal child
            nodes.
            """
            if state.terminal_test():
                return state.utility(self.player_id)
        
            if depth <= 0:
                ###  evaluate bottom node using specified heuristic  
                return select_heuristic(state, game_type) 
            
            v = float("-inf")
            for a in state.actions():
                v = max(v, min_value(state.result(a), alpha, beta, depth-1))
                if v >= beta:
                    return v
                alpha = max(alpha, v)
            return v
        
        ######
        ##
        ##        alpha beta minimax
        ##
        ######
        alpha = float("-inf")
        beta = float("inf")
        best_score = float("-inf")
        best_move = None
        
        for a in state.actions():
            
            v = min_value(state.result(a), alpha, beta, depth-1)
            
            alpha = max(alpha, v)
            
            if v > best_score:
                best_score = v
                best_move = a
        
        return best_move

    
    
    #################################################################################
    #
    #
    #           // heuristic evaluation functions used in alpha beta minimax search //
    #
    #
    #################################################################################
    
    ### ++++-++-- baseline heuristic
    def score(self, state):
        
        own_loc = state.locs[self.player_id]
        opp_loc = state.locs[1 - self.player_id]
        own_moves = state.liberties(own_loc)
        opp_moves = state.liberties(opp_loc)
        
        return len(own_moves) - len(opp_moves)
       
    
    ### opening and mid game heuristic
    def mid_game_score(self, state):
        """
        The agent utilizes combined heuristic function consisting of
        two different functions:
        
        heuristic one: board distance heuristic
        
        Occupy both board center areas(center_west and center_east)
        until there is less than 6 blank cells in either of them.
        select nodes that position the custom playing agent in or very close to
        center cells 55 or 59.
        
        expressed in code: -self.board_index_dist(own_pos, 59)
        
        
        If center areas are too crowded, then look for
        most vacant space in corner areas: north_west, or north_east,
        or south_west, or south_east.
        Select nodes that position the custom playing agent in or very close to
        corner locations. For example, cell 87 in north_west area or 35 in south west.  
        
        expressed in code: 
        -self.board_index_dist(own_pos, self.closest_sector(board_blanks, own_pos))
        shortest distance is the object thus negative sign
        
        where:
        board_index_dist() returns distance in board cells
        own_pos - custom playing agent's board index or location
        vacant_sector() returns dictionary containing corner locations and
        corresponding number of blank cells             
        closest_sector() returns vacant sector's location closest to custom playing agent's
        location
        
        heuristic two:
        
        Select nodes where the opposing player moves onto
        edge or corner locations on gaming board.
        
        in coded form: self.is_opp_loc_on_edge(opp_pos)
        """
        own_pos = state.locs[self.player_id]
        opp_pos = state.locs[1 - self.player_id]
        
        board_blanks = self.vacant_sector(state) ### get dictionary that specifies locations for vacant corner areas
        
        #print('mid game score: board blanks:', board_blanks)
        
        if board_blanks['center_west'][0] > 6: ## if center_west holds more than 6 blank cells, go here
            
            return -self.board_index_dist(own_pos, 59) + self.is_opp_loc_on_edge(opp_pos) 
                
        elif board_blanks['center_east'][0] > 5: ## or if center_east holds more than 6 blank cells, go here
            
            return -self.board_index_dist(own_pos, 55) + self.is_opp_loc_on_edge(opp_pos) 
                
        
        #### if center is occupied, redirect toward available corner locations
        return -self.board_index_dist(own_pos, self.closest_sector(board_blanks, own_pos)) + self.is_opp_loc_on_edge(opp_pos) 
        
    ### heuristic function used by the agent during moves 31-41
    def end_game_score(self, state):
        """
        heuristic one: board distance heuristic
        
        Direct custom playing agent toward most vacant corner regions.
        Select nodes that position the custom playing agent in or very close to
        corner locations. For example, cell 87 in north_west area or 35 in south west.  
        
        in coded form:
        -self.board_index_dist(own_pos, self.closest_sector(self.vacant_sector(state), own_pos))
        
        where:
        board_index_dist() returns distance in board cells
        own_pos - custom playing agent's board index or location
        vacant_sector() returns dictionary containing corner locations and
        corresponding number of blank cells             
        closest_sector() returns vacant sector's location closest to custom playing agent's
        location
        
        heuristic two:
        
        Select nodes where the opposing player moves onto
        edge or corner locations on gaming board.
        
        in coded form: self.is_opp_loc_on_edge(opp_pos)
        
        """
        
        own_pos = state.locs[self.player_id]
        opp_pos = state.locs[1 - self.player_id]
         
        return -self.board_index_dist(own_pos, self.closest_sector(self.vacant_sector(state), own_pos)) + self.is_opp_loc_on_edge(opp_pos)
    
    ### evaluate game nodes after move 41
    def end_game_score_two(self, state):
        """
        same as end_game_score except
        
        heuristic two:
        
        #2*own_moves 
        """
        own_pos = state.locs[self.player_id]
        opp_pos = state.locs[1 - self.player_id]
        own_moves = state.liberties(own_pos)
        
        #print('end game score two: closest sect:', self.closest_sector(self.vacant_sector(state), own_pos) ) 
             
        return -self.board_index_dist(own_pos, self.closest_sector(self.vacant_sector(state), own_pos)) + len(own_moves) 
    
    
    ############################################################################################
    #
    #
    #             //supporting functions activated from within heuristic evaluation functions
    #
    #
    #############################################################################################
    
    
        
    def ind_to_xy(self, ind):
        
        """ Convert from board index value to xy coordinates

        The coordinate frame is 0 in the bottom right corner, with x increasing
        along the columns progressing towards the left, and y increasing along
        the rows progressing towards the top.
        
        
        """
        return (ind % 13, ind // 13)
    
    
    def board_index_dist(self, ind_one, ind_two):
        """
        evaluate distances in number of cells from ind_one board index to ind_two
        board index in x and y axis
        and sum up the distances to obtain total cell distance
        
        """
        return abs(self.ind_to_xy(ind_two)[0] - self.ind_to_xy(ind_one)[0]) + abs(self.ind_to_xy(ind_two)[1] - self.ind_to_xy(ind_one)[1])
    
    
    def is_opp_loc_on_edge(self, opp_pos):
        """
        return a score of 5 if opposing agent's move falls in 
        corner cell or
        
        return a score of 3 if opposing agent's move ends up in
        edge cell
        
        return zero otherwise
        
        """
                
        if opp_pos in corner_cells:           
            return 5
        
        elif opp_pos in edge_cells:            
            return 3
        
        else:
            return 0
       
    
        
    def closest_sector(self, four_sectors, ind):
        """
        arguments: four_sectors - dictionary returned by vacant_sector()
        ex: {'center_west': [13, 59], 'center_east': [13, 55], 'north_west': [18, 87], 'north_east': [16, 79], 
        'south_west': [17, 35], 'south_east': [16, 27]}
        
        and ind - board index of custom playing agent's location 
        
        returns index value or cell location of most vacant sector
        or the sector holding largest number of blank cells.
        
        if most available sector is too far, move towards one that has
        got same number of blank cells or (same number of blank cells-1)
        """
        ######
        ##   function's supporting functions:
        ######
        
        def sorted_sectors(four_zones):
            """
            sort members of dictionary in descending order and
            return result in tuple array
            """
            return sorted(four_zones.items(), key = lambda x: x[1][0], reverse=True) 
         
        def get_closest_ind(ind_array, my_loc):
            """
            given an array of board locations, find the one closest to
            my agent's
            """
            
            min_dist = 100 
            for i in ind_array:
                dist = self.board_index_dist(i, my_loc)
                if dist < min_dist:
                    min_dist = dist
                    goal_ind = i
            
            return goal_ind        
            
        def closest_vacant_zone(sector_array, my_loc):
            
            #
            #--- sector_array is passed in by sorted_sectors() and is a sorted tuple: 
            # [('center_west', [15, 59]), ('south_west', [15, 34]), ('center_east', [12, 55]), .....]
            #
            no_of_spaces = sector_array[0][1][0] ### number of blank spaces in most vacant sector 
            closest_dist = 1000
            dist = 1000
        
            for i in range (0,5):
                ### mark sectors holding as many as (most blank spaces - 1) vacant as well
                ### in case most vacant sector is too far
                if sector_array[i][1][0] >= no_of_spaces-1:
                    dist = self.board_index_dist(sector_array[i][1][1], my_loc)
                    if dist < closest_dist:
                        closest_dist = dist  ### determine closest available sector
                        closest_zone = sector_array[i][1][1]  ### and its location
            
            return closest_zone  
        
        #####
        ## ------- closest sector() ------
        #####
        
        
        if ind == None: ## in case first move is made by the opp player
            ind = 57       
        
        c = closest_vacant_zone(sorted_sectors(four_sectors), ind)
        
        ### return board index of closest vacant area as long as
        ### my custom agent's location is within 4 cells
        if self.board_index_dist(c, ind) < 5:
            
            return c
         
        else:
            ### if location of vacant sector is over 4 cells then
            ### go to secondary location contained in by_way[] declared in global variables  
            return get_closest_ind(by_way[c], ind)
    
    
    def vacant_sector(self, board_state):
        """ function calculates the number of blank board positions
        and determines how many blank spaces are contained in corner
        parts of the board. 
        
        arguments: current or iterated game state from Isolation class
        
        returns: a dictionary whose items contain number of blank spaces
        in each board sector and corresponding sector location
        
        
        """        
        ####
        ## function's supporting functions:
        ####
        def dec_to_bin(d, result = 1000, bin_str = ''):
            """
            Here decimal integer is converted to binary equivalent
            in string format '11111100111110011101000'. Run this 
            function to convert game state from base 10 number to 
            binary bit board string where ones are available board positions
            and zeros are occupied or closed cells. Same string could be obtained
            from isolation's DebugState class.
            
            """
            while result != 0:
                result = d//2
                bin_str += str(d%2)
                d = result
    
            return bin_str[::-1]
        ##
        ### ------ ! vacant_sector() begins here: !----
        ##
        #
        #------ reset the dictionary after every function call ----- 
        #------ first values must be zeroes
        #------  second values are goal index locations 
        
        b_sectors = {}
        b_sectors['center_west'] = [0, 59]
        b_sectors['center_east'] = [0, 55]
        b_sectors['north_west'] = [0, 87]
        b_sectors['north_east'] = [0, 79]
        b_sectors['south_west'] = [0, 35]
        b_sectors['south_east'] = [0, 27]
        
        #----convert default board state to bitboard string 
        #----by running function dec_to_bin()
        bit_board = dec_to_bin(board_state[0])
        
        ### ---- if bits are missing in the string
        ### ---- add 115-len(t1) zeroes to bit_board's left end 
        bit_board_len = len(bit_board)
        
        if bit_board_len < 115:
            bit_board = (115-bit_board_len)*'0' + bit_board
        
        ###  iterate and count instances of '1' in the bitboard string
        ### '1' is a blank cell, '0' is a blocked cell 
        for i in range (0, len(bit_board)):
            
            if bit_board[i] == '1':
                
                
                cell = 114-i ### ---- convert i to board index
                #########
                ###    update number of blank spaces in center and corner 
                ###    board sectors
                #########
                if cell in center_west: ##center_west, center_east, north_west etc are declared as global variables
                    b_sectors['center_west'][0] += 1
                
                if cell in center_east:
                    b_sectors['center_east'][0] += 1
                
                if cell in north_west:
                    b_sectors['north_west'][0] += 1
                    
                if cell in north_east:
                    b_sectors['north_east'][0] += 1
                
                if cell in south_west:
                    b_sectors['south_west'][0] += 1
                
                if cell in south_east:
                    b_sectors['south_east'][0] += 1
                                       
                 
        return b_sectors           
   

   
