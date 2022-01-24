"""
To-Do:
1. Add reputation and necessary code for the Proof-of-Stake
"""

from nodes.participating_node import ParticipatingNode

class FullNode(ParticipatingNode):
    """This class models the nodes which will take part in the Blockchain.
    These nodes are the subsets of the participating nodes."""

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

    def add_network_parameters(self, network_nodes, neighbours_ids):
        self.network_nodes = network_nodes
        self.neighbours_ids = neighbours_ids
    
    def cast_vote(self):
        pass

    def validate_transactions(self):
        pass

    def receive_block(self):
        pass

    def update_blockchain(self):
        pass