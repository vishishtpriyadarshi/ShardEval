import json
import os
import subprocess

num_nodes = [100]
num_shards = [4]
# tx_block_capacity = [5, 8, 10, 15, 20]
cs_tx_fraction = [0, 0.25, 0.5, 0.75, 0.9]


for node_cnt in num_nodes:
    for shard_cnt in num_shards:
        for cs_tx_ratio in cs_tx_fraction:
            # if (node_cnt != 15 and shard_cnt <= 2) or (node_cnt == 15 and shard_cnt > 1):
            #     continue

            filename = 'config/params.json'
            with open(filename, 'r') as f:
                data = json.load(f)
                data['num_nodes'] = node_cnt
                data['num_shards'] = shard_cnt
                data['verbose'] = 0 if node_cnt > 15 else 1
                data['cross_shard_tx_percentage'] = cs_tx_ratio
                
            os.remove(filename)
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)

            cmd = ['python', 'simulate.py']
            subprocess.Popen(cmd).wait()