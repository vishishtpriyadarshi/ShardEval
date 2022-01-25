"""
To-Do:
1. Add reputation and necessary code for the Proof-of-Stake
"""

import numpy as np

from nodes.participating_node import ParticipatingNode
from network.pipe import Pipe
from transaction_factory.transaction import Transaction
from utils import get_transaction_delay


class FullNode(ParticipatingNode):
    """
    This class models the nodes which will take part in the Blockchain.
    These nodes are the subsets of the participating nodes.
    """

    def __init__(self, id, env, location, params):
        super().__init__(id, env, location, params)
        self.node_type = 3
        # 0 - Node is in between re-configuration (slot)
        # 1 - Principal Committee
        # 2 - Shard Leader
        # 3 - Shard Member
        
        self.shard_id = -1
        self.network_nodes = {}
        self.neighbours_ids = []
        self.env.process(self.generate_transactions())

    def add_network_parameters(self, network_nodes, neighbours_ids):
        self.network_nodes = network_nodes
        self.neighbours_ids = neighbours_ids
    
    def generate_transactions(self):
        """
        Generates transactions in the shard and broadcasts it to the neighbour nodes
        """
        num = 0
        while True:
            delay = get_transaction_delay(
                self.params["transaction_mu"], self.params["transaction_sigma"]
            )
            yield self.env.timeout(delay)

            value = np.random.randint(self.params["tx_value_low"], self.params["tx_value_high"])
            reward = value * self.params["reward_percentage"]

            transaction = Transaction("T_%s_%d" % (self.id, num), self.env.now, value, reward)
            # self.data["numTransactions"] += 1
            
            if self.params["verbose"]:
                print(
                    "%7.4f" % self.env.now
                    + " : "
                    + "%s added with reward %.2f"
                    % (transaction.id, transaction.reward)
                )

            # To-Do: Broadcast transactions to all neighbours
            
            num += 1

    def cast_vote(self):
        pass

    def validate_transactions(self):
        pass

    def receive_block(self):
        pass

    def update_blockchain(self):
        pass