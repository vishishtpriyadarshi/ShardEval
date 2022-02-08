class Transaction:
    """
    This class models a transaction
    """

    def __init__(self, id, creation_time, value, reward, state):
        self.id = id
        self.creation_time = creation_time
        self.miningTime = 0
        self.value = value
        self.reward = reward
        self.state = {}

    def display(self):
        print(self.id)