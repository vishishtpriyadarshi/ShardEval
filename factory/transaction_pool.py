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
        self.intra_shard_tx_queue = PriorityQueue()
        self.cross_shard_tx_queue = PriorityQueue()
        self.prev_transactions = []
        self.intra_shard_tx = []
        self.cross_shard_tx = []


    def get_transaction(self, transaction_count, tx_type):
        """
        Return transaction_count number of Transactions. 
        Returns top transactions based on tx reward.
        """
        if tx_type == 'intra-shard':
            return self.intra_shard_tx_queue.get(transaction_count)
        elif tx_type == 'cross-shard':
            return self.cross_shard_tx_queue.get(transaction_count)
        else:
            raise RuntimeError("Unknown transaction type specified")


    def pop_transaction(self, transaction_count, tx_type):
        """
        Remove transactions from transaction pool. 
        Called when transactions are added by a received block or a block is mined.
        """
        popped_transactions = None
        if tx_type == 'intra-shard':
            popped_transactions = self.intra_shard_tx_queue.pop(transaction_count)
        elif tx_type == 'cross-shard':
            popped_transactions = self.cross_shard_tx_queue.pop(transaction_count)
        else:
            raise RuntimeError("Unknown transaction type specified")

        self.prev_transactions.append(popped_transactions)
        return popped_transactions


    def put_transaction(self, transaction, source_location, tx_type):
        """
        Add received transaction to the transaction pool and broadcast further
        """
        if not tx_type == 'intra-shard' and not tx_type == 'cross-shard':
            raise RuntimeError("Unknown transaction type specified")

        dest_location = self.nodes[self.id].location
        delay = get_transmission_delay(source_location, dest_location)

        curr_queue = self.intra_shard_tx_queue if tx_type == 'intra-shard' else self.cross_shard_tx_queue
        yield self.env.timeout(delay)
        if (
            not curr_queue.is_present(transaction)
            and transaction not in self.prev_transactions
        ):
            curr_queue.insert(transaction)

            curr_node = self.nodes[self.id]
            neighbour_ids = [self.id if curr_node.next_hop_id == -1 else curr_node.next_hop_id]
            broadcast(self.env, transaction, "Tx", self.id, neighbour_ids, self.nodes, self.params)
            
            if self.params["verbose"]:
                print(
                    "%7.4f : %s accepted by %s"
                    % (self.env.now, transaction.id, self.id)
                )
            
            curr_node = self.nodes[self.id]
            # if curr_node.node_type == 2:
            #     print(f"Leader of the shard {curr_node.shard_id} is {self.id} and has {self.transaction_queue.length()} transactions")