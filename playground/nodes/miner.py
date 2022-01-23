"""
Implementation of custom miner resource
"""
import simpy
import numpy as np

from network.block import Block
from nodes.full_node import FullNode
from network.broadcast import broadcast
from transaction_factory.transaction_pool import TransactionPool
from utils import get_block_delay, get_transaction_delay


class Miner(FullNode):
    """docstring for Miner"""

    def __init__(
        self,
        identifier,
        env,
        neighbourList,
        pipes,
        nodes,
        location,
        blockPropData,
        params,
    ):
        FullNode.__init__(
            self,
            identifier,
            env,
            neighbourList,
            pipes,
            nodes,
            location,
            blockPropData,
            params,
        )
        self.blockGeneratorAction = self.env.process(self.blockGenerator(params))

    def blockGenerator(self, params):
        """Block generator"""
        while True:
            try:
                delay = get_block_delay(self.params["blockMu"], self.params["blockSigma"])
                yield self.env.timeout(delay)

                transactionCount = int(params["blockCapacity"])
                transactionList = self.transactionPool.getTransaction(transactionCount)
                l = []
                for transaction in transactionList:
                    transaction.miningTime = self.env.now
                    """Simulating Tx validation time"""
                    self.env.timeout(0.1)
                    l.append(transaction.identifier)
                b = Block("B" + str(self.currentBlockID), transactionList, params)

                """Collection of data"""
                """If block has been mined earlier, inrease count of fork"""
                if b.identifier in [
                    id[: id.index("_")] for id in self.data["blockProp"].keys()
                ]:
                    self.data["numForks"] += 1

                print(
                    "%7.4f" % self.env.now
                    + " : %s proposing %s with transaction list count %d with transactions %s ..."
                    % (self.identifier, b.identifier, len(l), l[:3])
                )

                if bool(self.params["verbose"]):
                    print(
                        "%7.4f" % self.env.now
                        + " : %s" % self.identifier
                        + " generated Block %s" % b.identifier
                    )
                self.blockchain.append(b)
                if bool(self.params["verbose"]):
                    self.displayChain()

                """Mark the block creation time"""
                if b.hash not in self.data["blockProp"].keys():
                    self.data["blockProp"][b.hash] = [self.env.now, self.env.now]

                """Broadcast block to all neighbours"""
                broadcast(
                    self.env,
                    b,
                    "Block",
                    self.identifier,
                    self.neighbourList,
                    self.params,
                    pipes=self.pipes,
                    nodes=self.nodes,
                )

                """Remove transactions from local pool"""
                self.transactionPool.popTransaction(transactionCount)
                self.currentBlockID += 1

            except simpy.Interrupt:
                if bool(self.params["verbose"]):
                    print(
                        "%7.4f" % self.env.now
                        + " : "
                        + "%s" % self.identifier
                        + " interrupted. To mine block %s" % (self.currentBlockID + 1)
                        + " now"
                    )
                self.currentBlockID += 1

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
                """Interrupt block generation"""
                self.blockGeneratorAction.interrupt()

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

                """Mark the block receive time"""
                self.data["blockProp"][b.hash][1] = self.env.now

            else:
                """If an invalid block is received, check neighbours and update 
				the chain if a longer chain is found"""
                self.updateBlockchain()
