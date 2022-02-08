"""
Implementation of custom full node resource
"""
import simpy
import numpy as np
from network.block import Block
from network.broadcast import broadcast
from factory.transaction_pool import TransactionPool
from utils import get_block_delay, get_transmission_delay

class FullNode:
    """docstring for FullNode"""

    def __init__(
        self, identifier, env, neighbourList, pipes, nodes, location, data, params
    ):
        self.identifier = identifier
        self.env = env
        self.neighbourList = neighbourList
        self.pipes = pipes
        self.nodes = nodes
        self.location = location
        self.data = data
        self.params = params
        self.transactionPool = TransactionPool(
            env, identifier, neighbourList, nodes, params
        )
        self.blockchain = []
        self.currentBlockID = 0
        self.env.process(self.receiveBlock())

    def validator(self):
        """Validate transactions"""
        if bool(self.params["verbose"]):
            print("miner", self.pipes)

    def getBlockchain(self, destination):
        self.env.timeout(get_transmission_delay(self.location, destination) * 2)
        return self.blockchain

    def receiveBlock(self):
        """Receive newly mined block from neighbour"""
        while True:
            b = yield self.pipes[self.identifier].get()
            if len(self.blockchain) > 0:
                currID = int(self.blockchain[-1].identifier[1:])
            else:
                currID = -1
            currIDs = [x.identifier for x in self.blockchain]
            if int(b.identifier[1:]) == currID + 1 and b.identifier not in currIDs:
                """Remove already mined transactions from private pool"""
                for transaction in b.transactionList:
                    if self.transactionPool.transactionQueue.isPresent(transaction):
                        self.transactionPool.transactionQueue.remove(transaction)
                        self.transactionPool.prevTransactions.append(transaction)
                """Append block to own chain"""
                self.blockchain.append(b)
                if bool(self.params["verbose"]):
                    print(
                        "%7.4f" % self.env.now
                        + " : "
                        + "%s" % self.identifier
                        + " added Block %s" % b.identifier
                        + " to the chain"
                    )
                    self.displayChain()
                """Mark the receive time of the block"""
                self.data["blockProp"][b.hash][1] = self.env.now
            else:
                """If an invalid block is received, check neighbours and update 
				the chain if a longer chain is found"""
                self.updateBlockchain()

    def updateBlockchain(self):
        """Update blockchain by requesting blocks from peers"""
        maxChain = self.blockchain.copy()
        neighbourID = ""
        flag = False
        numStaleBlocks = 0

        for neighbour in self.neighbourList:
            neighbourChain = self.nodes[neighbour].getBlockchain(self.location)
            if len(maxChain) < len(neighbourChain):
                maxChain = neighbourChain.copy()
                neighbourID = neighbour
                flag = True
        numStaleBlocks = len(maxChain) - len(self.blockchain)
        self.data["numStaleBlocks"] += numStaleBlocks
        self.blockchain = maxChain.copy()
        if flag:
            self.currentBlockID = int(self.blockchain[-1].identifier[1:]) + 1
        if bool(self.params["verbose"]):
            if neighbourID:
                print(
                    "%7.4f" % self.env.now
                    + " : "
                    + "%s" % self.identifier
                    + " updated to chain of %s and reverted %d blocks"
                    % (neighbourID, numStaleBlocks)
                )

    def displayChain(self):
        chain = [b.identifier for b in self.blockchain]
        print(
            "%7.4f" % self.env.now
            + " : %s" % self.identifier
            + " has current chain: %s" % chain
        )

    def displayLastBlock(self):
        if self.blockchain:
            block = self.blockchain[-1]
            transactions = block.transactionList
        print(
            "%7.4f" % self.env.now
            + " : %s" % self.identifier
            + " has last block: %s" % transactions
        )

