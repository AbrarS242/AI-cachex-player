import time
import gc

from numpy import zeros, array, roll, vectorize
from random import randint
from queue import Queue, PriorityQueue
from math import inf


# Action types (taken from 'referee' module)
_ACTION_PLACE = "PLACE"
_ACTION_STEAL = "STEAL"

# Axis goals gor each player (taken from the 'referee' module)
_PLAYER_AXIS = {
    "red": 0, # Red aims to form path in r/0 axis
    "blue": 1 # Blue aims to form path in q/1 axis
}

# Players
RED = "red"
BLUE = "blue"

# Utility function to add two coord tuples (taken from the 'referee' module)
_ADD = lambda a, b: (a[0] + b[0], a[1] + b[1])

# Neighbour hex steps in clockwise order (taken from the 'referee' module)
_HEX_STEPS = array([(1,-1), (1, 0), (0,1), (-1,1), (-1, 0), (0, -1)], dtype="i,i")

# Pre-compute diamon capture patterns (taken from the 'referee' module)
_CAPTURE_PATTERNS = [[_ADD(n1, n2), n1, n2] 
    for n1, n2 in 
        list(zip(_HEX_STEPS, roll(_HEX_STEPS, 1))) + 
        list(zip(_HEX_STEPS, roll(_HEX_STEPS, 2)))]

# Maps between player string and internal token type (taken from the 'referee' module)
_TOKEN_MAP_OUT = { 0: None, 1: "red", 2: "blue" }
_TOKEN_MAP_IN = {v: k for k, v in _TOKEN_MAP_OUT.items() }

# Map between player token types (taken from the 'referee' module)
_SWAP_PLAYER = { 0: 0, 1: 2, 2: 1 }


