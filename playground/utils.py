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
    with open("params/params.json", "r") as f:
        params = f.read()
    params = json.loads(params)
    mu = params["delay"][source][destination]["mu"]
    sigma = params["delay"][source][destination]["sigma"]
    delay = mu + sigma * np.random.randn()
    if delay < 0:
        return get_transmission_delay(source, destination)
    return delay


"""Custom Priority Queue implementation to maintain the order of 
transactions to be mined by a miner, with key as the miner reward"""


class PriorityQueue:
    def __init__(self):
        self.queue = []

    def isEmpty(self):
        return len(self.queue) == []

    def isPresent(self, transaction):
        return transaction in self.queue

    def length(self):
        return len(self.queue)

    def insert(self, newTransaction):
        indx = 0
        while (
            indx < len(self.queue) and self.queue[indx].reward >= newTransaction.reward
        ):
            indx += 1
        self.queue.insert(indx, newTransaction)

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
            print(tx.identifier, end=" ")
        print()

