class ParticipatingNode:
    """This class models the real-world nodes which intend to
    take part in the Blockchain."""

    def __init__(self, id, env, network_nodes, neighbours_ids, location, params):
        self.id = id
        self.env = env 
        self.network_nodes = network_nodes
        self.neighbours_ids = neighbours_ids
        self.location = location
        self.params = params