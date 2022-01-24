from time import time
import numpy as np

from nodes.participating_node import ParticipatingNode


class Network:
    """
    This class models the backbone of the entire blockchain network.
    """

    def __init__(self, name, env, params):
        self.name = name
        self.env = env
        self.params = params
        self.locations = params["locations"]
        self.participating_nodes = {}
        self.full_nodes = {}

        self.add_participating_nodes(params["num_nodes"])

    def add_participating_nodes(self, num_nodes=20):
        """
        Add the participating nodes - nodes which want to be 
        part of the network (may contain) Sybil identities.
        """

        for id in range(num_nodes):
            location = np.random.choice(self.locations, size=1)[0]
            self.participating_nodes["PN%d" % id] = ParticipatingNode(
                "PN%d" % id,
                self.env,
                location,
                self.params
            )
            if bool(self.params["verbose"]):
                print(
                    "%7.4f" % time() # self.env.now
                    + " : "
                    + "%s added at location %s"
                    % ("PN%d" % id, location)
                )

    def execute_sybil_resistance_mechanism(self):
        """
        Run Proof-of-Stake as a Sybil resistance mechanim
        to filter the participating nodes as full nodes.
        """
        pass