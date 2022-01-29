"""
To-Do:
1. Add reputation and necessary code for the Proof-of-Stake
"""

import numpy as np
import random

from nodes.participating_node import ParticipatingNode
from network.broadcast import broadcast
from network.mini_block import MiniBlock
from network.tx_block import TxBlock
from network.pipe import Pipe
from transaction_factory.transaction import Transaction
from transaction_factory.transaction_pool import TransactionPool
from utils import get_transaction_delay, is_voting_complete, get_shard_neighbours, get_principal_committee_neigbours, is_vote_casted


class FullNode(ParticipatingNode):
    """
    This class models the nodes which will take part in the Blockchain.
    These nodes are the subsets of the participating nodes.
    """

    def __init__(self, id, env, location, params):
        super().__init__(id, env, location, params)

        self.node_type = 0
        # 0 - Node is in between re-configuration (slot)
        # 1 - Principal Committee
        # 2 - Shard Leader
        # 3 - Shard Member
        
        self.shard_id = -1
        self.shard_leader = None
        self.curr_shard_nodes = {}
        self.neighbours_ids = []


    def add_network_parameters(self, curr_shard_nodes, neighbours_ids):
        self.curr_shard_nodes = curr_shard_nodes
        self.neighbours_ids = neighbours_ids
        self.transaction_pool = TransactionPool(
            self.env, self.id, neighbours_ids, curr_shard_nodes, self.params
        )
        self.pipes = Pipe(self.env, self.id, self.curr_shard_nodes)
        self.env.process(self.receive_block())
    

    def generate_transactions(self):
        """
        Generates transactions in the shard and broadcasts it to the neighbour nodes
        """

        # To-Do: Don't allow generation of transactions during shard re-configuration

        if self.node_type != 3:
            raise RuntimeError("Node not allowed to generate transactions.")

        num = 0
        while True:
            delay = get_transaction_delay(
                self.params["transaction_mu"], self.params["transaction_sigma"]
            )
            yield self.env.timeout(delay)
            
            value = np.random.randint(self.params["tx_value_low"], self.params["tx_value_high"])
            reward = value * self.params["reward_percentage"]

            transaction_state = {}
            for key, value in self.curr_shard_nodes.items():
                transaction_state[key] = 0

            transaction = Transaction("T_%s_%d" % (self.id, num), self.env.now, value, reward, transaction_state)
            # self.data["numTransactions"] += 1
            
            if self.params["verbose"]:
                print(
                    "%7.4f" % self.env.now
                    + " : "
                    + "%s added with reward %.2f"
                    % (transaction.id, transaction.reward)
                )

            # [WIP]: Rough Broadcast to all the neighbors
            broadcast(
                self.env, 
                transaction, 
                "Tx", 
                self.id, 
                self.neighbours_ids, 
                self.curr_shard_nodes, 
                self.params
            )

            num += 1

    
    def preprocess_transactions(self):
        """
        Pre-processes the transactions (done by shard leader)
        """
        if self.node_type != 2:
            raise RuntimeError("Pre-processing can only be performed by the shard leader")

        while True:
            delay = get_transaction_delay(
                self.params["transaction_mu"], self.params["transaction_sigma"]
            )
            yield self.env.timeout(delay)

            if self.transaction_pool.transaction_queue.length() >= self.params["mini_block_capacity"]:
                transactions_list = self.transaction_pool.transaction_queue.pop(self.params["mini_block_capacity"])

                # To-do: Add pre-processing step
                delay = get_transaction_delay(
                    self.params["transaction_mu"], self.params["transaction_sigma"]
                )
                yield self.env.timeout(delay)
                
                shard_neigbours = get_shard_neighbours(self.curr_shard_nodes, self.neighbours_ids, self.shard_id)

                # To-do: Clean this piece of code for filtered_curr_shard_nodes
                filtered_curr_shard_nodes = []
                for node_id in self.curr_shard_nodes.keys():
                    if self.curr_shard_nodes[node_id].shard_id == self.shard_id and self.curr_shard_nodes[node_id].node_type == 3:
                        filtered_curr_shard_nodes.append(node_id)

                # print("[Neighbours]:", shard_neigbours)
                tx_block = TxBlock(f"TB_{self.id}", transactions_list, self.params, self.shard_id, filtered_curr_shard_nodes)

                broadcast(
                    self.env, 
                    tx_block, 
                    "Tx-block", 
                    self.id, 
                    shard_neigbours, 
                    self.curr_shard_nodes, 
                    self.params
                )


    def generate_mini_block(self, tx_block):
        """
        Generate a mini block and broadcast it to the shard nodes
        """
        if self.node_type != 2:
            raise RuntimeError("Mini-block can only be generated by the shard leader")

        # To-Do: Filter transactions from tx_block based on votes
        accepted_transactions = tx_block.transactions_list
        
        mini_block = MiniBlock(f"MB_{self.id}", accepted_transactions, self.params, self.shard_id)
        principal_committee_neigbours = get_principal_committee_neigbours(self.curr_shard_nodes, self.neighbours_ids)
        
        broadcast(
            self.env, 
            mini_block,
            "Mini-block", 
            self.id, 
            principal_committee_neigbours, 
            self.curr_shard_nodes, 
            self.params
        )


    def generate_block(self):
        """
        Generate a block and broadcast it in the entire network
        """
        if self.node_type != 1:
            raise RuntimeError("Block can only be generated by the Principal Committee")


    def validate_transaction(self, tx):
        """
        Validate transaction
        """
        # To-do: Think on improving it
        return bool(random.getrandbits(1))


    def cast_vote(self, tx_block):
        """
        Cast votes on each tx in tx_block
        """
        for tx in tx_block.transactions_list:
            tx_block.votes_status[tx.id][self.id] = self.validate_transaction(tx)
    

    def process_received_tx_block(self, tx_block):
        """
        Handle the received Tx-block
        """
        if self.shard_id != tx_block.shard_id:
            raise RuntimeError("Tx-block received by other shard node.")

        if self.node_type == 0:
            raise RuntimeError("Tx-block received in between re-configuration.")
            # To-do: Complete when dealing with nodes re-configuration (new epoch)
        
        if self.node_type == 1:
            raise RuntimeError("Tx-block received by Principal Committee node.")
        
        flag = is_voting_complete(tx_block)
        # print("[Debug]:", flag)
        shard_neigbours = get_shard_neighbours(
            self.curr_shard_nodes, self.neighbours_ids, self.shard_id
        )

        if self.node_type == 2:
            if self.id not in tx_block.visitor_count_post_voting.keys():
                tx_block.visitor_count_post_voting[self.id] = 1
                if flag:
                    if self.params["verbose"]:
                        print(
                            "%7.4f" % self.env.now
                            + " : "
                            + "Node %s (Leader) received voted Tx-block %s" % (self.id, tx_block.id)
                        )
                    self.generate_mini_block(tx_block)

        elif self.node_type == 3:
            if flag:
                if self.id not in tx_block.visitor_count_post_voting.keys():
                    tx_block.visitor_count_post_voting[self.id] = 1
                    if self.params["verbose"]:
                        print(
                            "%7.4f" % self.env.now
                            + " : "
                            + "Node %s (shard node) propagated voted Tx-block %s" % (self.id, tx_block.id)
                        )

                    broadcast(
                        self.env, 
                        tx_block, 
                        "Tx-block", 
                        self.id, 
                        shard_neigbours, 
                        self.curr_shard_nodes, 
                        self.params
                    )
            else:
                if is_vote_casted(tx_block, self.id) == False:
                    self.cast_vote(tx_block)
                    if self.params["verbose"]:
                        print(
                            "%7.4f" % self.env.now
                            + " : "
                            + "Node %s voted and for the Tx-block %s" % (self.id, tx_block.id)
                        )

                    print("[Neighbours]:", shard_neigbours)
                    broadcast(
                        self.env, 
                        tx_block, 
                        "Tx-block", 
                        self.id, 
                        shard_neigbours, 
                        self.curr_shard_nodes, 
                        self.params
                    )
            

    def receive_block(self):
        """
        Receive Tx-block sent by the shard leader, or
        (final) Block sent by the Principal Committee
        """
        while True:
            block = yield self.pipes.get()
            block_type = ""

            # if self.id == "FN1":
            #     print("[Node Debug]: FN1 here")

            if isinstance(block, TxBlock):
                self.process_received_tx_block(block)
                block_type = "Tx"
            elif isinstance(block, MiniBlock):
                pass
                block_type = "Final"
            else:
                raise RuntimeError("Unknown Block received")
            
            if self.params["verbose"]:
                print(
                    "%7.4f" % self.env.now
                    + " : "
                    + "%s received a %s-block"
                    % (self.id, block_type)
                )


    def update_blockchain(self):
        pass