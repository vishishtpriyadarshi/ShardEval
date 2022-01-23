from playground.participating_nodes import ParticipatingNode

class FullNode(ParticipatingNode):
    """This class models the nodes which will take part in the Blockchain.
    These nodes are the subsets of the participating nodes."""

    def __init__(self, id, env, network_nodes, neighbours_ids, location, params):
        super().__init__(self, id, env, network_nodes, neighbours_ids, location, params)