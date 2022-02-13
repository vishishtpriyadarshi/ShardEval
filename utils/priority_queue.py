"""
Custom Priority Queue implementation to maintain the order of 
transactions to be proposed by a full node, with key as the reward
"""

class PriorityQueue:
    def __init__(self):
        self.queue = []

    def is_empty(self):
        return len(self.queue) == []

    def is_present(self, transaction):
        return transaction in self.queue

    def length(self):
        return len(self.queue)

    def insert(self, new_transaction):
        idx = 0
        while (idx < len(self.queue) and 
                self.queue[idx].reward >= new_transaction.reward):
            idx += 1
        self.queue.insert(idx, new_transaction)

    def pop(self, count):
        count = min(self.length(), count)
        elements = self.queue[:count]
        self.queue = self.queue[count:]
        return elements

    def remove(self, transaction):
        self.queue.remove(transaction)

    def get(self, count):
        count = min(self.length(), count)
        return self.queue[:count]

    def display(self):
        for tx in self.queue:
            print(tx.id, end=" ")
        print()