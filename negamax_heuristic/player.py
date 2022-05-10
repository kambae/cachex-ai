from negamax import player


class Player(player.Player):
    depth = 2
    def evaluate(self, board):
        player_hexes = board.red_hexes if self.player == "red" else board.blue_hexes
        enemy_hexes = board.blue_hexes if self.enemy == "blue" else board.red_hexes
        return self.get_player_min_placements(board, self.enemy) - self.get_player_min_placements(board, self.player) + 1/1000 * (len(player_hexes) - len(enemy_hexes))
