from time import time
import numpy as np

from nodes.participating_node import ParticipatingNode
from nodes.full_node import FullNode


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
            if bool(self.params["verbose"]) and self.params["verbose"] == "elaborate":
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
        
        participating_node_ids = list(self.participating_nodes.keys())
        num_nodes = len(self.participating_nodes)
        # Dummy mechanism
        mask = np.random.choice([0, 1], size=(num_nodes,), p=[1./3, 2./3])

        for idx in range(num_nodes):
            curr_participating_node = self.participating_nodes[participating_node_ids[idx]]

            if mask[idx] == 1:
                curr_id = int(curr_participating_node.id[2:])
                self.full_nodes["FN%d" % curr_id] = FullNode(
                    "FN%d" % curr_id,
                    curr_participating_node.env,
                    curr_participating_node.location,
                    curr_participating_node.params
                )

                if bool(self.params["verbose"]):
                    print(
                        "%7.4f" % time() # self.env.now
                        + " : "
                        + "%s entered the network from location %s"
                        % ("FN%d" % curr_id, curr_participating_node.location)
                    )

    def run_epoch(self):
        """
        Start executing a fresh epoch
        """
        self.partition_nodes()
        self.display_network_info()

    def partition_nodes(self):
        """
        Partititon the nodes in the network into principal committee, leaders
        and shard members
        """

        # Add members to the Principal Committee randomly
        nodes = np.asarray(list(self.full_nodes.keys()))
        np.random.shuffle(nodes)
        num_principal_committe_nodes = int(len(nodes) * self.params["principal_committee_size"])
        principal_committee_nodes = nodes[0: num_principal_committe_nodes]

        for node_id in principal_committee_nodes:
            self.full_nodes[node_id].node_type = 1

        # Allot nodes to different shards
        shard_nodes = nodes[num_principal_committe_nodes:]
        shard_groups = np.array_split(shard_nodes, self.params["num_shards"])

        for idx in range(self.params["num_shards"]):
            for node_id in shard_groups[idx]:
                self.full_nodes[node_id].shard_id = idx
                self.full_nodes[node_id].node_type = 3
            
            # Assign a leader randomly
            self.full_nodes[np.random.choice(shard_groups[idx])].node_type = 2

    def display_network_info(self):
        principal_committee_nodes = [node.id for _, node in self.full_nodes.items() if node.node_type == 1]
    
        shard_nodes = [[] for i in range(self.params["num_shards"])]
        for _, node in self.full_nodes.items():
            shard_nodes[node.shard_id - 1].append(node.id)
        
        print("\n============  NETWORK INFORMATION  ============")
        print("Principal Committee Nodes -", principal_committee_nodes, "\n\n")

        for i in range(self.params["num_shards"]):
            print("\t\t\t\tSHARD -", i+1)
            print("Nodes -", shard_nodes[i])
            print("Leader -", [i for i in shard_nodes[i] if self.full_nodes[i].node_type == 2])
            print("\n")