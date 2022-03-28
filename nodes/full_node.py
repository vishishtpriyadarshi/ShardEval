import numpy as np
import random
import functools
import operator

from nodes.participating_node import ParticipatingNode
from network.broadcast import broadcast
from network.mini_block import MiniBlock
from network.tx_block import TxBlock
from network.cross_shard_block import CrossShardBlock
from network.block import Block
from network.pipe import Pipe
from factory.transaction import Transaction
from factory.transaction_pool import TransactionPool
from network.consensus.consensus import Consensus
from utils.helper import get_transaction_delay, is_voting_complete, get_shard_neighbours, \
    get_principal_committee_neigbours, is_vote_casted, can_generate_block, has_received_mini_block, \
    is_voting_complete_for_cross_shard_block, is_vote_casted_for_cross_shard_block, received_cross_shard_block_for_first_time


class FullNode(ParticipatingNode):
    """
    This class models the nodes which will take part in the Blockchain.
    These nodes are the subsets of the participating nodes.
    """

    def __init__(self, id, env, location, params):
        super().__init__(id, env, location, params)

        self.node_type = 0
        """ 
        node_type --
            0 - Node is in between re-configuration (slot)
            1 - Principal Committee
            2 - Shard Leader
            3 - Shard Member
        """
        
        self.shard_id = -1
        self.shard_leader_id = -1
        self.curr_shard_nodes = {}
        self.neighbours_ids = []
        self.blockchain = []
        self.shard_leaders = {}

        # Handled by only principal committee
        self.mini_block_consensus_pool = {}
        self.processed_mini_blocks = []
        self.processed_tx_blocks = []
        self.current_tx_blocks = []

        # Experimental
        self.pc_leader_id = -1
        self.mini_blocks_vote_pool = []
        self.next_hop_id = -1


    def add_network_parameters(self, curr_shard_nodes, neighbours_ids):
        self.curr_shard_nodes = curr_shard_nodes
        self.neighbours_ids = neighbours_ids
        self.transaction_pool = TransactionPool(
            self.env, self.id, neighbours_ids, curr_shard_nodes, self.params
        )
        self.pipes = Pipe(self.env, self.id, self.curr_shard_nodes)
        self.env.process(self.receive_block())

    def init_shard_leaders(self, leaders):
        self.shard_leaders = leaders

    def update_neighbours(self, neighbours_ids):
        self.neighbours_ids = neighbours_ids
        self.transaction_pool.neighbours_ids = neighbours_ids


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
            
            self.params["generated_tx_count"] += 1
            if self.params["verbose"]:
                print(
                    "%7.4f" % self.env.now
                    + " : "
                    + "%s added with reward %.2f"
                    % (transaction.id, transaction.reward)
                )

            neighbour_ids = [self.id if self.next_hop_id == -1 else self.next_hop_id]
            broadcast(
                self.env, 
                transaction, 
                "Tx", 
                self.id, 
                neighbour_ids, 
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

            if self.transaction_pool.transaction_queue.length() >= self.params["tx_block_capacity"]:
                # print(f"Queue size of {self.id} = {self.transaction_pool.transaction_queue.length()}")
                transactions_list = self.transaction_pool.transaction_queue.pop(self.params["tx_block_capacity"])
                num_cross_shard_txns = int(len(transactions_list) * 0.3)
                num_intra_shard_txns = len(transactions_list) - num_cross_shard_txns
                random.shuffle(transactions_list)

                intra_shard_txns = transactions_list[:num_intra_shard_txns]
                cross_shard_txns = transactions_list[num_intra_shard_txns:]
                
                for txn in cross_shard_txns:
                    txn.cross_shard_status = 1
                    txn.set_receiver(self.get_cross_shard_random_node_id())
                # print(f"New Queue size of {self.id} = {self.transaction_pool.transaction_queue.length()}")
                # print(f"Queue {self.id} = {[tx.id for tx in self.transaction_pool.transaction_queue.queue]}\n\n")

                # To-do: Add different type of delay for the pre-processing
                delay = get_transaction_delay(
                    self.params["transaction_mu"], self.params["transaction_sigma"]
                )
                yield self.env.timeout(delay)
                
                shard_neighbours = get_shard_neighbours(self.curr_shard_nodes, self.neighbours_ids, self.shard_id)
                # print(f"[Debug]: Shard neighbours are {shard_neighbours}")

                # To-do: Clean this piece of code for filtered_curr_shard_nodes
                filtered_curr_shard_nodes = []
                for node_id in self.curr_shard_nodes.keys():
                    if self.curr_shard_nodes[node_id].shard_id == self.shard_id and self.curr_shard_nodes[node_id].node_type == 3:
                        filtered_curr_shard_nodes.append(node_id)

                id = int(1000*round(self.env.now, 3))
                tx_block = TxBlock(f"TB_{self.id}_{id}", intra_shard_txns, self.params, self.shard_id, filtered_curr_shard_nodes)
                cross_shard_block = CrossShardBlock(f"TB_{self.id}_{id}", cross_shard_txns, self.params, self.shard_id, filtered_curr_shard_nodes)
                

                """
                Cross-shard Transactions -
                    (i)  Probabilistically divide the tx into inter vs intra(cross) shard tx
                    (ii) Create Cross-shard Block and broadcast it
                """
                print(f"[Logs 2]: At {self.env.now} -- {self.id} = {len(transactions_list)}")
                broadcast(
                    self.env, 
                    tx_block, 
                    "Tx-block", 
                    self.id, 
                    shard_neighbours, 
                    self.curr_shard_nodes, 
                    self.params
                )

                neighbour_shard_leaders = list(self.shard_leaders.keys())
                neighbour_shard_leaders.remove(self.id)

                broadcast(
                    self.env, 
                    cross_shard_block, 
                    "Cross-shard-block", 
                    self.id,
                    neighbour_shard_leaders, 
                    self.curr_shard_nodes, 
                    self.params
                )
            else:       # To avoid code being stuck in an infinite loop
                delay = get_transaction_delay(
                    self.params["transaction_mu"], self.params["transaction_sigma"]
                )
                yield self.env.timeout(delay)


    def generate_mini_block(self, tx_block):
        """
        Generate a mini block and broadcast it to the principal committee
        """

        if self.node_type != 2:
            raise RuntimeError("Mini-block can only be generated by the shard leader")

        self.current_tx_blocks.append(tx_block)
        if self.params["verbose"]:
            print(f"[Debug len]: processed_tx_blocks = {len(self.processed_tx_blocks)}")

        if len(self.current_tx_blocks) >= self.params["tx_blocks_in_mini_block"]:
            # To-Do: Maintain already processed tx-blocks list
            self.processed_tx_blocks += self.current_tx_blocks[0 : self.params["tx_blocks_in_mini_block"]]
            self.current_tx_blocks = self.current_tx_blocks[self.params["tx_blocks_in_mini_block"] : ]

            # To-Do: Filter transactions from tx_block based on votes
            accepted_transactions = tx_block.transactions_list
            # print(f"[Log]: {self.id} = {len(accepted_transactions)}")

            self.params["processed_tx_count"] += len(accepted_transactions)

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
        
        """ M - 1 (with leader) """

        """
        Steps -
            1. Shard leader sends mini-block to a principal committee node
            2. Principal committee node sends the mini-block to p.c. leader
            3. Leader asks for votes from other p.c. nodes 
               This step can be optimised by buffering all the mini-blocks from the different shards, and then 
               broadcasting it to the network for the votes.
            4. After leader has got the votes, it will generate the block and broadcast to the entire network
            5. p.c. nodes won't broadcast it to other p.c. nodes but to the rest of the network.
        """

        """ M - 2 (Without leader) """
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
            count_tx_processed = 0

            for key, val in self.mini_block_consensus_pool.items():
                block = val["data"]
                count_tx_processed += len(block.transactions_list)

                net_vote = 0
                for id, curr_vote in val["votes"].items():
                    net_vote += curr_vote if curr_vote else -1
                
                if net_vote > 0:
                    if block.shard_id in temp_data:
                        existing_block = temp_data[block.shard_id]

                        # Select only latest mini-block sent by a shard
                        if int(block.id[block.id.rfind('_')+1:]) > int(existing_block.id[existing_block.id.rfind('_')+1:]):
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
            
            filtered_neigbours = self.neighbours_ids
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
            # yield self.env.timeout(1)
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

    
    def cast_vote_for_cross_shard_block(self, cross_shard_block):
        """
        ...
        """
        # To-do: Add vote option when node is unable to validate transaction
        for tx in cross_shard_block.transactions_list:
            vote = 2

            # If tx is relevant to this shard, vote for it else discard it by voting 2
            if tx.receiver in self.curr_shard_nodes.keys():
                vote = self.validate_transaction(tx)
            
            cross_shard_block.shard_votes_status[self.shard_id][tx.id][self.id] = vote
    

    def receive_block(self):
        """
        Receive -
        (i)   Tx-block sent by the shard leader (for shard nodes),
        (ii)  Mini-block sent by the shard leader (for Principal Committee)
              / principal committee (intra-committee broadcast), or
        (iii) (Final) Block sent by the Principal Committee (for all the nodes)
        """
        while True:
            packeted_message = yield self.pipes.get()
            block = packeted_message.message
            block_type = ""

            """
            Cross-shard Transactions -
                Add processing step for the Cross-shard Block
            """
            if isinstance(block, list):                 block_type = "List"
            elif isinstance(block, TxBlock):            block_type = "Tx"
            elif isinstance(block, CrossShardBlock):    block_type = "Cross-shard"
            elif isinstance(block, MiniBlock):          block_type = "Mini"
            elif isinstance(block, Block):              block_type = "Final"
            else:
                raise RuntimeError("Unknown Block received")

            if self.params["verbose"]:
                debug_info = [ b.id for b in block ] if isinstance(block, list) else block.id
                print(
                    "%7.4f" % self.env.now
                    + " : "
                    + "Node %s received a %s-block - %s from %s"
                    % (self.id, block_type, debug_info, packeted_message.sender_id)
                )

            if isinstance(block, list):
                self.process_received_mini_blocks_list(block, packeted_message.sender_id)
                if self.id == self.pc_leader_id:
                    self.generate_block()

            elif isinstance(block, TxBlock):
                if block not in self.shard_leader.processed_tx_blocks:
                    self.process_received_tx_block(block, packeted_message.sender_id)

            elif isinstance(block, CrossShardBlock):
                flag = False
                for txn in block.transactions_list:
                    if(txn.cross_shard_status != 1):
                        raise RuntimeError(f"Intra Shard transaction present in Cross Shard Block")
                    receiver = txn.receiver
                    if(receiver in self.curr_shard_nodes.keys()):
                        flag = True
                        break
    
                if flag:        # Cross-shard-block has even 1 tx related to the current shard
                    curr_shard_nodes_id = [ node for node in self.curr_shard_nodes.keys() ]
                    block.add_shard_info_for_voting(self.shard_id, curr_shard_nodes_id)
                    self.process_received_cross_shard_block(block, packeted_message.sender_id)

            elif isinstance(block, MiniBlock):
                if block.id not in self.processed_mini_blocks:
                    # print(f"[Test] = current - {block.id}\tProcessed = {self.processed_mini_blocks}")
                    self.process_received_mini_block(block)

                    # generate_block() is triggered whenever mini-block is received by the principal committee node
                    # Although whether block will be generated or not, is handled inside the function
                    """ self.generate_block() """

            elif isinstance(block, Block):
                self.process_received_block(block)
    

    def process_received_tx_block(self, tx_block, sender_id):
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
            if flag:
                if self.params["verbose"]:
                    print(
                        "%7.4f" % self.env.now
                        + " : "
                        + "Node %s (Leader) received voted Tx-block %s" % (self.id, tx_block.id)
                    )
                self.generate_mini_block(tx_block)
            else:
                raise RuntimeError(f"Shard Leader {self.id} received a voted Tx-block {tx_block.id} which is not been voted by all shard nodes.")

        elif self.node_type == 3:
            if flag:
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
                    [ self.next_hop_id ], 
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
                            + "Node %s voted for the Tx-block %s" % (self.id, tx_block.id)
                        )

                    # If voting is complete, pass the tx-block to the leader, else broadcast it further in the network
                    neighbours = []
                    if is_voting_complete(tx_block):
                        neighbours = [ self.next_hop_id ]
                        if self.params["verbose"]:
                            print(
                                "%7.4f" % self.env.now
                                + " : "
                                + "Voting for the tx-block %s is complete and node %s sent it on its path to shard leader" % (tx_block.id, self.id)
                            )
                    else:
                        neighbours = shard_neigbours    # Exclude source node
                        neighbours.remove(sender_id)

                    broadcast(
                        self.env, 
                        tx_block, 
                        "Tx-block", 
                        self.id, 
                        neighbours, 
                        self.curr_shard_nodes, 
                        self.params
                    )
            

    def process_received_mini_blocks_list(self, blocks, sender_id):
        """
        Handle the received list of mini-blocks
        """
        
        if self.node_type != 1:
            raise RuntimeError(f"Mini-block list (voting) received by node other than a principal committee node. Received by node {self.id}.")

        if self.id == self.pc_leader_id:
            for mini_block in blocks:
                self.mini_block_consensus_pool[mini_block.id]["votes"][sender_id] = mini_block.message_data[sender_id]
            
        else:
            voted_blocks = []
            for mini_block in blocks:
                consensus_delay_obj = Consensus(1, 1)
                # To-do: Adjust threshold
                threshold = 0.5
                vote = 1 if consensus_delay_obj.get_random_number() > threshold else 0

                new_mini_block = MiniBlock(mini_block.id, mini_block.transactions_list, mini_block.params, mini_block.shard_id)
                new_mini_block.shard_id = mini_block.shard_id

                new_mini_block.message_data[self.id] = vote
                voted_blocks.append(new_mini_block)
            
            broadcast(
                self.env, 
                voted_blocks, 
                "Mini-blocks-voting", 
                self.id, 
                [ self.pc_leader_id ], 
                self.curr_shard_nodes, 
                self.params
            )


    def process_received_mini_block(self, block):
        """
        Handle the received mini-block
        """
        if self.node_type != 1:
            raise RuntimeError(f"Mini-block received by node other than a principal committee node. Received by node {self.id}.")

        """ M - 1 (With leader) """
        if block not in self.processed_mini_blocks:
            if self.id == self.pc_leader_id:
                self.mini_blocks_vote_pool.append(block)
                self.mini_block_consensus_pool[block.id] = {}
                self.mini_block_consensus_pool[block.id]["data"] = block
                self.mini_block_consensus_pool[block.id]["votes"] = {}
                
                consensus_delay_obj = Consensus(1, 1)
                # To-do: Adjust threshold
                threshold = 0.5
                vote = 1 if consensus_delay_obj.get_random_number() > threshold else 0
                self.mini_block_consensus_pool[block.id]["votes"][self.id] = vote

                if len(self.mini_blocks_vote_pool) == self.params["num_shards"]:
                    principal_committee_neigbours = get_principal_committee_neigbours(self.curr_shard_nodes, self.neighbours_ids)
                    broadcast(
                        self.env, 
                        self.mini_blocks_vote_pool, 
                        "Mini-blocks-voting", 
                        self.id, 
                        principal_committee_neigbours, 
                        self.curr_shard_nodes, 
                        self.params
                    )

                    self.mini_blocks_vote_pool = []

            else:
                broadcast(
                    self.env, 
                    block, 
                    "Mini-block-consensus", 
                    self.id, 
                    [ self.pc_leader_id ], 
                    self.curr_shard_nodes, 
                    self.params
                )
            
            self.processed_mini_blocks.append(block)

        """ M - 2 (Without leader)
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
            
            # Pseudo-code:

            # Update the publisher's (or sender's) vote to own consensus_pool
            # If receiving mini-block for the first time {
            #     a. Cast vote for the block and add it to its own pool
            #     b. Broadcast it to other neighbour nodes to let them know your own vote
            # }
            # else {
            #     a. Filter the neighbours which haven't casted their vote
            #     b. Broadcast it to only thos neighbours
            # }
            

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
            """
            

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


    def process_received_cross_shard_block(self, cross_shard_block, sender_id):
        """
        Handle the received Cross-shard-block
        """

        if self.node_type == 0:
            raise RuntimeError("Cross-shard-block received in between re-configuration.")
            # To-do: Complete when dealing with nodes re-configuration (new epoch)
        
        if self.node_type == 1:
            raise RuntimeError("Cross-shard-block received by Principal Committee node.")    

        flag = is_voting_complete_for_cross_shard_block(cross_shard_block, self.shard_id)
        shard_neigbours = get_shard_neighbours(
            self.curr_shard_nodes, self.neighbours_ids, self.shard_id
        )

        if self.node_type == 2:
            if received_cross_shard_block_for_first_time(cross_shard_block, self.shard_id):
                shard_neighbours = get_shard_neighbours(self.curr_shard_nodes, self.neighbours_ids, self.shard_id)
                broadcast(
                    self.env, 
                    cross_shard_block, 
                    "Cross-shard-block", 
                    self.id, 
                    shard_neighbours, 
                    self.curr_shard_nodes, 
                    self.params
                )
            else:
                if flag:
                    if self.params["verbose"]:
                        print(
                            "%7.4f" % self.env.now
                            + " : "
                            + "Node %s (Leader) received voted Cross-shard-block %s" % (self.id, cross_shard_block.id)
                        )
                    # self.generate_mini_block(cross_shard_block)
                    print(f"[Hackerman]: Voting for cross-shard-block {cross_shard_block.id} is complete and voted block reached the shard leader")
                else:
                    print(cross_shard_block.shard_votes_status)
                    raise RuntimeError(f"Shard Leader {self.id} received a voted Cross-shard-block {cross_shard_block.id} which is not been voted by all shard nodes.")

        elif self.node_type == 3:
            if flag:
                if self.params["verbose"]:
                    print(
                        "%7.4f" % self.env.now
                        + " : "
                        + "Node %s (shard node) propagated voted Cross-shard-block %s" % (self.id, cross_shard_block.id)
                    )

                broadcast(
                    self.env, 
                    cross_shard_block, 
                    "Cross-shard-block", 
                    self.id, 
                    [ self.next_hop_id ], 
                    self.curr_shard_nodes, 
                    self.params
                )
            else:
                if is_vote_casted_for_cross_shard_block(cross_shard_block, self.shard_id, self.id) == False:
                    print(f"VP - Id is {cross_shard_block.id} \nVotes = {cross_shard_block.shard_votes_status[self.shard_id]}")
                    self.cast_vote_for_cross_shard_block(cross_shard_block)
                    print(f"Vishisht - Id is {cross_shard_block.id} \nVotes = {cross_shard_block.shard_votes_status[self.shard_id]}")
                    if self.params["verbose"]:
                        print(
                            "%7.4f" % self.env.now
                            + " : "
                            + "Node %s voted for the Cross-shard-block %s" % (self.id, cross_shard_block.id)
                        )

                    # If voting is complete, pass the Cross-shard-block to the leader, else broadcast it further in the network
                    neighbours = []
                    if is_voting_complete_for_cross_shard_block(cross_shard_block, self.shard_id):
                        neighbours = [ self.next_hop_id ]
                        if self.params["verbose"]:
                            print(
                                "%7.4f" % self.env.now
                                + " : "
                                + "Voting for the Cross-shard-block %s is complete and node %s sent it on its path to shard leader" % (cross_shard_block.id, self.id)
                            )
                    else:
                        neighbours = shard_neigbours    # Exclude source node
                        neighbours.remove(sender_id)

                    print(f"Sourav {self.id} - {is_voting_complete_for_cross_shard_block(cross_shard_block, self.shard_id)} and list is \n {cross_shard_block.shard_votes_status[self.shard_id]}")
                    broadcast(
                        self.env, 
                        cross_shard_block, 
                        "Cross-shard-block", 
                        self.id, 
                        neighbours, 
                        self.curr_shard_nodes, 
                        self.params
                    )


    def update_blockchain(self, block):
        self.blockchain.append(block)
        
        if self.node_type == 2:
            self.params["chain"] = self.blockchain


    def get_cross_shard_random_node_id(self):
        cross_shard_leader = self.shard_leaders[self.id]
        while(cross_shard_leader.id == self.id):
            cross_shard_leader = random.choice(list(self.shard_leaders.values()))
        cross_shard_node = random.choice(list(cross_shard_leader.curr_shard_nodes.values()))
        while(cross_shard_node.node_type == 2):
            cross_shard_node = random.choice(list(cross_shard_leader.curr_shard_nodes.values()))
        return cross_shard_node.id