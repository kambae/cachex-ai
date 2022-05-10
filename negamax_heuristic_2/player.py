from negamax import player
import numpy as np
from functools import lru_cache


class Player(player.Player):
    depth = 2

    def evaluate(self, board):
        player_hexes = board.red_hexes if self.player == "red" else board.blue_hexes
        enemy_hexes = board.blue_hexes if self.enemy == "blue" else board.red_hexes

        def get_centrality_score(hexes):
            return - sum([get_hex_centrality(hex) for hex in hexes])

        @lru_cache(maxsize=None)
        def get_hex_centrality(hex):
            return np.linalg.norm(np.array([hex]) - np.array([self.n / 2, self.n / 2]))

        return self.get_player_min_placements(board, self.enemy) - self.get_player_min_placements(board, self.player) + 1/1000 * (len(player_hexes) - len(enemy_hexes)) + 1/100000 * get_centrality_score(player_hexes)
