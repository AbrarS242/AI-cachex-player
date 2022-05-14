from numpy import zeros
from random import randint

_STEAL_ACT_LEN = 2
_PLACE_ACT_LEN = 3
_TOKEN_MAP_OUT = { 0: None, 1: "red", 2: "blue" }
_TOKEN_MAP_IN = {v: k for k, v in _TOKEN_MAP_OUT.items() }
_ACT_X_POS = 1
_ACT_Y_POS = 2

class Player:

    
    def __init__(self, player, n):
        """
        Called once at the beginning of a game to initialise this player.
        Set up an internal representation of the game state.

        The parameter player is the string "red" if your player will
        play as Red, or the string "blue" if your player will play
        as Blue.
        """
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
        valid_move = False
        
        # Select a random move
        while valid_move = False:
            x = randint(0,self.ub)
            aX = self.axial_x(x)
            y = randint(0,self.ub)
            if (self._data[aX][y] == 0):
                break
            
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
        
        if len(action) == _PLACE_ACT_LEN:
            x = self.axial_x(action[_ACT_X_POS])  
            y = action[_ACT_Y_POS]
            self._data[x][y] = _TOKEN_MAP_IN[player]

        self.n_turns += 1
            
        print(self._data)


    def axial_x(self, x):
        """
        Flips the value of the x-coordinate along the middle of the board to
        get an axial x-coordinate.
        """
        mid = int(self.n / 2)
        x = (mid - x) + mid
        return x

        
