import numpy as np

from network.broadcast import broadcast
from factory.transaction import Transaction
from utils.helper import get_transmission_delay
from utils.priority_queue import PriorityQueue


class TransactionPool:
    """
    Transaction pool for a full node
    """

    def __init__(self, env, id, neighbours_ids, nodes, params):
        self.env = env
        self.id = id
        self.neighbours_ids = neighbours_ids
        self.params = params
        self.nodes = nodes
        self.transaction_queue = PriorityQueue()
        self.prev_transactions = []


    def get_transaction(self, transaction_count):
        """
        Return transaction_count number of Transactions. 
        Returns top transactions based on tx reward.
        """
        return self.transaction_queue.get(transaction_count)


    def pop_transaction(self, transaction_count):
        """
        Remove transactions from transaction pool. 
        Called when transactions are added by a received block or a block is mined.
        """
        popped_transactions = self.transaction_queue.pop(transaction_count)
        self.prev_transactions.append(popped_transactions)


    def put_transaction(self, transaction, source_location):
        """
        Add received transaction to the transaction pool and broadcast further
        """
        dest_location = self.nodes[self.id].location
        delay = get_transmission_delay(source_location, dest_location)

        yield self.env.timeout(delay)
        if (
            not self.transaction_queue.is_present(transaction)
            and transaction not in self.prev_transactions
        ):
            self.transaction_queue.insert(transaction)
            broadcast(self.env, transaction, "Tx", self.id, self.neighbours_ids, self.nodes, self.params)
            
            if self.params["verbose"] == "Elaborate":
                print(
                    "%7.4f : %s accepted by %s"
                    % (self.env.now, transaction.id, self.id)
                )
            
            curr_node = self.nodes[self.id]
            # if curr_node.node_type == 2:
            #     print(f"Leader of the shard {curr_node.shard_id} is {self.id} and has {self.transaction_queue.length()} transactions")