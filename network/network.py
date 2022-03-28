from time import time
import numpy as np
import random

from nodes.participating_node import ParticipatingNode
from nodes.full_node import FullNode
from network.pipe import Pipe
from utils.spanning_tree import SpanningTree
from utils.helper import assign_next_hop_to_leader


class Network:
    """
    This class models the backbone of the entire blockchain network.
    """

    def __init__(self, name, env, params):
        self.name = name
        self.env = env
        self.params = params
        self.locations = params["locations"]
        self.participating_nodes = []
        self.full_nodes = {}
        self.principal_committee_node_ids = []
        self.shard_nodes = []
        self.pipes = {}
        self.num_nodes = params['num_nodes']
        self.add_participating_nodes(params["num_nodes"])


    def add_participating_nodes(self, num_nodes=20):
        """
        Add the participating nodes - nodes which want to be 
        part of the network (may contain) Sybil identities.
        """

        # node id is serial number as of now
        for id in range(num_nodes):
            location = np.random.choice(self.locations, size=1)[0]
            self.participating_nodes.append(ParticipatingNode(
                id,
                self.env,
                location,
                self.params
            ))
            if bool(self.params["verbose"]) and self.params["verbose"] == "elaborate":
                print(
                    "%7.4f" % self.env.now
                    + " : "
                    + "%s added at location %s"
                    % ("PN%d" % id, location)
                )


    def execute_sybil_resistance_mechanism(self):       # Sybil Resistance: https://en.wikipedia.org/wiki/Sybil_attack
        """
        TODO: Run Proof-of-Stake as a Sybil resistance mechanim
        to filter the participating nodes as full nodes.
        """
        
        # participating_node_ids = list(self.participating_nodes.keys())

        # Dummy mechanism: currently we are choosing nodes at random and converting them to full nodes
        mask = np.random.choice([0, 1], size=(self.num_nodes,), p=[0, 1])

        for idx in range(self.num_nodes):
            curr_participating_node = self.participating_nodes[idx]

            if mask[idx] == 1:
                curr_id = curr_participating_node.id
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
            else:
            # rejected nodes are looged here
                pass


    def run_epoch(self):
        """
        Start executing a fresh epoch
        """

        self.params["network_config_start_time"] = self.env.now
        self.partition_nodes()
        self.establish_network_connections()

        self.params["tx_start_time"] = self.env.now
        self.allow_transactions_generation()
        self.display_network_info()


    def partition_nodes(self):
        """
        Partititon the nodes in the network into principal committee, leaders
        and shard members
        """

        # Add members to the Principal Committee randomly
        nodes = list(self.full_nodes.keys())
        np.random.shuffle(nodes)
        num_principal_committe_nodes = int(len(nodes) * self.params["principal_committee_size"])
        self.principal_committee_node_ids = nodes[0: num_principal_committe_nodes]
        
        # Randomly select the leader of the principal committee
        principal_committee_leader = random.choice(self.principal_committee_node_ids)

        for node_id in self.principal_committee_node_ids:
            self.full_nodes[node_id].node_type = 1
            # self.principal_committee_node[node_id] = self.full_nodes[node_id]
            self.full_nodes[node_id].pc_leader_id = principal_committee_leader
        
        # Allot nodes to different shards
        shard_nodes = nodes[num_principal_committe_nodes:]
        shard_groups = np.array_split(shard_nodes, self.params["num_shards"])
        
        for idx in range(self.params["num_shards"]):
            # Randomly select the shard leader
            shard_leader_id = np.random.choice(shard_groups[idx])
            self.full_nodes[shard_leader_id].node_type = 2

            for node_id in shard_groups[idx]:
                self.full_nodes[node_id].shard_id = idx
                self.full_nodes[node_id].shard_leader_id = shard_leader_id
                if node_id != shard_leader_id:
                    self.full_nodes[node_id].node_type = 3

        self.shard_nodes = [shards.tolist() for shards in shard_groups]
        # for id, node in self.full_nodes.items():
        #     if id not in self.principal_committee_node_ids:
        #         self.shard_nodes[node.shard_id - 1].append(node.id)
       

    def establish_network_connections(self):
        """
        Establish network topology between the full nodes
        """
        """Degree of network graph. Degree >= n/2 guarantees a connected graph"""
        # degree = len(self.principal_committee_node_ids) // 2 + 1

        ################## Connect the Principal Committee nodes ##################
        # keeping the degress as num nodes - 1 to make the pricinpal committee network fully connected
        degree = len(self.principal_committee_node_ids) - 1

        # neighbours info is a dictionary mapping nodes to its neighbours for constructing undirected graph
        neighbours_info = {}

        for id in self.principal_committee_node_ids:
            possible_neighbours = self.principal_committee_node_ids.copy()
            possible_neighbours.remove(id)
            
            neighbours_info[id] = possible_neighbours

            """Generate a random sample of size degree without replacement from possible neighbours"""
            # NOTE - This is a generic code to create bidirectional links among neighbors when graph is not fully connected
            
            # neighbours_list = np.random.choice(
            #     possible_neighbours, 
            #     size=degree, 
            #     replace=False
            # )
            
            # if id not in neighbours_info.keys():
            #     neighbours_info[id] = set()
            
            # for neighbour_id in neighbours_list:
            #     if neighbour_id not in neighbours_info.keys():
            #         neighbours_info[neighbour_id] = set()

            #     neighbours_info[id].add(neighbour_id)
            #     neighbours_info[neighbour_id].add(id)

        for key, value in neighbours_info.items():
            self.full_nodes[key].add_network_parameters(self.full_nodes, list(value))
    
        ################## Connect the leaders of the shards with the Principal Committee ##################
        degree = len(self.principal_committee_node_ids) // 2 + 1
        for idx in range(len(self.shard_nodes)):
            curr_leader = self.get_shard_leader(idx)
            possible_neighbours = self.principal_committee_node_ids
            
            neighbours_list = np.random.choice(
                possible_neighbours, size=degree, replace=False
            )

            curr_leader.add_network_parameters(self.full_nodes, neighbours_list)
            
            # Add back connections to the principal committee neighbours
            for id in neighbours_list:
                self.full_nodes[id].neighbours_ids.append(curr_leader.id)

        ################## Connect the shard nodes with each other and the leaders ##################
        for idx in range(len(self.shard_nodes)):
            curr_shard_nodes = {}
            for node_id in self.shard_nodes[idx]:
                curr_shard_nodes[node_id] = self.full_nodes[node_id]

            neighbours_info = {}
            degree = len(self.shard_nodes[idx]) // 2 + 1

            for curr_node_id in self.shard_nodes[idx]:
                possible_neighbours = self.shard_nodes[idx].copy()
                possible_neighbours.remove(curr_node_id)
            
                neighbours_list = np.random.choice(
                    possible_neighbours, size=degree, replace=False
                )

                if curr_node_id not in neighbours_info.keys():
                    neighbours_info[curr_node_id] = set()
                
                for neighbour_id in neighbours_list:
                    if neighbour_id not in neighbours_info.keys():
                        neighbours_info[neighbour_id] = set()

                    neighbours_info[curr_node_id].add(neighbour_id)
                    neighbours_info[neighbour_id].add(curr_node_id)
                
                self.full_nodes[curr_node_id].shard_leader = self.get_shard_leader(idx)
            
            principal_committee_neigbours = []
            for key, value in neighbours_info.items():
                if self.full_nodes[key].node_type == 2:
                    # If curr_node is a leader, append to the neighbors list
                    principal_committee_neigbours = self.full_nodes[key].neighbours_ids
                    self.full_nodes[key].update_neighbours(list(value))
                else:
                    self.full_nodes[key].add_network_parameters(curr_shard_nodes, list(value))
            
            # Create a Spanning Tree for the broadcast for the shard nodes
            spanning_tree = SpanningTree(curr_shard_nodes)
            neighbours_info = spanning_tree.Kruskal_MST()
            
            # Make edges bi-directional
            for id, neighbours in neighbours_info.items():
                for neighbour_id in list(neighbours):
                    neighbours_info[neighbour_id].add(id)

            # Update the neighbours
            for key, value in neighbours_info.items():
                # print(f"{key} -- {self.full_nodes[key].neighbours_ids}")
                value = list(value)
                if self.full_nodes[key].node_type == 2:
                    value += list(principal_committee_neigbours)
                self.full_nodes[key].update_neighbours(value)
            
            # Assign next_hop to reach the leader
            assign_next_hop_to_leader(curr_shard_nodes, self.get_shard_leader(idx))
            # for id, node in curr_shard_nodes.items():
            #     print(f"{id} = {node.next_hop_id}")


        """
        Cross-shard Transactions -
            Connect shard leaders with each other
        """
        num_leaders = len(self.shard_nodes)
        leaders_id_list = []
        for id in range(num_leaders):
            leaders_id_list.append(self.get_shard_leader(id).id)
        
        neighbours_info = {}
        degree = num_leaders // 2 + 1
        for id in leaders_id_list:
            possible_neighbours = leaders_id_list.copy()
            possible_neighbours.remove(id) 

            if id not in neighbours_info.keys():
                neighbours_info[id] = set()            
            
            neighbours_list = np.random.choice(
                possible_neighbours, 
                size=degree, 
                replace=False
            )
                
            for neighbour_id in neighbours_list:
                if neighbour_id not in neighbours_info.keys():
                    neighbours_info[neighbour_id] = set()
                
                neighbours_info[id].add(neighbour_id)
                neighbours_info[neighbour_id].add(id)
        
        leader_nodes = {id: self.full_nodes[id] for id in leaders_id_list}
        
        for id in leaders_id_list:
            self.full_nodes[id].init_shard_leaders(leader_nodes)
            self.full_nodes[id].neighbours_ids += (list(neighbours_info[id]))
            
        


    def get_shard_leader(self, idx):
        """
        Return leader of the specified shard
        """
        return self.full_nodes[self.full_nodes[self.shard_nodes[idx][0]].shard_leader_id]
        # leader = [idx for idx in self.shard_nodes[idx] if self.full_nodes[idx].node_type == 2]
        # if len(leader_id) != 1:
        #     raise RuntimeError("More than 1 leader for the Shard - %d" %idx)
        
        # return self.full_nodes[leader[0]]


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
        print("Principal Committee Nodes -", self.principal_committee_node_ids)
        print(f"Leader = '{self.full_nodes[self.principal_committee_node_ids[0]].pc_leader_id}'")

        for id in self.principal_committee_node_ids:
            print(f"{id} has neighbors - {self.full_nodes[id].neighbours_ids}")
        print("\n")

        for i in range(self.params["num_shards"]):
            print("\t\t\t\tSHARD -", i+1)
            print("Nodes -", self.shard_nodes[i])  
            print(f"Leader - '{self.get_shard_leader(i).id}'\n")
            
            for j in range(len(self.shard_nodes[i])):
                curr_node = self.full_nodes[self.shard_nodes[i][j]]
                print(f"{j+1}. {curr_node.id} has neighbours - {curr_node.neighbours_ids} and next hop to leader is '{curr_node.next_hop_id}'")
            print("\n")