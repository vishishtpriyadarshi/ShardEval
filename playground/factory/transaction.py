class Transaction:
    """docstring for Transaction"""

    def __init__(self, identifier, creationTime, value, reward):
        self.identifier = identifier
        self.creationTime = creationTime
        self.miningTime = 0
        self.value = value
        self.reward = reward

    def display(self):
        print(self.identifier)

