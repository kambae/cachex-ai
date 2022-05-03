import numpy as np
from negamax.board import Board
import copy
import math
import functools
import random

class Player:
    depth = 2
    COLOURS = ["red", "blue"]

    def __init__(self, player, n):
        self.board = Board(n)
        self.player = player

        self.enemy = [i for i in self.COLOURS if not i == self.player][0]

    # find action based on negamax with alpha-beta pruning
    # evalution function is (opponent minimum placements to win - your minimum placements to win)
    #
    # note that placements to win is given by a graph search from start to end,
    # with your tokens as 0 edge and theirs as obstacles
    # todo: code for swap?
    def action(self):
        actions, next_states = self.get_legal_moves(self.board, self.player)
        # todo sort actions, next_states

        best_value = -math.inf
        alpha = -math.inf
        beta = math.inf
        action = random.choice(actions)

        for i in range(0, len(actions)):
            negamax = -self.negamax(next_states[i], self.depth - 1, -beta, -alpha, -1)
            if negamax > best_value:
                best_value = negamax
                action = actions[i]
            alpha = max(alpha, best_value)

        return ("PLACE", *action)

    # player_num = 1 for player and player_num = -1 for opponent
    def negamax(self, board, depth, alpha, beta, player_num):
        # todo: detect game end by repeat state/turns as well
        # check if node is terminal
        winner = self.check_winner(board)
        if winner:
            return player_num * (math.inf if self.player == winner else -math.inf)

        if depth == 0:
            return player_num * self.evaluate(board)

        next_states = self.get_legal_moves(board, self.player if player_num == 1 else self.enemy)[1]
        # todo: sort states

        value = -math.inf
        for state in next_states:
            value = max(value, -self.negamax(state, depth - 1, -beta, -alpha, -player_num))
            # note this is fail-soft
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    def get_legal_moves(self, board, player):
        board_values = [(i // board.n, i % board.n) for i in range(0, np.square(board.n))]
        action_set = [i for i in board_values if not board.is_occupied(i)]
        next_states = [copy.deepcopy(board) for i in action_set]
        for i in range(0, len(action_set)):
            next_states[i].place(player, action_set[i])
        # map(lambda i: next_states[i].place(self.player, action_set[i]), range(0, len(action_set)))

        return action_set, next_states

    def check_winner(self, board):
        for player in self.COLOURS:
            if self.get_player_min_placements(board, player) == 0:
                return player
        return None

    def evaluate(self, board):
        return self.get_player_min_placements(board, self.enemy) - self.get_player_min_placements(board, self.player)

    # apply dijkstra
    # todo: this bit is kinda shit, refactor if necessary
    @functools.lru_cache(maxsize=None)
    def get_player_min_placements(self, board, player):
        def path_heuristic(a):
            return 0

        def get_neighbours(a):
            if a == (-1, -1):
                return [(0, i) for i in range(0, n) if is_valid_neighbour((0, i))] if player == "red" else [(i, 0) for i in range(0, n) if is_valid_neighbour((i, 0))]

            # we take this from class board as _coord_neighbours is essentially static and now it gets memoised
            neighbours = [i for i in self.board._coord_neighbours(a) if is_valid_neighbour(i)]

            if (player == "red" and a[0] == n - 1) or (player == "blue" and a[1] == n - 1):
                neighbours.append((n, n))

            return neighbours

        def get_edge_weight(a, b):
            if b == (n, n) or board[b] == player:
                return 0
            return 1

        def is_valid_neighbour(a):
            return board[a] == player or board[a] is None

        n = board.n
        start = (-1, -1)
        goal = (n, n)

        prev = {start: None}
        dist = {start: 0}
        pq = PriorityQueue()
        pq.insert(start, path_heuristic(start))
        while not pq.is_empty():
            curr = pq.pop()
            if curr == goal:
                return dist[goal]
            for neighbour in get_neighbours(curr):
                tentative_dist = dist[curr] + get_edge_weight(curr, neighbour)
                if neighbour not in dist or tentative_dist < dist[neighbour]:
                    pq.update(neighbour, tentative_dist + path_heuristic(neighbour))
                    prev[neighbour] = curr
                    dist[neighbour] = tentative_dist
        return math.inf

    
    def turn(self, player, action):
        atype, *aargs = action

        if atype == "STEAL":
            # Apply STEAL action
            self.board.swap()

        elif atype == "PLACE":
            # Apply PLACE action
            coord = tuple(aargs)
            self.board.place(player, coord)

# todo make prio queue efficient?
class PriorityQueue:
    def __init__(self):
        self.items = []

    def insert(self, item, prio):
        self.items.append({"prio": prio, "item": item})

    def pop(self):
        if len(self.items) == 0:
            return None
        self.items = sorted(self.items, key=lambda x: x["prio"])
        return self.items.pop(0)["item"]

    # removes all matches to item and replaces with new prio
    def update(self, item, prio):
        self.items = list(filter(lambda x: x["item"] != item, self.items))
        self.insert(item, prio)

    def is_empty(self):
        return len(self.items) == 0

    def __str__(self):
        return str(self.items)
