import numpy as np
import json
from queue import Queue


def is_voting_complete(tx_block):
    for _, tx_status in tx_block.votes_status.items():
        for _, node_vote in tx_status.items():
            if node_vote == -1:
                return False
    return True


def is_vote_casted(tx_block, node_id):
    random_tx = list(tx_block.votes_status.values())[0]
    return random_tx[node_id] != -1
    

def get_shard_neighbours(nodes, neighbours_ids, shard_id):
    shard_neigbours = []
    for id in neighbours_ids:
        if nodes[id].shard_id == shard_id and (nodes[id].node_type == 3 or nodes[id].node_type == 2):
            shard_neigbours.append(id)
    return shard_neigbours


def get_shard_nodes(nodes, shard_id):
    shard_neigbours = []
    for id in neighbours_ids:
        if nodes[id].shard_id == shard_id:
            shard_neigbours.append(id)
    return shard_neigbours


def get_principal_committee_neigbours(nodes, neighbours_list):
    principal_committee_neigbours = []
    for id in neighbours_list:
        if nodes[id].node_type == 1:
            principal_committee_neigbours.append(id)
    return principal_committee_neigbours


def get_block_delay(mu, sigma):
    delay = mu + sigma * np.random.randn()
    if delay < 0:
        return get_block_delay(mu, sigma)
    return delay


def get_transaction_delay(mu, sigma):
    delay = mu + sigma * np.random.randn()
    if delay < 0:
        return get_transaction_delay(mu, sigma)
    return delay


def get_transmission_delay(source, destination):
    with open("config/params.json", "r") as f:
        params = f.read()
    params = json.loads(params)
    mu = params["delay"][source][destination]["mu"]
    sigma = params["delay"][source][destination]["sigma"]
    delay = mu + sigma * np.random.randn()
    if delay < 0:
        return get_transmission_delay(source, destination)
    return delay


def can_generate_block(mini_block_consensus_pool, size_principal_committee, num_shards):
    """
    Check whether the principal committee node can generate block
    """
    # To-do: Handle case when 1 shard produces mutliple mini-blocks while other shard has produced only 1 mini-block
    if len(mini_block_consensus_pool) < num_shards:
        return False
    else:
        for key, val in mini_block_consensus_pool.items():
            if len(val["votes"]) != size_principal_committee:
                return False
            
            for node_id, vote in val["votes"].items():
                if vote == -1:
                    return False
        return True        


def has_received_mini_block(mini_block_consensus_pool, block_id):
    """
    Check whether the principal committee node is receiving mini-block for the first time
    """
    # print(f"[Test] = {block_id in mini_block_consensus_pool}\n{block_id}\t{mini_block_consensus_pool}")
    return block_id in mini_block_consensus_pool


def assign_next_hop_to_leader(nodes, leader):
    """
    Perform BFS to assign next_hop to all the shard nodes
    """
    q = Queue(maxsize = len(nodes))
    q.put(leader.id)
    used = {node_id: False for node_id in nodes}
    used[leader.id] = True

    while not q.empty():
        curr_node = nodes[q.get()]
        for neighbour_id in curr_node.neighbours_ids:
            if not used[neighbour_id]:
                used[neighbour_id] = True
                q.put(neighbour_id)
                nodes[neighbour_id].next_hop_id = curr_node.id