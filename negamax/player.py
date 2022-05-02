import numpy as np
from randomplayer.board import Board
import copy
import math

class Player:
    def __init__(self, player, n):
        self.board = Board(n)
        self.player = player

    # find action based on negamax with alpha-beta pruning
    # evalution function is (opponent minimum placements to win - your minimum placements to win)
    #
    # note that placements to win is given by a graph search from start to end,
    # with your tokens as 0 edge and theirs as obstacles
    def action(self):


    def negamax(self, board, depth, alpha, beta, player_num):
        # todo: detect game end by repeat state/turns as well
        if depth == 0: # todo: or node is a terminal node
            return player_num * self.evaluate(board)

        board_values = [(i // board, i % board) for i in range(0, np.square(board))]
        action_set = [i for i in board_values if board.is_occupied(i)]
        next_states = [copy.deepcopy(board) for i in action_set]
        map(lambda i: next_states[i].place(self.player, action_set[i]), range(0, len(action_set)))
        # todo: sort states

        value = -math.inf
        for state in next_states:
            value = max(value, -self.negamax(state, depth - 1, -beta, -alpha, -player_num))
            # note this is fail-soft
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    def evaluate(self, board):
        return 0


    
    def turn(self, player, action):
        atype, *aargs = action

        if atype == "STEAL":
            # Apply STEAL action
            self.board.swap()

        elif atype == "PLACE":
            # Apply PLACE action
            coord = tuple(aargs)
            self.board.place(player, coord)
