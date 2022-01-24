class ParticipatingNode:
    """This class models the real-world nodes which intend to
    take part in the Blockchain."""

    def __init__(self, id, env, location, params):
        self.id = id
        self.env = env 
        self.location = location
        self.params = params