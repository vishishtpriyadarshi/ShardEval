from time import time
import numpy as np

from nodes.participating_node import ParticipatingNode
from nodes.full_node import FullNode
from network.pipe import Pipe


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
        self.principal_committee_nodes = {}
        self.shard_nodes = []
        self.pipes = {}

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
                    "%7.4f" % self.env.now
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
                        "%7.4f" % self.env.now
                        + " : "
                        + "%s entered the network from location %s"
                        % ("FN%d" % curr_id, curr_participating_node.location)
                    )


    def run_epoch(self):
        """
        Start executing a fresh epoch
        """
        self.partition_nodes()
        self.establish_network_connections()
        self.allow_transactions_generation()
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
            self.principal_committee_nodes[node_id] = self.full_nodes[node_id]

        # Allot nodes to different shards
        shard_nodes = nodes[num_principal_committe_nodes:]
        shard_groups = np.array_split(shard_nodes, self.params["num_shards"])

        for idx in range(self.params["num_shards"]):
            for node_id in shard_groups[idx]:
                self.full_nodes[node_id].shard_id = idx
                self.full_nodes[node_id].node_type = 3
            
            # Assign a leader randomly
            self.full_nodes[np.random.choice(shard_groups[idx])].node_type = 2

        self.shard_nodes = [[] for i in range(self.params["num_shards"])]
        for id, node in self.full_nodes.items():
            if id not in self.principal_committee_nodes:
                self.shard_nodes[node.shard_id - 1].append(node.id)
       

    def establish_network_connections(self):
        """
        Establish network topology between the full nodes
        """

        # Connect the Principal Committee nodes
        """Degree of network graph. Degree >= n/2 guarantees a connected graph"""
        degree = len(self.principal_committee_nodes) // 2 + 1

        # neighbours info is a dictionary mapping nodes to its neighbours for constructing undirected graph
        neighbours_info = {}

        for id, node in self.principal_committee_nodes.items():
            possible_neighbours = list(self.principal_committee_nodes.keys())
            possible_neighbours.remove(id)
            
            """Generate a random sample of size degree without replacement from possible neighbours"""
            neighbours_list = np.random.choice(
                possible_neighbours, size=degree, replace=False
            )
            
            if id not in neighbours_info.keys():
                neighbours_info[id] = set()
            
            for neighbour_id in neighbours_list:
                if neighbour_id not in neighbours_info.keys():
                    neighbours_info[neighbour_id] = set()

                neighbours_info[id].add(neighbour_id)
                neighbours_info[neighbour_id].add(id)

        for key, value in neighbours_info.items():
            self.full_nodes[key].add_network_parameters(self.full_nodes, list(value))
    
        # Connect the leaders of the shards with the Principal Committee
        for idx in range(len(self.shard_nodes)):
            curr_leader = self.get_shard_leader(idx)
            possible_neighbours = list(self.principal_committee_nodes.keys())
            
            neighbours_list = np.random.choice(
                possible_neighbours, size=degree, replace=False
            )

            curr_leader.add_network_parameters(self.full_nodes, neighbours_list)

        # Connect the shard nodes with each other and the leaders
        for idx in range(len(self.shard_nodes)):
            curr_shard_nodes = {}
            for node_id in self.shard_nodes[idx]:
                curr_shard_nodes[node_id] = self.full_nodes[node_id]

            neighbours_info = {}
            for curr_node_id in self.shard_nodes[idx]:
                possible_neighbours = self.shard_nodes[idx].copy()
                possible_neighbours.remove(curr_node_id)
            
                neighbours_list = np.random.choice(
                    possible_neighbours, size=degree, replace=False
                )

                print(f"{curr_node_id} - {neighbours_list}")

                if curr_node_id not in neighbours_info.keys():
                    neighbours_info[curr_node_id] = set()
                
                for neighbour_id in neighbours_list:
                    if neighbour_id not in neighbours_info.keys():
                        neighbours_info[neighbour_id] = set()

                    neighbours_info[curr_node_id].add(neighbour_id)
                    neighbours_info[neighbour_id].add(curr_node_id)
                
                self.full_nodes[curr_node_id].shard_leader =  self.get_shard_leader(idx)
            
            for key, value in neighbours_info.items():
                if self.full_nodes[key].node_type == 2:
                    # If curr_node is a leader, append to the neighbors list
                    self.full_nodes[key].neighbours_ids = np.append(self.full_nodes[key].neighbours_ids,
                                                                    list(value))
                else:
                    self.full_nodes[key].add_network_parameters(curr_shard_nodes, list(value))


    def get_shard_leader(self, idx):
        """
        Return leader of the specified shard
        """
        leader = [idx for idx in self.shard_nodes[idx] if self.full_nodes[idx].node_type == 2]
        if len(leader) != 1:
            raise RuntimeError("More than 1 leader for the Shard - %d" %idx)
        
        return self.full_nodes[leader[0]]


    def allow_transactions_generation(self):
        """
        Prompt each shard node to generate and broadcast the transactions
        """
        for idx in range(len(self.shard_nodes)):
            for node_id in self.shard_nodes[idx]:
                curr_node = self.full_nodes[node_id]

                if curr_node.node_type == 2:
                    curr_node.env.process(curr_node.preprocess_transactions())
                    continue
                
                curr_node.env.process(curr_node.generate_transactions())
                

    def display_network_info(self):
        print("\n============  NETWORK INFORMATION  ============")
        print("Principal Committee Nodes -", list(self.principal_committee_nodes.keys()))
        
        for id, node in self.principal_committee_nodes.items():
            print("{} has neighbors -".format(id), end=' ')
            print(node.neighbours_ids)
        print("\n")

        for i in range(self.params["num_shards"]):
            print("\t\t\t\tSHARD -", i+1)            
            print("Leader -", [l for l in self.shard_nodes[i] if self.full_nodes[l].node_type == 2])

            print("Nodes -", self.shard_nodes[i], "\n")
            for j in range(len(self.shard_nodes[i])):
                print("{}. {} has neighbours -".format(j+1, self.shard_nodes[i][j]), end=' ') 
                print(self.full_nodes[self.shard_nodes[i][j]].neighbours_ids, end='\n')
            print("\n")