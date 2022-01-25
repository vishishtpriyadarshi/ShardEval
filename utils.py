import numpy as np
import json


def get_block_delay(mu, sigma):
    delay = mu + sigma * np.random.randn()
    if delay < 0:
        return get_block_delay(mu, sigma)
    return delay


def get_transaction_delay(mu, sigma):
    delay = mu + sigma * np.random.randn()
    if delay < 0:
        return get_transaction_delay(mu, sigma)
    return delay


def get_transmission_delay(source, destination):
    with open("config/params.json", "r") as f:
        params = f.read()
    params = json.loads(params)
    mu = params["delay"][source][destination]["mu"]
    sigma = params["delay"][source][destination]["sigma"]
    delay = mu + sigma * np.random.randn()
    if delay < 0:
        return get_transmission_delay(source, destination)
    return delay


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