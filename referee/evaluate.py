from game import *
from referee.player import PlayerWrapper

from tabulate import tabulate
import numpy as np

players = {
    "greedy": ("greedy", "Player"),
    "AIFTB": ("AIFTB","Player"),
    "MCST": ("MCST", "Player"),
    "Minimax 1": ("negamax_heuristic", "Player"),
    "Minimax 2": ("negamax_simple_heuristic", "Player"),
    "Random": ("randomplayer", "Player")
}

size = 6
print("SIZE: ", size)

player_names = list(players.keys())
results = [[0 for i in range(0, len(player_names))] for j in range(0, len(player_names))]
num_plays = 4

for i in range(0, len(player_names)):
    for j in range(0, len(player_names)):
        if i != j:
            for k in range(0, num_plays):
                player1 = players[player_names[i]]
                player2 = players[player_names[j]]

                p1 = PlayerWrapper(
                    "player 1",
                    player1,
                )
                p2 = PlayerWrapper(
                    "player 2",
                     player2,
                )

                result = play([p1, p2], n=size, print_state=False)

                if result == "winner: blue":
                    results[j][i] += 1
                else:
                    results[i][j] += 1

for i in range(0, len(player_names)):
    results[i].insert(0, player_names[i])

results.insert(0, ["Agent"] + player_names)

print(tabulate(results))