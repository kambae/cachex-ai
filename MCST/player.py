import numpy as np
from MCST.board import Board
import copy
import math
import functools
import random


def print_board(board):
    class GameBoard:
        def __init__(self):
            self.board = board
    from referee.game import _RENDER
    from referee.log import comment
    gameboard = GameBoard()
    comment(_RENDER(game=gameboard))

class Player:
    COLOURS = ["red", "blue"]
    START_HEX = (-2, -2)
    END_HEX = (-1, -1)

    playout_num = 2000
    c = np.sqrt(2)

    def __init__(self, player, n):
        self.board = Board(n)
        self.player = player
        self.board_values = [(i // n, i % n) for i in range(0, np.square(n))]

        self.enemy = [i for i in self.COLOURS if not i == self.player][0]

    def action(self):
        wins = {}
        games = {}

        wins_dict = {}
        plays_dict = {}

        for i in range(0, self.playout_num):
            selected_action = self.select_move(self.board, wins_dict, plays_dict, i)

            # todo: find out why np error is occuring without this line
            selected_action = tuple([int(i) for i in selected_action])

            if selected_action not in wins:
                wins[selected_action] = 0
            if selected_action not in games:
                games[selected_action] = 0

            result = self.playout(copy.deepcopy(self.board), selected_action, 1, wins_dict, plays_dict, i)
            self.update_digest_dict(self.board.digest(), selected_action, wins_dict, plays_dict, result)
            if result == 1:
                wins[selected_action] += 1
            games[selected_action] += 1
            # print("-----------------------------")

        win_prob = {k: wins[k]/games[k] for k in games.keys() & wins if games[k] > 0}
        action = max(win_prob, key=win_prob.get) if len(win_prob.keys()) > 0 else self.select_move(self.board)

        # print(win_prob)
        # print(games)
        # print(wins)
        return ("PLACE", *action)

    def calculate_hex_groups(self, board, player):
        is_start_hex = lambda coord: (coord[0] == 0 and player == "red") or (coord[1] == 0 and player == "blue")
        is_end_hex = lambda coord: (coord[0] == (self.board.n - 1) and player == "red") or (coord[1] == (self.board.n - 1) and player == "blue")

        your_hexes = [i for i in self.board_values if board[i] == player]
        hex_parents = {k: self.START_HEX if is_start_hex(k) else self.END_HEX if is_end_hex(k) else k for k in self.board_values}
        hex_parents[self.START_HEX] = self.START_HEX
        hex_parents[self.END_HEX] = self.END_HEX

        hex_groups = DisjointSet(self.board_values + [self.START_HEX, self.END_HEX], hex_parents)

        for coord in your_hexes:
            for neigh in board._coord_neighbours(coord):
                if board[neigh] == player:
                    hex_groups.union(coord, neigh)

        return hex_groups

    def recalculate_hex_groups(self, board, hex_groups, recalculate_vertices, player):
        is_start_hex = lambda coord: (coord[0] == 0 and player == "red") or (coord[1] == 0 and player == "blue")
        is_end_hex = lambda coord: (coord[0] == (self.board.n - 1) and player == "red") or (coord[1] == (self.board.n - 1) and player == "blue")

        for vertex in recalculate_vertices:
            hex_groups.parent[vertex] = self.START_HEX if is_start_hex(vertex) else self.END_HEX if is_end_hex(vertex) else vertex

        for coord in recalculate_vertices:
            for neigh in board._coord_neighbours(coord):
                if board[neigh] == player:
                    hex_groups.union(coord, neigh)

        return hex_groups

    def playout(self, board, action, turn, wins_dict, plays_dict, n, hex_groups=None, enemy_hex_groups=None):
        player = self.player if turn == 1 else self.enemy
        not_player = self.enemy if turn == 1 else self.player

        player_groups = self.calculate_hex_groups(board, self.player) if hex_groups is None else hex_groups
        enemy_groups = self.calculate_hex_groups(board, self.enemy) if enemy_hex_groups is None else enemy_hex_groups
        cur_groups = player_groups if turn == 1 else enemy_groups
        other_group = enemy_groups if turn == 1 else player_groups

        captured = board.place(player, action)

        if len(captured) > 0:
            roots = set([other_group.find(i) for i in captured])
            to_recalculate = [i for i in self.board_values if other_group.find(i) in roots]
            self.recalculate_hex_groups(board, other_group, to_recalculate, not_player)

        for neigh in board._coord_neighbours(action):
            if board[neigh] == player:
                cur_groups.union(neigh, action)

        # print_board(board)
        if player_groups.find(self.END_HEX) == player_groups.find(self.START_HEX):
            return 1
        elif enemy_groups.find(self.END_HEX) == enemy_groups.find(self.START_HEX):
            return -1

        result = self.playout(board, self.select_move(board, wins_dict, plays_dict, n), -turn, wins_dict, plays_dict, n, player_groups, enemy_groups)
        self.update_digest_dict(board.digest(), action, wins_dict, plays_dict, result)
        return result

    def update_digest_dict(self, digest, action, wins_dict, plays_dict, result):
        if digest not in wins_dict:
            wins_dict[digest] = {}
        if digest not in plays_dict:
            plays_dict[digest] = {}
        if action not in plays_dict[digest]:
            plays_dict[digest][action] = 0
        if action not in wins_dict[digest]:
            wins_dict[digest][action] = 0

        plays_dict[digest][action] += 1
        if result == 1:
            wins_dict[digest][action] += 1


    def select_move(self, board, wins_dict, plays_dict, n):
        digest = board.digest()
        action_set = list(board.unoccupied)

        ucts = {x: self.get_uct_value(digest, x, wins_dict, plays_dict, n) for x in action_set}
        max_uct = max(ucts.values())
        return random.choice([k for k in ucts if ucts[k] == max_uct])

        # if board.digest() == self.board.digest():
        #     print([self.get_uct_value(digest, i, wins_dict, plays_dict, n) for i in action_set])

        return action

    def get_uct_value(self, digest, action, wins_dict, plays_dict, n):
        if digest in plays_dict and action in plays_dict[digest]:
            ni = plays_dict[digest][action]
            wi = wins_dict[digest][action]
            return (wi/ni) + (self.c * np.sqrt(np.log(n)/ni))
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


class DisjointSet():
    def __init__(self, vertices=None, parent=None):
        self.vertices = vertices if vertices is not None else []
        self.parent = parent if parent is not None else {k: k for k in self.vertices}

    def __str__(self):
        return str(self.parent)

    def find(self, item):
        root = item
        while self.parent[root] != root:
            root = self.parent[root]

        while self.parent[item] != root:
            parent = self.parent[item]
            self.parent[item] = root
            item = parent

        return root

    def add(self, item, parent=None):
        if parent is None:
            parent = item
        self.vertices.append(item)
        self.parent[item] = parent

    def union(self, set1, set2):
        root1 = self.find(set1)
        root2 = self.find(set2)
        self.parent[root1] = root2
