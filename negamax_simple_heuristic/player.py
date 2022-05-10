import copy

from negamax import player
import math
import random
import numpy as np


def print_board(board):
    class GameBoard:
        def __init__(self):
            self.board = board
    from referee.game import _RENDER
    from referee.log import comment
    gameboard = GameBoard()
    comment(_RENDER(game=gameboard))


class Player(player.Player):
    depth = 3
    hex_group_dict = {}

    def __init__(self, player, n):
        super().__init__(player, n)
        self.board_values = [(i // n, i % n) for i in range(0, np.square(n))]

    def evaluate(self, board):
        player_hexes = board.red_hexes if player == "red" else board.blue_hexes
        enemy_hexes = board.blue_hexes if player == "blue" else board.red_hexes

        return len(player_hexes) - len(enemy_hexes)

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

    def check_winner(self, board):
        player_groups = self.hex_group_dict[board.digest()][self.player]
        enemy_groups = self.hex_group_dict[board.digest()][self.enemy]
        if player_groups.find(self.END_HEX) == player_groups.find(self.START_HEX):
            return self.player
        elif enemy_groups.find(self.END_HEX) == enemy_groups.find(self.START_HEX):
            return self.enemy
        return None

    def get_legal_moves(self, board, player, sorted=False):
        digest = board.digest()
        if digest not in self.hex_group_dict:
            self.hex_group_dict[digest] = {}
            self.hex_group_dict[digest][self.player] = self.calculate_hex_groups(board, self.player)
            self.hex_group_dict[digest][self.enemy] = self.calculate_hex_groups(board, self.enemy)

        player_hex_groups = self.hex_group_dict[digest][self.player]
        enemy_hex_groups = self.hex_group_dict[digest][self.enemy]
        cur_groups = player_hex_groups if self.player == player else enemy_hex_groups
        other_group = enemy_hex_groups if self.player == player else player_hex_groups
        not_player = self.enemy if player == self.player else self.player

        action_set = list(board.unoccupied - {self.CENTER_TILE}) if (
                    self.CENTER_TILE is not None and self.turn_num == 1) else list(board.unoccupied)
        # todo: keep random or no?
        random.shuffle(action_set)
        next_states = [self.copy_board(board) for i in action_set]
        if sorted:
            next_states.sort(
                key=lambda x: (len(x.red_hexes) - len(x.blue_hexes)) if player == "red" else len(x.blue_hexes) - len(
                    x.red_hexes))

        for i in range(0, len(action_set)):
            captured = next_states[i].place(player, action_set[i])
            new_digest = next_states[i].digest()

            if new_digest not in self.hex_group_dict:
                self.hex_group_dict[new_digest] = {}
                new_cur_groups = cur_groups.clone()
                self.hex_group_dict[new_digest][player] = new_cur_groups
                new_other_group = other_group.clone()
                self.hex_group_dict[new_digest][not_player] = new_other_group

                if len(captured) > 0:
                    roots = set([new_other_group.find(i) for i in captured])
                    to_recalculate = [i for i in self.board_values if new_other_group.find(i) in roots]
                    self.recalculate_hex_groups(board, new_other_group, to_recalculate, not_player)

                for neigh in self.board._coord_neighbours(action_set[i]):
                    if board[neigh] == player:
                        new_cur_groups.union(neigh, action_set[i])
        # map(lambda i: next_states[i].place(self.player, action_set[i]), range(0, len(action_set)))

        return action_set, next_states



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

    def clone(self):
        return DisjointSet(self.vertices.copy(), self.parent.copy())

