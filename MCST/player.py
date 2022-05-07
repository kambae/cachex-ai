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

    playout_num = 1000

    def __init__(self, player, n):
        self.board = Board(n)
        self.player = player
        self.board_values = [(i // n, i % n) for i in range(0, np.square(n))]

        self.enemy = [i for i in self.COLOURS if not i == self.player][0]

    def action(self):
        wins = {}
        games = {}

        for i in range(0, self.playout_num):
            selected_action = self.select_move(self.board)

            if selected_action not in wins:
                wins[selected_action] = 0
            if selected_action not in games:
                games[selected_action] = 0

            if self.playout(copy.deepcopy(self.board), selected_action, 1) == 1:
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

        hex_groups = DisjointSet(self.board_values.extend([self.START_HEX, self.END_HEX]), hex_parents)

        for coord in your_hexes:
            for neigh in board._coord_neighbours(coord):
                if board[neigh] == player:
                    hex_groups.union(coord, neigh)

        return hex_groups

    def playout(self, board, action, turn, hex_groups=None, enemy_hex_groups=None):
        player_groups = self.calculate_hex_groups(board, self.player) if hex_groups is None else hex_groups
        enemy_groups = self.calculate_hex_groups(board, self.enemy) if enemy_hex_groups is None else enemy_hex_groups

        captured = board.place(self.player if turn == 1 else self.enemy, action)

        if len(captured) > 0:
            player_groups = self.calculate_hex_groups(board, self.player)
            enemy_groups = self.calculate_hex_groups(board, self.enemy)
        else:
            cur_groups = player_groups if turn == 1 else enemy_groups
            for neigh in board._coord_neighbours(action):
                if board[neigh] == (self.player if turn == 1 else self.enemy):
                    cur_groups.union(neigh, action)

        # print_board(board)
        if player_groups.find(self.END_HEX) == player_groups.find(self.START_HEX):
            return 1
        elif enemy_groups.find(self.END_HEX) == enemy_groups.find(self.START_HEX):
            return -1

        return self.playout(board, self.select_move(board), -turn, player_groups, enemy_groups)

    def select_move(self, board):
        action_set = [i for i in self.board_values if not board.is_occupied(i)]
        return random.choice(action_set)
    
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
