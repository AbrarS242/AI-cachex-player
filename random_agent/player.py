import time

from numpy import zeros, array, roll, vectorize
from random import randint
from queue import Queue

# Axis goals gor each player (taken from the 'referee' module)
_PLAYER_AXIS = {
    "red": 0,  # Red aims to form path in r/0 axis
    "blue": 1  # Blue aims to form path in q/1 axis
}

# Action types (taken from 'referee' module)
_ACTION_PLACE = "PLACE"
_ACTION_STEAL = "STEAL"

_STEAL_ACT_LEN = 2
_PLACE_ACT_LEN = 3

_ACT_X_POS = 1
_ACT_Y_POS = 2

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
        Sets up an internal representation of the game state.

        The parameter player is the string "red" if the player will
        play as Red, or the string "blue" if the player will play
        as Blue.
        """

        self.clock = 0
        self.player = player

        
        self.n = n
        self.n_turns = 1
        self.ub = self.n - 1
        self._data = zeros((n,n), dtype=int)
        self.occ_coords = []

    def action(self):
        """
        Called at the beginning of the player's turn. Based on the current state
        of the game, select an action to play.
        """
        valid_move = False
        
        # Select a random move
        while valid_move == False:
            x = randint(0,self.ub)
            aX = self.axial_x(x)
            y = randint(0,self.ub)
            if self._data[aX][y] == 0:
                valid_move= True
                # Cannot place token in the center if it is the first turn of the game
                if self.n_turns == 0 and aX * 2 == y * 2 == self.n - 1:
                    valid_move = False
                else:
                    valid_move = True


 
        return ("PLACE", x, y)

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
            coord = (x, y)

            # Place the token on the board
            self.set_token(coord, _TOKEN_MAP_IN[player])

            # Check if any captures have taken place
            self.apply_captures(coord)

            if self.n_turns > (self.n) * 2 - 1:
                print(self.detect_win(coord, player))
            self.occ_coords.append((x, y))

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
        x = abs((self.n - 1) - x)
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
        if they exist. Returns a list of captured token coordinates.
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
        print(captured)

    def inside_bounds(self, coord):
        """
        True iff coord inside board bounds.
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

    def _coord_neighbours(self, coord):
        """
        Returns (within-bounds) neighbouring coordinates for given coord
        (taken from the 'referee' module written by the COMP30024 teaching staff).
        """
        return [_ADD(coord, step) for step in _HEX_STEPS \
                if self.inside_bounds(_ADD(coord, step))]

        
