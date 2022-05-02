class Player:
    def __init__(self, player, n):
        pass

    def action(self):
        """
        Called at the beginning of your turn. Based on the current state
        of the game, select an action to play.
        """

        chosen = tuple(map(int, input("Enter move:\n").split()))

        return ("PLACE", *chosen)

    def turn(self, player, action):
        pass