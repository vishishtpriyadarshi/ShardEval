import numpy as np
import random
import functools
import operator

from nodes.participating_node import ParticipatingNode
from network.broadcast import broadcast
from network.mini_block import MiniBlock
from network.tx_block import TxBlock
from network.block import Block
from network.pipe import Pipe
from factory.transaction import Transaction
from factory.transaction_pool import TransactionPool
from network.consensus.consensus import Consensus
from utils import get_transaction_delay, is_voting_complete, get_shard_neighbours, \
     get_principal_committee_neigbours, is_vote_casted, can_generate_block, has_received_mini_block


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
        self.blockchain = []

        # Handled by only principal committee
        self.mini_block_consensus_pool = {}
        self.processed_mini_blocks = []
        self.processed_tx_blocks = []
        self.current_tx_blocks = []


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

            id = int(1000*round(self.env.now, 3))
            transaction = Transaction(f"T_{self.id}_{id}", self.env.now, value, reward, transaction_state)
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

                id = int(1000*round(self.env.now, 3))
                tx_block = TxBlock(f"TB_{self.id}_{id}", transactions_list, self.params, self.shard_id, filtered_curr_shard_nodes)

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
        Generate a mini block and broadcast it to the principal committee
        """
        if self.node_type != 2:
            raise RuntimeError("Mini-block can only be generated by the shard leader")

        self.current_tx_blocks.append(tx_block)
        # print(f"[Debug len]: processed_tx_blocks = {len(self.processed_tx_blocks)}")

        if len(self.current_tx_blocks) == 4:
            # To-Do: Maintain already processed tx-blocks list
            self.processed_tx_blocks += self.current_tx_blocks
            self.current_tx_blocks = []

            # To-Do: Filter transactions from tx_block based on votes
            accepted_transactions = tx_block.transactions_list
            
            id = int(1000*round(self.env.now, 3))
            mini_block = MiniBlock(f"MB_{self.id}_{id}", accepted_transactions, self.params, self.shard_id)
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
        
        # Generate block only when each shard has provided with a mini-block and other principal committee nodes 
        # have voted on it

        # Considering each principal committee node is connected to all other nodes
        size_principal_committee = 1 + len(get_principal_committee_neigbours(self.curr_shard_nodes, self.neighbours_ids))
        # print(f"len = {size_principal_committee}")
        
        if can_generate_block(self.mini_block_consensus_pool, size_principal_committee, self.params["num_shards"]):
            """
            Steps - 

            1. Apply filter on mini-blocks and collect transactions from valid mini-blocks
               a. Take only latest mini-block from each shard
               b. Modify state of the mini_block_consensus_pool
            2. Update own blockchain
            3. Broadcast the block to the shards (To-do: neighbors may have to debug)
            """
            if self.params["verbose"]:
                print(f"[Debug] - Node {self.id} ready to generate \nPool - {self.mini_block_consensus_pool}")

            self.processed_mini_blocks = [ id for id in self.mini_block_consensus_pool ]
            filtered_mini_blocks = []
            temp_data = {}              # stores latest accepted mini-block corresponding to evey shard
            for key, val in self.mini_block_consensus_pool.items():
                block = val["data"]
                net_vote = 0
                for id, curr_vote in val["votes"].items():
                    net_vote += curr_vote if curr_vote else -1
                
                if net_vote > 0:
                    if block.shard_id in temp_data:
                        existing_block = temp_data[block.shard_id]

                        # Select only latest mini-block sent by a shard
                        if int(block[block.rfind('_')+1:]) > int(existing_block[existing_block.rfind('_')+1:]):
                            block = existing_block
                        
                    temp_data[block.shard_id] = block
                    filtered_mini_blocks.append(block)
            
            # To-do: Add mini-blocks data to the consensus_pool before next statement gets executed
            accepted_transactions = [ mini_block.transactions_list for mini_block in filtered_mini_blocks ]

            # Flatten to a flat list
            accepted_transactions = functools.reduce(operator.iconcat, accepted_transactions, [])
            
            id = int(1000*round(self.env.now, 3))
            block = Block(f"B_{self.id}_{id}", accepted_transactions, self.params)
            
            # Update consensus_pool
            temp_dict = self.mini_block_consensus_pool
            self.mini_block_consensus_pool = {key: temp_dict[key] for key in temp_dict if key in filtered_mini_blocks} 

            # Update own Blockchain
            self.update_blockchain(block)

            # Broadcast the block to the shards
            filtered_neigbours = []
            for id in self.neighbours_ids:
                if self.curr_shard_nodes[id].node_type == 2:
                    filtered_neigbours.append(id)
            
            broadcast(
                self.env, 
                block,
                "Block", 
                self.id, 
                filtered_neigbours, 
                self.curr_shard_nodes, 
                self.params
            ) 

        else:
            if self.params["verbose"]:
                print(f"[Debug] - Node {self.id} not ready \nPool - {self.mini_block_consensus_pool}")


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
        # To-do: Add vote option when node is unable to validate transaction
        for tx in tx_block.transactions_list:
            tx_block.votes_status[tx.id][self.id] = self.validate_transaction(tx)
    

    def receive_block(self):
        """
        Receive -
        (i)   Tx-block sent by the shard leader (for shard nodes),
        (ii)  Mini-block sent by the shard leader (for Principal Committee)
              / principal committee (intra-committee broadcast), or
        (iii) (Final) Block sent by the Principal Committee (for all the nodes)
        """
        while True:
            block = yield self.pipes.get()
            block_type = ""

            if isinstance(block, TxBlock):      block_type = "Tx"
            elif isinstance(block, MiniBlock):  block_type = "Mini"
            elif isinstance(block, Block):      block_type = "Final"
            else:
                raise RuntimeError("Unknown Block received")

            if self.params["verbose"]:
                print(
                    "%7.4f" % self.env.now
                    + " : "
                    + "%s received a %s-block - %s"
                    % (self.id, block_type, block.id)
                )

            if isinstance(block, TxBlock):
                if block not in self.shard_leader.processed_tx_blocks:
                    self.process_received_tx_block(block)
            
            # if isinstance(block, TxBlock):
            #     print(f"yoyo Id = {self.id} and shard_id = {self.shard_id} and leader = {self.shard_leader}")
            #     if block not in self.shard_leader.processed_tx_blocks:
            #         self.process_received_tx_block(block)

            elif isinstance(block, MiniBlock):
                if block.id not in self.processed_mini_blocks:
                    # print(f"[Test] = current - {block.id}\tProcessed = {self.processed_mini_blocks}")
                    self.process_received_mini_block(block)

                    # generate_block() is triggered whenever mini-block is received by the principal committee node
                    # Although whether block will be generated or not, is handled inside the function
                    self.generate_block()

            elif isinstance(block, Block):
                self.process_received_block(block)
    

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

                    broadcast(
                        self.env, 
                        tx_block, 
                        "Tx-block", 
                        self.id, 
                        shard_neigbours, 
                        self.curr_shard_nodes, 
                        self.params
                    )
            

    def process_received_mini_block(self, block):
        """
        Handle the received mini-block
        """
        if self.node_type != 1:
            raise RuntimeError(f"{block}\nMini-block received by node other than a principal committee node. Received by node {self.id}. Sent from {block.publisher_info} {block.message_data}")

        if not block.publisher_info:                  # MiniBlock received from the shard leader
            self.mini_block_consensus_pool[block.id] = {}
            self.mini_block_consensus_pool[block.id]["data"] = block
            self.mini_block_consensus_pool[block.id]["votes"] = {}

            principal_committee_neigbours = get_principal_committee_neigbours(self.curr_shard_nodes, self.neighbours_ids)
            for neighbour_id in principal_committee_neigbours:
                self.mini_block_consensus_pool[block.id]["votes"][neighbour_id] = -1
                # -1 = No vote received
            
            # To-do: Adjust mu and sigma for conensus delay; yielding not working
            consensus_delay_obj = Consensus(1, 1)
            # yield self.env.timeout(consensus_delay_obj.get_consensus_time())

            # To-do: Adjust threshold
            threshold = 0.5
            vote = 1 if consensus_delay_obj.get_random_number() > threshold else 0

            # Add own vote for this mini-block
            self.mini_block_consensus_pool[block.id]["votes"][self.id] = vote

            # Add meta-data to the mini-block before the broadcast
            block.publisher_info["id"] = self.id
            block.publisher_info["vote"] = vote
            
            # print(f"bugs = {get_principal_committee_neigbours(self.curr_shard_nodes, self.neighbours_ids)}")
            broadcast(
                self.env, 
                block, 
                "Mini-block-consensus", 
                self.id, 
                get_principal_committee_neigbours(self.curr_shard_nodes, self.neighbours_ids),
                self.curr_shard_nodes, 
                self.params,
            )

        else:       # MiniBlock received from the principal committee neighbor
            """
            Pseudo-code:

            Update the publisher's (or sender's) vote to own consensus_pool
            If receiving mini-block for the first time {
                a. Cast vote for the block and add it to its own pool
                b. Broadcast it to other neighbour nodes to let them know your own vote
            }
            else {
                a. Filter the neighbours which haven't casted their vote
                b. Broadcast it to only thos neighbours
            }
            """

            if has_received_mini_block(self.mini_block_consensus_pool, block.id):
                # Add publisher's vote in its own data copy
                self.mini_block_consensus_pool[block.id]["votes"][block.publisher_info["id"]] = block.publisher_info["vote"]
                
                # Filter the neighbours who have already voted for the mini-block
                principal_committee_neigbours = get_principal_committee_neigbours(self.curr_shard_nodes, self.neighbours_ids)
                filtered_neighbour_ids = [ id for id in principal_committee_neigbours if id not in self.mini_block_consensus_pool[block.id] ]
                filtered_neighbour_ids += [ id for id, vote in self.mini_block_consensus_pool[block.id].items() if vote == -1 ]
                
                # Add meta-data to the mini-block before the broadcast
                prev_publisher_id = block.publisher_info["id"]
                block.publisher_info["id"] = self.id
                block.publisher_info["vote"] = self.mini_block_consensus_pool[block.id]["votes"][self.id]
                
                if filtered_neighbour_ids:
                    # print(f"[Debug for - {self.id} = {filtered_neighbour_ids}")
                    # print(f"More info - {self.mini_block_consensus_pool}")
                    # print(f"[Filter Debug] - {filtered_neighbour_ids} {self.id}")
                    block.message_data = [ self.id ]
                    broadcast(
                        self.env, 
                        block, 
                        "Mini-block-consensus", 
                        self.id, 
                        filtered_neighbour_ids,
                        self.curr_shard_nodes, 
                        self.params,
                    )
                else:
                    if block.message_data and prev_publisher_id == block.message_data[0]:
                        # print(f"Meta = {block.message_data}")
                        block.message_data = []
                        broadcast(
                            self.env, 
                            block, 
                            "Mini-block-consensus", 
                            self.id, 
                            [ prev_publisher_id ],
                            self.curr_shard_nodes, 
                            self.params,
                        )
            else:
                # print(f"[Debug] - {self.mini_block_consensus_pool}")
                # print(f"Contd. - {block.id}")
                self.mini_block_consensus_pool[block.id] = {}
                self.mini_block_consensus_pool[block.id]["data"] = block
                self.mini_block_consensus_pool[block.id]["votes"] = {}

                # Add publisher's vote in its own data copy
                self.mini_block_consensus_pool[block.id]["votes"][block.publisher_info["id"]] = block.publisher_info["vote"]

                # Add own vote for the mini-block if vote not yet casted
                if self.id not in self.mini_block_consensus_pool[block.id]["votes"]:
                    consensus_delay_obj = Consensus(1, 1)
                    # yield self.env.timeout(consensus_delay_obj.get_consensus_time())

                    # To-do: Adjust threshold
                    threshold = 0.5
                    vote = 1 if consensus_delay_obj.get_random_number() > threshold else 0
                    self.mini_block_consensus_pool[block.id]["votes"][self.id] = vote
                
                # Add meta-data to the mini-block before the broadcast
                block.publisher_info["id"] = self.id
                block.publisher_info["vote"] = self.mini_block_consensus_pool[block.id]["votes"][self.id]
                
                # print(f"bugs = {get_principal_committee_neigbours(self.curr_shard_nodes, self.neighbours_ids)}")
                broadcast(
                    self.env, 
                    block, 
                    "Mini-block-consensus", 
                    self.id, 
                    get_principal_committee_neigbours(self.curr_shard_nodes, self.neighbours_ids),
                    self.curr_shard_nodes, 
                    self.params,
                )
            

    def process_received_block(self, block):
        if block not in self.blockchain:
            self.update_blockchain(block)

            broadcast(
                self.env, 
                block,
                "Block", 
                self.id, 
                self.neighbours_ids,
                self.curr_shard_nodes, 
                self.params
            ) 


    def update_blockchain(self, block):
        self.blockchain.append(block)
        
        if self.node_type == 2:
            self.params["chain"] = self.blockchain