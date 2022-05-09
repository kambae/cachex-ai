import numpy as np
from negamax.board import Board
import copy
import math
import functools
import random

class Player:
    depth = 3
    COLOURS = ["red", "blue"]

    def __init__(self, player, n):
        self.board = Board(n)
        self.player = player
        self.n = n
        self.turn_num = 1

        self.enemy = [i for i in self.COLOURS if not i == self.player][0]

        self.START_HEX = (-1, -1)
        self.END_HEX = (n, n)

        self.CENTER_TILE = ((n-1)/2, (n-1)/2) if self.n % 2 == 1 else None

    # find action based on negamax with alpha-beta pruning
    # evalution function is (opponent minimum placements to win - your minimum placements to win)
    #
    # note that placements to win is given by a graph search from start to end,
    # with your tokens as 0 edge and theirs as obstacles
    # todo: code for swap?
    def action(self):
        if self.turn_num == 2:
            return ("STEAL", )
        
        actions, next_states = self.get_legal_moves(self.board, self.player, True)

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

            action = tuple([int(i) for i in action])

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

        sort_states = False if depth == 1 else True
        next_states = self.get_legal_moves(board, self.player if player_num == 1 else self.enemy, sort_states)[1]

        value = -math.inf
        for state in next_states:
            value = max(value, -self.negamax(state, depth - 1, -beta, -alpha, -player_num))
            # note this is fail-soft
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    def get_legal_moves(self, board, player, sorted=False):
        action_set = list(board.unoccupied - {self.CENTER_TILE}) if (self.CENTER_TILE is not None and self.turn_num == 1) else list(board.unoccupied)
        # todo: keep random or no?
        random.shuffle(action_set)
        next_states = [self.copy_board(board) for i in action_set]
        if sorted:
            next_states.sort(key=lambda x: (len(x.red_hexes) - len(x.blue_hexes)) if player=="red" else len(x.blue_hexes) - len(x.red_hexes))
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

    # apply A*
    @functools.lru_cache(maxsize=128)
    def get_player_min_placements(self, board, player):
        hexes = (len(board.red_hexes) if player == "red" else len(board.blue_hexes))

        def path_heuristic(a):
            return max(0, n - 1 - (a[0] if player == "red" else a[1]) - hexes)

        def get_neighbours(a):
            if a == self.START_HEX:
                return [(0, i) for i in range(0, n) if is_valid_neighbour((0, i))] if player == "red" else [(i, 0) for i in range(0, n) if is_valid_neighbour((i, 0))]

            # we take this from class board as _coord_neighbours is essentially static and now it gets memoised
            neighbours = [i for i in self.board._coord_neighbours(a) if is_valid_neighbour(i)]

            if (player == "red" and a[0] == n - 1) or (player == "blue" and a[1] == n - 1):
                neighbours.append(self.END_HEX)

            return neighbours

        @functools.lru_cache(maxsize=None)
        # edge weight only dependant on target hex here - now we can cache!
        def get_edge_weight(b):
            if b == self.END_HEX or board[b] == player:
                return 0
            return 1

        @functools.lru_cache(maxsize=None)
        def is_valid_neighbour(a):
            return board[a] == player or board[a] is None

        n = board.n
        start = self.START_HEX
        goal = self.END_HEX

        dist = {start: 0}
        pq = PriorityQueue()
        pq.insert(start, path_heuristic(start))
        while not pq.is_empty():
            curr = pq.pop()
            if curr == goal:
                return dist[goal]
            for neighbour in get_neighbours(curr):
                tentative_dist = dist[curr] + get_edge_weight(neighbour)
                if neighbour not in dist or tentative_dist < dist[neighbour]:
                    pq.update(neighbour, tentative_dist + path_heuristic(neighbour))
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

        self.turn_num += 1

    def copy_board(self, board):
        ret = Board(board.n)
        ret._data = board._data.copy()
        ret.blue_hexes = board.blue_hexes.copy()
        ret.red_hexes = board.red_hexes.copy()
        ret.unoccupied = board.unoccupied.copy()

        return ret

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
