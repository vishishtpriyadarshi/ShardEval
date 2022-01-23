import numpy as np
from network.broadcast import broadcast
from transaction_factory.transaction import Transaction
from utils import get_transmission_delay, PriorityQueue


class TransactionPool:
    """Transaction pool for a miner"""

    def __init__(self, env, identifier, neighbourList, nodes, params):
        self.env = env
        self.identifier = identifier
        self.neighbourList = neighbourList
        self.params = params
        self.nodes = nodes
        self.transactionQueue = PriorityQueue()
        self.prevTransactions = []

    def getTransaction(self, transactionCount):
        """Returns transactionCount number of Transactions. Returns
		 top transactions based on miner reward"""
        return self.transactionQueue.get(transactionCount)

    def popTransaction(self, transactionCount):
        """Remove transactions from transaction pool. Called when transactions 
		are added by a received block or a block is mined."""
        poppedTransactions = self.transactionQueue.pop(transactionCount)
        self.prevTransactions.append(poppedTransactions)

    def putTransaction(self, transaction, sourceLocation):
        """Add received transaction to the transaction pool and broadcast further"""
        destLocation = self.nodes[self.identifier].location
        delay = get_transmission_delay(sourceLocation, destLocation)
        yield self.env.timeout(delay)
        if (
            not self.transactionQueue.isPresent(transaction)
            and transaction not in self.prevTransactions
        ):
            self.transactionQueue.insert(transaction)
            broadcast(
                self.env,
                transaction,
                "Transaction",
                self.identifier,
                self.neighbourList,
                self.params,
                nodes=self.nodes,
            )
            if self.params["verbose"] == "vv":
                print(
                    "%7.4f : %s accepted by %s"
                    % (self.env.now, transaction.identifier, self.identifier)
                )

