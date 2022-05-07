import numpy as np
from MCST.board import Board
import copy
import math
import functools
import random

class Player:
    COLOURS = ["red", "blue"]
    START_HEX = (0, 0)
    END_HEX = (-1, -1)

    playout_num = 10000

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

        win_prob = {k: wins[k]/games[k] for k in games.keys() & wins if games[k] > 0}
        action = max(win_prob, key=win_prob.get) if len(win_prob.keys()) > 0 else self.select_move(self.board)

        return ("PLACE", *action)

    def calculate_hex_groups(self, board, player):
        hex_groups = {}

        your_hexes = [i for i in self.board_values if board[i] == player]

        for coord in self.board_values:
            is_start_hex = (coord[0] == 0 and player == "red") or (coord[1] == 0 and player == "blue")
            is_end_hex = (coord[0] == (self.board.n - 1) and player == "red") or (coord[1] == (self.board.n - 1) and player == "blue")
            hex_groups[coord] = {coord} | ({self.START_HEX} if is_start_hex else set()) | ({self.END_HEX} if is_end_hex else set())

        for coord in your_hexes:
            for neigh in board._coord_neighbours(coord):
                group = hex_groups[coord] | hex_groups[neigh]
                hex_groups[neigh] = group
                hex_groups[coord] = group

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
                group = cur_groups[action] | cur_groups[neigh]
                cur_groups[neigh] = group
                cur_groups[action] = group

        if action in player_groups and self.END_HEX in player_groups[action] and self.START_HEX in player_groups[action]:
            return 1
        elif action in enemy_groups and self.END_HEX in enemy_groups[action] and self.START_HEX in enemy_groups[action]:
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
