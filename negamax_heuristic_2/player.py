from negamax import player


class Player(player.Player):
    depth = 2

    def evaluate(self, board):
        player_hexes = board.red_hexes if self.player == "red" else board.blue_hexes
        enemy_hexes = board.blue_hexes if self.enemy == "blue" else board.red_hexes

        def get_total_tile_value(board_input, player_type, hexes):
            triples = set()
            for hex in hexes:
                candidates = set()
                for coord in board_input._coord_neighbours(hex):
                    if board_input[coord] == player_type:
                        candidates.add(coord)
                for i in candidates:
                    for coord in board_input._coord_neighbours(i):
                        if coord in candidates:
                            triples.add(frozenset({hex, i, coord}))
            return len(triples)

        return 10/self.get_player_min_placements(board, self.player) - 20/self.get_player_min_placements(board, self.enemy) + len(player_hexes) - len(enemy_hexes)

