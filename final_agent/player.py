import time
import gc

from numpy import zeros, array, roll
from random import randint
from queue import Queue

# Action types (taken from 'referee' module)
_ACTION_PLACE = "PLACE"
_ACTION_STEAL = "STEAL"

# Axis goals gor each player (taken from the 'referee' module)
_PLAYER_AXIS = {
    "red": 0, # Red aims to form path in r/0 axis
    "blue": 1 # Blue aims to form path in q/1 axis
}

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

        The parameter player is the string "red" if your player will
        play as Red, or the string "blue" if your player will play
        as Blue.
        """

        #Initialise the timer
        self.time_limit = n**2
        self.timer = _CountdownTimer(self.time_limit)

        with self.timer:
            
            # Initialise the board 
            self.n = n
            self.n_turns = 0
            self.ub = self.n - 1
            self._data = zeros((n,n), dtype=int)

            print(self._data)

    def action(self):
        """
        Called at the beginning of your turn. Based on the current state
        of the game, select an action to play.
        """

        with self.timer:
            
            valid_move = False
            
            # Select a random move
            while valid_move == False:
                x = randint(0,self.ub)
                aX = self.axial_x(x)
                y = randint(0,self.ub)
                if self._data[aX][y] == 0:

                    # Cannot place token in the center if it is the first turn of the game (and the board size is odd)
                    if self.n % 2 == 1 and self.n_turns == 0 and aX * 2 == y * 2 == self.n - 1:
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

        with self.timer:
            if action[0] == _ACTION_PLACE:

                # Find the coordinates
                _, x, y = action
                coord = (x,y)

                # Place the token on the board
                self.set_token(coord, _TOKEN_MAP_IN[player])

                if self.n_turns > (self.n) * 2 - 1:
                    print(self.detect_win(coord, player))

                # Check if any captures have taken place
                self.apply_captures(coord)

            self.n_turns += 1
                
            print(self._data)


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
        if they exist. Returns a list of captured token coordinates
        (taken from the 'referee' module).
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

    def inside_bounds(self, coord):
        """
        True iff coord inside board bounds
        (taken from the 'referee' module).
        """
        r, q = coord
        return r >= 0 and r < self.n and q >= 0 and q < self.n

    def detect_win(self, coord, player):
        """
        Check if the current placement causes a victory for the player
        (taken from the 'referee' module).
        """
        r, q = coord
        reachable = self.connected_coords((r, q))
        axis_vals = [c_coord[_PLAYER_AXIS[player]] for c_coord in reachable]
        if min(axis_vals) == 0 and max(axis_vals) == self.n - 1:
            return True
        else:
            return False

    def _coord_neighbours(self, coord):
        """
        Returns (within-bounds) neighbouring coordinates for given coord
        (taken from the 'referee' module).
        """
        return [_ADD(coord, step) for step in _HEX_STEPS \
            if self.inside_bounds(_ADD(coord, step))]

    def connected_coords(self, start_coord):
        """
        Find connected coordinates from start_coord. This uses the token 
        value of the start_coord cell to determine which other cells are
        connected (e.g., all will be the same value)
        - taken from the 'referee' module.
        """
        # Get search token type
        token_type = self._data[start_coord]

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

        return list(reachable)

class _CountdownTimer:
    """
    Reusable context manager for timing specific sections of code

    * measures CPU time, not wall-clock time
    * unless time_limit is 0, throws an exception upon exiting the context
      after the allocated time has passed

    (taken from the 'referee' module)
    """

    def __init__(self, time_limit):
        """
        Create a new countdown timer with time limit `limit`, in seconds
        (0 for unlimited time)
        """
        self.limit = time_limit
        self.clock = 0
        

    def __enter__(self):
        # clean up memory off the clock
        gc.collect()
        # then start timing
        self.start = time.process_time()
        return self  # unused

    def __exit__(self, exc_type, exc_val, exc_tb):
        # accumulate elapsed time since __enter__
        elapsed = time.process_time() - self.start
        self.clock += elapsed
        print(
            f"AAA time:  +{elapsed:6.3f}s  (just elapsed)  "
            f"AAA {self.clock:7.3f}s  (game total)"
        )



        


        
