import numpy as np
from randomplayer.board import Board
import copy
import math

class Player:
    depth = 3

    def __init__(self, player, n):
        self.board = Board(n)
        self.player = player

    # find action based on negamax with alpha-beta pruning
    # evalution function is (opponent minimum placements to win - your minimum placements to win)
    #
    # note that placements to win is given by a graph search from start to end,
    # with your tokens as 0 edge and theirs as obstacles
    def action(self):
        actions, next_states = self.get_legal_moves(self.board)
        # todo sort actions, next_states

        best_value = -math.inf
        alpha = -math.inf
        beta = math.inf
        action = None

        for i in range(0, len(actions)):
            negamax = -self.negamax(next_states[i], self.depth - 1, -beta, -alpha, -1)
            if negamax > best_value:
                best_value = negamax
                action = actions[i]
            alpha = max(alpha, best_value)

        return ("PLACE", *action)


    def negamax(self, board, depth, alpha, beta, player_num):
        # todo: detect game end by repeat state/turns as well
        if depth == 0: # todo: or node is a terminal node
            return player_num * self.evaluate(board)

        next_states = self.get_legal_moves(board)[1]
        # todo: sort states

        value = -math.inf
        for state in next_states:
            value = max(value, -self.negamax(state, depth - 1, -beta, -alpha, -player_num))
            # note this is fail-soft
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    def get_legal_moves(self, board):
        board_values = [(i // board, i % board) for i in range(0, np.square(board))]
        action_set = [i for i in board_values if board.is_occupied(i)]
        next_states = [copy.deepcopy(board) for i in action_set]
        map(lambda i: next_states[i].place(self.player, action_set[i]), range(0, len(action_set)))

        return action_set, next_states

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