class Player:

    
    def __init__(self, player, n):
        """
        Called once at the beginning of a game to initialise this player.
        Set up an internal representation of the game state.

        The parameter player is the string "red" if the player will
        play as Red, or the string "blue" if the player will play
        as Blue.
        """

        self.player = player
        self.original_player = player
        self.stolen = False
            
        # Initialise the board 
        self.n = n
        self.n_turns = 1
        self.ub = self.n - 1
        self._data = zeros((n,n), dtype=int)
        self.all_coords = self.enum_coords(n)
        self.border_coords = {"red" : [coord for coord in self.all_coords if (coord[0] == 0 or coord[0] == n-1)], 
                              "blue": [coord for coord in self.all_coords if (coord[1] == 0 or coord[1] == n-1)]}
        self.occ_coords = [] 

    def action(self):
        """
        Called at the beginning of the turn. Based on the current state
        of the game, select an action to play.
        """
            
        valid_move = False

        if self.n_turns == 1:
            
            # Select a corner if possible
            if self.get_token((0, 0)) == 0:
                return (_ACTION_PLACE, 0, 0)
            elif self.get_token((0, self.n - 1)) == 0:
                return (_ACTION_PLACE, 0, self.n - 1)
            elif self.get_token((self.n - 1, 0)) == 0:
                return (_ACTION_PLACE, self.n - 1, 0)
            elif self.get_token((self.n - 1, self.n - 1)) == 0:
                return (_ACTION_PLACE, self.n - 1, self.n - 1)

        # Steal if going second
        if self.n_turns == 2:
            return (_ACTION_STEAL, )

        # Check if no piece on the board
        piece_found = False
        for i in range(self.n):
            for j in range(self.n):
                if self.get_token((i,j)) == _TOKEN_MAP_IN[self.player]:
                    piece_found = True
                    
        if piece_found == False:

            # Select a corner if possible
            if self.get_token((0, 0)) == 0:
                return (_ACTION_PLACE, 0, 0)
            elif self.get_token((0, self.n - 1)) == 0:
                return (_ACTION_PLACE, 0, self.n - 1)
            elif self.get_token((self.n - 1, 0)) == 0:
                return (_ACTION_PLACE, self.n - 1, 0)
            elif self.get_token((self.n - 1, self.n - 1)) == 0:
                return (_ACTION_PLACE, self.n - 1, self.n - 1)
            else:
                # Select a random move
                while valid_move == False:
                    x = randint(0,self.ub)
                    aX = self.axial_x(x)
                    y = randint(0,self.ub)
                    if self._data[aX][y] == 0:

                        # Cannot place token in the center if it is the first turn of the game (and the board size is odd)
                        if self.n % 2 == 1 and self.n_turns == 1 and aX * 2 == y * 2 == self.n - 1:
                            valid_move = False
                        else:
                            valid_move = True
                self.stolen = False
                return (_ACTION_PLACE, x, y)

        maxChain, maxChainEnds = self.find_longest_chain()
        bestScore, move = self.make_best_move()

        if move == None or self.get_token(move) != 0:
            # Select a corner if possible
            if self.get_token((0, 0)) == 0:
                return (_ACTION_PLACE, 0, 0)
            elif self.get_token((0, self.n - 1)) == 0:
                return (_ACTION_PLACE, 0, self.n - 1)
            elif self.get_token((self.n - 1, 0)) == 0:
                return (_ACTION_PLACE, self.n - 1, 0)
            elif self.get_token((self.n - 1, self.n - 1)) == 0:
                return (_ACTION_PLACE, self.n - 1, self.n - 1)
            else:
                # Select a random move
                while valid_move == False:
                    x = randint(0,self.ub)
                    aX = self.axial_x(x)
                    y = randint(0,self.ub)
                    if self._data[aX][y] == 0:

                        # Cannot place token in the center if it is the first turn of the game (and the board size is odd)
                        if self.n % 2 == 1 and self.n_turns == 1 and aX * 2 == y * 2 == self.n - 1:
                            valid_move = False
                        else:
                            valid_move = True
                self.stolen = False
                return (_ACTION_PLACE, x, y)
        
        x, y = move
        x = int(x)
        y = int(y)

        
        return (_ACTION_PLACE, x, y)
    
    def turn(self, player, action):
        """
        Called at the end of each player's turn to inform this player of 
        their chosen action. Update your internal representation of the 
        game state based on this. The parameter action is the chosen 
        action itself. 
        
        Note: At the end of your player's turn, the action parameter is
        the same as what your player returned from the action method
        above. However, the referee has validated it at this point.
        """
        
        if self.n_turns == 1:
            _, x, y = action
            self.opening_move = (x, y)

        
        if action[0] == _ACTION_PLACE:
            
            # Find the coordinates
            _, x, y = action
            coord = (x,y)

            # Place the token on the board
            self.set_token(coord, _TOKEN_MAP_IN[player])

            # Check if any captures have taken place
            self.apply_captures(coord)

            if self.n_turns > (self.n) * 2 - 1:
                print(self.detect_win(coord, player))
            self.occ_coords.append((x,y))

        elif action[0] == _ACTION_STEAL:
            if self.player != player:
                self.stolen = True
            self.swap()

            
        self.n_turns += 1


    def axial_x(self, x):
        """
        Flips the value of the x-coordinate along the middle of the board to
        get an axial x-coordinate.
        """
        x = abs((self.n -1) - x)       
        return x

    def set_token(self, coord, token):
        """
        Given a set of coordinates, update the internal representation of the board
        """
        aX = self.axial_x(coord[0])
        y = coord[1]
        self._data[aX][y] = token

    def get_token(self, coord):
        aX = self.axial_x(coord[0])
        y = coord[1]
        return self._data[aX][y]

    def apply_captures(self, coord):
        """
        Check coord for diamond captures, and apply these to the board
        if they exist
        (taken from the 'referee' module written by the COMP30024 teaching staff).
        """
        opp_type = self.get_token(coord)
        mid_type = _SWAP_PLAYER[opp_type]
        captured = set()

        # Check each capture pattern intersecting with coord
        for pattern in _CAPTURE_PATTERNS:
            coords = [_ADD(coord, s) for s in pattern]
            # No point checking if any coord is outside the board!
            if all(map(self.inside_bounds, coords)):
                tokens = [self.get_token(coord) for coord in coords]
                if tokens == [opp_type, mid_type, mid_type]:
                    # Capturing has to be deferred in case of overlaps
                    # Both mid cell tokens should be captured
                    captured.update(coords[1:])

        # Remove any captured tokens
        for coord in captured:
            self.set_token(coord, 0)


    def check_captures(self, coord):
        """
        Check coord for diamond captures and returns a list of captured token coordinates
        (taken from the 'referee' module written by the COMP30024 teaching staff).
        """
        opp_type = _TOKEN_MAP_IN[self.player]
        mid_type = _SWAP_PLAYER[opp_type]
        captured = set()

        # Check each capture pattern intersecting with coord
        for pattern in _CAPTURE_PATTERNS:
            coords = [_ADD(coord, s) for s in pattern]
            # No point checking if any coord is outside the board!
            if all(map(self.inside_bounds, coords)):
                tokens = [self.get_token(coord) for coord in coords]
                if tokens == [opp_type, mid_type, mid_type]:
                    # Capturing has to be deferred in case of overlaps
                    # Both mid cell tokens should be captured
                    captured.update(coords[1:])

        # Remove any captured tokens
        return captured

    def inside_bounds(self, coord):
        """
        True iff coord inside board bounds
        (taken from the 'referee' module written by the COMP30024 teaching staff).
        """
        r, q = coord
        return r >= 0 and r < self.n and q >= 0 and q < self.n

    def detect_win(self, coord, player):
        """
        Check if the current placement causes a victory for the player
        (taken from the 'referee' module written by the COMP30025 teaching staff).
        """
        r, q = coord
        reachable, endpoints = self.connected_coords((r, q))
        axis_vals = [c_coord[_PLAYER_AXIS[player]] for c_coord in reachable]
        if min(axis_vals) == 0 and max(axis_vals) == self.n - 1:
            return True
        else:
            return False

    def _coord_neighbours(self, coord):
        """
        Returns (within-bounds) neighbouring coordinates for given coord
        (taken from the 'referee' module written by the COMP30024 teaching staff).
        """
        return [_ADD(coord, step) for step in _HEX_STEPS \
            if self.inside_bounds(_ADD(coord, step))]

    def connected_coords(self, start_coord):
        """
        Find connected coordinates from start_coord. This uses the token 
        value of the start_coord cell to determine which other cells are
        connected - e.g. all will be the same value
        (taken from the 'referee' module written by the COMP30024 teaching staff).
        """
        # Get search token type
        token_type = self.get_token(start_coord)

        # Find the chain endpoints
        endpoints = []

        # Use bfs from start coordinate
        reachable = set()
        queue = Queue(0)
        queue.put(start_coord)
        

        while not queue.empty():

            curr_coord = queue.get()
            reachable.add(curr_coord)
            
            for coord in self._coord_neighbours(curr_coord):
                if coord not in reachable and self.get_token(coord) == token_type:
                    queue.put(coord)

        reachable = list(reachable)

        # Find the endpoints of the current chain
        axis_vals = [coord[_PLAYER_AXIS[_TOKEN_MAP_OUT[token_type]]] for coord in reachable]
        endpoints.append(reachable[axis_vals.index(max(axis_vals))])
        endpoints.append(reachable[axis_vals.index(min(axis_vals))])
        endpoints = list(set(endpoints))
        
        return reachable, endpoints

    def find_player_tokens(self, token):
        positions = []
        for x in range(self.n):
            for y in range(self.n):
                if self._data[x][y] == token:
                    aX = self.axial_x(x)
                    positions.append((aX,y))
        return positions

    def find_longest_chain(self):
        all_tokens = self.find_player_tokens(_TOKEN_MAP_IN[self.player])
        searched = []
        maxChainLen = 0 
        maxChain = []
        maxChainEnds = []
        for coord in all_tokens:
            if coord not in searched:
                reachable, endpoints = self.connected_coords(coord)
                searched += reachable
                if len(reachable) > maxChainLen:
                    maxChainLen = len(reachable)
                    maxChain = reachable.copy()
                    maxChainEnds = endpoints.copy()

        return maxChain, maxChainEnds

    def find_opp_longest_chain(self):
        if self.player == RED:
            opp = BLUE
        else:
            opp = RED
        all_tokens = self.find_player_tokens(_TOKEN_MAP_IN[opp])
        searched = []
        maxChainLen = 0 
        maxChain = []
        maxChainEnds = []
        for coord in all_tokens:
            if coord not in searched:
                reachable, endpoints = self.connected_coords(coord)
                searched += reachable
                if len(reachable) > maxChainLen:
                    maxChainLen = len(reachable)
                    maxChain = reachable.copy()
                    maxChainEnds = endpoints.copy()

        return maxChain, maxChainEnds

    def enum_coords(self, n):
        all_coords = []
        for i in range (0, n):
            for j in range (0, n):
                new_coord = (i, j)
                all_coords.append(new_coord)
        return all_coords

    def compute_path(self, n, start_coord, goal_coord, occ_coords, f_h=lambda *_: 0):
        """
        Compute lowest cost path on Cachex board. Internally uses A*
        (taken from the subject modules written by the COMP30024 teaching staff).
        """

        # Using a set will be a lot more efficient than a list here
        occ_coords = set(occ_coords)

        # Returns true iff coord is valid (inside board bounds, not occupied)
        def valid_coord(coord):
            (r, q) = coord
            return 0 <= r < n and 0 <= q < n and (not coord in occ_coords)

        
        # Run A* and return path (default empty list if no path)
        return self.a_star(start_coord, goal_coord, f_h, self._coord_neighbours) or []

    def axial_distance(self, coord, goal_coord):
        """
        Axial distance heuristic for use in hex-grid based A* search
        (taken from the subject modules written by the COMP30024 teaching staff).
        """
        (a_r, a_q) = coord
        (b_r, b_q) = goal_coord
        return (abs(a_q - b_q) 
            + abs(a_q + a_r - b_q - b_r)
            + abs(a_r - b_r)) / 2

    def backtrace_path(self, goal_node, start_node, came_from):
        """
        Compute minimal cost path from the goal node to the start node given 
        a dictionary of "came from" node mappings
        (taken from the subject modules written by the COMP30024 teaching staff).
        """
        path = []
        curr_node = goal_node
        while curr_node != start_node:
            path.append(curr_node)
            curr_node = came_from[curr_node]
        path.append(start_node)
        path.reverse()
        return path

    def a_star(self, start_node, goal_node, f_h, f_n, f_w=lambda *_: 1):
        """
        Perform an A* search given start and end node objects, and functions
        to compute problem-domain-specific values
        (taken from the subject modules written by the COMP30024 teaching staff).
        """
        open_nodes = PriorityQueue()
        open_nodes.put((0, 0, start_node))
        closed_nodes = set()
        came_from = {}
        g = { start_node: 0 }

        while not open_nodes.empty():
            # Get lowest f(x) cost node, or lowest h(x) in case of ties
            *_, curr_node = open_nodes.get()
            closed_nodes.add(curr_node)

            # Check if we reached goal
            if curr_node == goal_node:
                return self.backtrace_path(goal_node, start_node, came_from)

            # Expand and add neighbours to queue
            for neighbour_node in f_n(curr_node):
                
                if self.get_token(neighbour_node) == _TOKEN_MAP_IN[self.player] or self.get_token(neighbour_node) == 0:
                    # Compute neighbour g(x) and ensure it is not in closed set
                    neighbour_g = g[curr_node] + f_w(curr_node, neighbour_node)
                    is_lowest_cost_so_far = neighbour_g < g.get(neighbour_node, inf)
                    closed_node = neighbour_node in closed_nodes

                    if not closed_node and is_lowest_cost_so_far:
                        # Update g/parent values for this neighbour node
                        g[neighbour_node] = neighbour_g
                        came_from[neighbour_node] = curr_node

                        # Add to queue with priority by f(x), then h(x) (for ties)
                        neighbour_h = f_h(neighbour_node, goal_node)
                        neighbour_f = neighbour_g + neighbour_h
                        open_nodes.put((neighbour_f, neighbour_h, neighbour_node))

        # No path found if we reach this point
        return None



    def get_possible_moves(self):


        maxChain, endpoints = self.find_longest_chain()
        
        # Find out which borders the endpoints are closest to
        borders = self.border_coords[self.player]
        border_targets = []
        if len(endpoints) == 2:
            if (endpoints[0][_PLAYER_AXIS[self.player]] <= endpoints[1][_PLAYER_AXIS[self.player]]):
                closest_border1 = (-1, -1)
                nearest_dist1 = 999
                closest_border2 = (-1, -1)
                nearest_dist2 = 999
                for border in borders:
                    if border[_PLAYER_AXIS[self.player]] == 0:
                        if self.get_token(border) == _TOKEN_MAP_IN[self.player] or self.get_token(border) == 0:
                            path1 = self.compute_path(self.n, endpoints[0], border, self.occ_coords, self.axial_distance)
                            dist1 = len(path1)
                            if dist1 >= 1 and dist1 < nearest_dist1:
                                nearest_dist1 = dist1
                                closest_border1 = border
                    else:
                        if self.get_token(border) == _TOKEN_MAP_IN[self.player] or self.get_token(border) == 0:
                            path2 = self.compute_path(self.n, endpoints[1], border, self.occ_coords, self.axial_distance)
                            dist2 = len(path2)
                            if dist2 >= 1 and dist2 < nearest_dist2:
                                nearest_dist2 = dist2
                                closest_border2 = border
                border_targets.append(closest_border1)
                border_targets.append(closest_border2)
            else:
                closest_border1 = (-1, -1)
                nearest_dist1 = 999
                closest_border2 = (-1, -1)
                nearest_dist2 = 999
                for border in borders:
                    if border[_PLAYER_AXIS[self.player]] == self.n-1:
                        if self.get_token(border) == _TOKEN_MAP_IN[self.player] or self.get_token(border) == 0:
                            path1 = self.compute_path(self.n, endpoints[0], border, self.occ_coords, self.axial_distance)
                            dist1 = len(path1)
                            if dist1 >= 1 and dist1 < nearest_dist1:
                                nearest_dist1 = dist1
                                closest_border1 = border
                    else:
                        if self.get_token(border) == _TOKEN_MAP_IN[self.player] or self.get_token(border) == 0:
                            path2 = self.compute_path(self.n, endpoints[1], border, self.occ_coords, self.axial_distance)
                            dist2 = len(path2)
                            if dist2 >= 1 and dist2 < nearest_dist2:
                                nearest_dist2 = dist2
                                closest_border2 = border
                border_targets.append(closest_border1)
                border_targets.append(closest_border2)
        elif len(endpoints) == 1:
            closest_border = (-1, -1)
            nearest_dist = 999
            for border in borders:
                skip = False
                for coord in maxChain:
                    if (coord[_PLAYER_AXIS[self.player]] == border[_PLAYER_AXIS[self.player]] == self.n - 1) or (coord[_PLAYER_AXIS[self.player]] == border[_PLAYER_AXIS[self.player]] == 0):
                        skip = True
                        break
                if (skip == False):
                    if self.get_token(border) == _TOKEN_MAP_IN[self.player] or self.get_token(border) == 0:
                        path = self.compute_path(self.n, endpoints[0], border, self.occ_coords, self.axial_distance)
                        dist = len(path)
                        if dist >=1 and dist < nearest_dist:
                            nearest_dist = dist
                            closest_border = border
            border_targets.append(closest_border)
            
        # Find the shortest path from ends to the borders
        paths = []
        for i in range(len(endpoints)):
            path = self.compute_path(self.n, endpoints[i], border_targets[i], self.occ_coords, self.axial_distance)
            paths.append(path)
        #print(paths)

        moves = []
        for path in paths:
            if path != []:
                for coord in path:
                    if self.get_token(coord) == 0:
                        moves.append(coord)
                        break

        # Find out if the opponent can be attacked
        if self.player == RED:
            opp = BLUE
        else:
            opp = RED
        oppChain, endpointsOpp = self.find_opp_longest_chain()

        # Ignore the opponent endpoints if already at the border
        remove = []
        for endpoint in endpointsOpp:
            if endpoint in self.border_coords[self.player]:
                remove.append(endpoint)
        for endpoint in remove:
            endpointsOpp.remove(endpoint)

        # Break a sufficiently long chain of the opponent
        pos_block_moves = []
        if len(oppChain) > float(self.n) / 2:
            for endpoint in endpointsOpp:
                for neighbour in self._coord_neighbours(endpoint):
                    
                    if self.get_token(neighbour) == 0:
                       
                        opp_around = 0
                        for neighbour2 in self._coord_neighbours(neighbour):
                            if self.get_token(neighbour2) == _TOKEN_MAP_IN[opp] and neighbour2 in oppChain:
                                opp_around += 1
                        if opp_around == 1:
                            
                            pos_block_moves.append(neighbour)

            for move in pos_block_moves:
                for move2 in pos_block_moves:
                    
                    dist = self.axial_distance(move, move2)
                    if dist == 2:
                        moves.append(move)

        # Check if a capture can be made
        for coord in self.occ_coords:
            if self.get_token(coord) == _TOKEN_MAP_IN[opp]:
                for neighbour in self._coord_neighbours(coord): 
                    if self.get_token(neighbour) == 0:
                        captured = self.check_captures(neighbour)
                        if len(captured) != 0:
                            moves.append(neighbour)
                            

        moves = list(set(moves))


        return moves

    def eval(self, coord):
        value = 0
        self.set_token(coord, _TOKEN_MAP_IN[self.player])

        maxChain, endpoints = self.find_longest_chain()
        
        borders = self.border_coords[self.player]
        border_targets = []

        if len(endpoints) == 2:
            if (endpoints[0][_PLAYER_AXIS[self.player]] <= endpoints[1][_PLAYER_AXIS[self.player]]):
                closest_border1 = (-1, -1)
                nearest_dist1 = 999
                closest_border2 = (-1, -1)
                nearest_dist2 = 999
                for border in borders:
                    if border[_PLAYER_AXIS[self.player]] == 0:
                        if self.get_token(border) == _TOKEN_MAP_IN[self.player] or self.get_token(border) == 0:
                            path1 = self.compute_path(self.n, endpoints[0], border, self.occ_coords, self.axial_distance)
                            dist1 = len(path1)
                            if dist1 < nearest_dist1:
                                nearest_dist1 = dist1
                                closest_border1 = border
                    else:
                        if self.get_token(border) == _TOKEN_MAP_IN[self.player] or self.get_token(border) == 0:
                            path2 = self.compute_path(self.n, endpoints[1], border, self.occ_coords, self.axial_distance)
                            dist2 = len(path2)
                            if dist2 < nearest_dist2:
                                nearest_dist2 = dist2
                                closest_border2 = border
                border_targets.append(closest_border1)
                border_targets.append(closest_border2)
            else:
                closest_border1 = (-1, -1)
                nearest_dist1 = 999
                closest_border2 = (-1, -1)
                nearest_dist2 = 999
                for border in borders:
                    if border[_PLAYER_AXIS[self.player]] == self.n-1:
                        if self.get_token(border) == _TOKEN_MAP_IN[self.player] or self.get_token(border) == 0:
                            path1 = self.compute_path(self.n, endpoints[0], border, self.occ_coords, self.axial_distance)
                            dist1 = len(path1)
                            if dist1 < nearest_dist1:
                                nearest_dist1 = dist1
                                closest_border1 = border
                    else:
                        if self.get_token(border) == _TOKEN_MAP_IN[self.player] or self.get_token(border) == 0:
                            path2 = self.compute_path(self.n, endpoints[1], border, self.occ_coords, self.axial_distance)
                            dist2 = len(path2)
                            if dist2 < nearest_dist2:
                                nearest_dist2 = dist2
                                closest_border2 = border
                border_targets.append(closest_border1)
                border_targets.append(closest_border2)
        elif len(endpoints) == 1:
            closest_border = (-1, -1)
            nearest_dist = 999
            for border in borders:
                skip = False
                for coord in maxChain:
                    if (coord[_PLAYER_AXIS[self.player]] == border[_PLAYER_AXIS[self.player]] == self.n - 1) or (coord[_PLAYER_AXIS[self.player]] == border[_PLAYER_AXIS[self.player]] == 0):
                        skip = True
                        break
                if (skip == False):
                    if self.get_token(border) == _TOKEN_MAP_IN[self.player] or self.get_token(border) == 0:
                        path = self.compute_path(self.n, endpoints[0], border, self.occ_coords, self.axial_distance)
                        dist = len(path)
                        if dist < nearest_dist:
                            nearest_dist = dist
                            closest_border = border
            border_targets.append(closest_border)
            
            
            
        # Find the shortest path from ends to the borders
        paths = []
        for i in range(len(endpoints)):
            path = self.compute_path(self.n, endpoints[i], border_targets[i], self.occ_coords, self.axial_distance)
            paths.append(path)

        adjust = 0
        for path in paths:
            if path != []:
                adjust += 1
            value += len(path)
        value -= adjust # Taking into account that a chain can have two different endpoints

        self.set_token(coord, 0)

        # Find out if the opponent can be attacked
        block_moves = []
        if self.player == RED:
            opp = BLUE
        else:
            opp = RED
        oppChain, endpointsOpp = self.find_opp_longest_chain()

        # Ignore the opponent endpoints if already at the border
        remove = []
        for endpoint in endpointsOpp:
            if endpoint in self.border_coords[self.player]:
                remove.append(endpoint)
        for endpoint in remove:
            endpointsOpp.remove(endpoint)

        # Block a sufficiently long chain of the opponent
        pos_block_moves = []
        if len(oppChain) > float(self.n) / 2:
            for endpoint in endpointsOpp:
                for neighbour in self._coord_neighbours(endpoint):
                    
                    if self.get_token(neighbour) == 0:
                       
                        opp_around = 0
                        for neighbour2 in self._coord_neighbours(neighbour):
                            if self.get_token(neighbour2) == _TOKEN_MAP_IN[opp] and neighbour2 in oppChain:
                                opp_around += 1
                        if opp_around == 1:
                            
                            pos_block_moves.append(neighbour)

            for move in pos_block_moves:
                for move2 in pos_block_moves:
                    
                    dist = self.axial_distance(move, move2)
                    if dist == 2:
                        block_moves.append(move)
                        
            block_moves = list(set(block_moves))
            
        if coord in block_moves:
            value = 999
                

        # Check if a capture can be made
        captured = self.check_captures(coord)
        if len(captured) != 0:
            value = 9999
            
                            

        return value        

    def swap(self):
        """
        Swap player positions by mirroring the state along the major 
        board axis.
        """
        (y, x) = self.opening_move
        self.set_token(self.opening_move, 0)
        self.set_token((x,y), 2)
        self.occ_coords.remove((y,x))
        self.occ_coords.append((x,y))

    def make_best_move(self):
        bestScore = -inf
        bestMove = None
        for move in self.get_possible_moves():
            score = self.minimax(move, 4, -inf, +inf, True)
            if (score > bestScore):
                bestScore = score
                bestMove = move
        return bestScore, bestMove

    def minimax(self, move, depth, alpha, beta, maximize):
        
        if depth == 0:
            return self.eval(move)
        if maximize:
            self.player = self.original_player
            max_eval = -inf
            for move in self.get_possible_moves():
                self.set_token(move, _TOKEN_MAP_IN[self.player])
                f_eval = self.minimax(move, depth - 1, alpha, beta, False)
                self.set_token(move, 0)
                max_eval = max(max_eval, f_eval)
                alpha = max(alpha, max_eval)
                if alpha < beta:
                    break
            return max_eval
        else:
            if self.player == RED:
                self.player = BLUE
            else:
                self.player = RED 
            min_eval = +inf
            for move in self.get_possible_moves():
                self.set_token(move, _TOKEN_MAP_IN[self.player])
                f_eval = self.minimax(move, depth - 1, alpha, beta, True)
                self.set_token(move, 0)
                min_eval = min(min_eval, f_eval)
                beta = min(beta, min_eval)
                if alpha < beta:
                    break
            return min_eval
