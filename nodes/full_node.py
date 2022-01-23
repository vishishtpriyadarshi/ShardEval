"""
To-Do:
1. Add reputation and necessary code for the Proof-of-Stake
"""

from nodes.participating_nodes import ParticipatingNode

class FullNode(ParticipatingNode):
    """This class models the nodes which will take part in the Blockchain.
    These nodes are the subsets of the participating nodes."""

    def __init__(self, id, env, network_nodes, neighbours_ids, location, params):
        super().__init__(self, id, env, network_nodes, neighbours_ids, location, params)
        self.node_type = 3
        # 0 - Node is in between re-configuration (slot)
        # 1 - Principal Committee
        # 2 - Shard Leader
        # 3 - Shard Member
        

    def cast_vote:
        pass

    def validate_transactions:
        pass

    def receive_block:
        pass

    def update_blockchain:
        pass