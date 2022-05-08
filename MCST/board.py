"""
Provide a class to maintain the state of a Cachex game board, including
some helper methods to assist in updating and searching the board.

NOTE:
This board representation is designed to be used internally by the referee
for the purposes of validating actions and displaying the result of the game.
Each player is expected to store its own internal representation of the board
for use in informing decisions about which action to choose each turn. Please
don't assume this class is an "ideal" board representation for your own agent; 
you should think carefully about how to design your own data structures for 
representing the state of a game, with respect to your chosen strategy. 
"""

from queue import Queue
from numpy import zeros, array, roll, vectorize, append
import numpy as np
import functools

# Utility function to add two coord tuples
_ADD = lambda a, b: (a[0] + b[0], a[1] + b[1])
_SUBTRACT = lambda a, b: (a[0] - b[0], a[1] - b[1])

# Neighbour hex steps in clockwise order
_HEX_STEPS = array([(1, -1), (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1)], 
    dtype="i,i")

# Pre-compute diamond capture patterns - each capture pattern is a 
# list of offset steps:
# [opposite offset, neighbour 1 offset, neighbour 2 offset]
#
# Note that the "opposite cell" offset is actually the sum of
# the two neighbouring cell offsets (for a given diamond formation)
#
# Formed diamond patterns are either "longways", in which case the
# neighbours are adjacent to each other (roll 1), OR "sideways", in
# which case the neighbours are spaced apart (roll 2). This means
# for a given cell, it is part of 6 + 6 possible diamonds.
_CAPTURE_PATTERNS = [[_ADD(n1, n2), n1, n2] 
    for n1, n2 in 
        list(zip(_HEX_STEPS, roll(_HEX_STEPS, 1))) + 
        list(zip(_HEX_STEPS, roll(_HEX_STEPS, 2)))]

_CAPTURE_NEIGHBOURHOOD = append(_HEX_STEPS, array([(2, -1), (1, 1), (-1, 2), (-2, 1), (-1, -1), (1, -2)], dtype="i,i"))

# Maps between player string and internal token type
_TOKEN_MAP_OUT = { 0: None, 1: "red", 2: "blue" }
_TOKEN_MAP_IN = {v: k for k, v in _TOKEN_MAP_OUT.items()}

# Map between player token types
_SWAP_PLAYER = { 0: 0, 1: 2, 2: 1 }

# memoise captures
capture_map = {}
for k in _TOKEN_MAP_OUT.keys():
    capture_map[k] = {}

capture_neighbourhood_square_map = {}
coord_neighbour_map = {}

class Board:
    def __init__(self, n):
        """
        Initialise board of given size n.
        """
        self.n = n
        self._data = zeros((n, n), dtype=int)

        self.board_values = [(i // n, i % n) for i in range(0, np.square(n))]
        self.red_hexes = set()
        self.blue_hexes = set()
        self.unoccupied = set(self.board_values)


    def __getitem__(self, coord):
        """
        Get the token at given board coord (r, q).
        """
        return _TOKEN_MAP_OUT[self._data[coord]]

    def __setitem__(self, coord, token):
        """
        Set the token at given board coord (r, q).
        """
        if token is None:
            self.red_hexes.discard(coord)
            self.blue_hexes.discard(coord)
            self.unoccupied.add(coord)
        elif token == "red":
            self.red_hexes.add(coord)
            self.unoccupied.discard(coord)
        elif token == "blue":
            self.blue_hexes.add(coord)
            self.unoccupied.discard(coord)

        self._data[coord] = _TOKEN_MAP_IN[token]

    def digest(self):
        """
        Digest of the board state (to help with counting repeated states).
        Could use a hash function, but not really necessary for our purposes.
        """
        return self._data.tobytes()

    def swap(self):
        """
        Swap player positions by mirroring the state along the major 
        board axis. This is really just a "matrix transpose" op combined
        with a swap between player token types.
        """
        # todo: update red_hexes and blue_hexes and unoccupied
        swap_player_tokens = vectorize(lambda t: _SWAP_PLAYER[t])
        self._data = swap_player_tokens(self._data.transpose())

    def place(self, token, coord):
        """
        Place a token on the board and apply captures if they exist.
        Return coordinates of captured tokens.
        """
        self[coord] = token
        return self._apply_captures(coord)

    def connected_coords(self, start_coord):
        """
        Find connected coordinates from start_coord. This uses the token 
        value of the start_coord cell to determine which other cells are
        connected (e.g., all will be the same value).
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
                if coord not in reachable and self._data[coord] == token_type:
                    queue.put(coord)

        return list(reachable)

    @functools.lru_cache(maxsize=None)
    def inside_bounds(self, coord):
        """
        True iff coord inside board bounds.
        """
        r, q = coord
        return r >= 0 and r < self.n and q >= 0 and q < self.n

    def is_occupied(self, coord):
        """
        True iff coord is occupied by a token (e.g., not None).
        """
        return self[coord] != None

    def _apply_captures(self, coord):
        """
        Check coord for diamond captures, and apply these to the board
        if they exist. Returns a list of captured token coordinates.
        """

        def _get_capture_neighbourhood(placed_coord):
            if placed_coord in capture_neighbourhood_square_map:
                neighbourhood = capture_neighbourhood_square_map[placed_coord]
            else:
                neighbourhood = [_ADD(placed_coord, s) for s in _CAPTURE_NEIGHBOURHOOD]
                capture_neighbourhood_square_map[placed_coord] = neighbourhood

            return tuple([-1 if not self.inside_bounds(i) else self._data[i] for i in neighbourhood])

        opp_type = self._data[coord]

        capture_neighbourhood = _get_capture_neighbourhood(coord)
        if capture_neighbourhood in capture_map[opp_type]:
            captures = [_ADD(coord, s) for s in capture_map[opp_type][capture_neighbourhood]]
            # Remove any captured tokens
            for coord in captures:
                self[coord] = None
            return captures

        mid_type = _SWAP_PLAYER[opp_type]
        captured = set()

        # Check each capture pattern intersecting with coord
        for pattern in _CAPTURE_PATTERNS:
            coords = [_ADD(coord, s) for s in pattern]
            # No point checking if any coord is outside the board!
            if all(map(self.inside_bounds, coords)):
                tokens = [self._data[coord] for coord in coords]
                if tokens == [opp_type, mid_type, mid_type]:
                    # Capturing has to be deferred in case of overlaps
                    # Both mid cell tokens should be captured
                    captured.update(coords[1:])

        capture_map[opp_type][capture_neighbourhood] = [_SUBTRACT(s, coord) for s in list(captured)]

        # Remove any captured tokens
        for coord in captured:
            self[coord] = None

        return list(captured)

    def _coord_neighbours(self, coord):
        """
        Returns (within-bounds) neighbouring coordinates for given coord.
        """

        if coord in coord_neighbour_map:
            return coord_neighbour_map[coord]

        neighbours = [_ADD(coord, step) for step in _HEX_STEPS \
            if self.inside_bounds(_ADD(coord, step))]
        coord_neighbour_map[coord] = neighbours
        return neighbours
