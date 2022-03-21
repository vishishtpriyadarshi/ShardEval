import json
import os
import subprocess

num_nodes = [40]
num_shards = [4]
mini_block_capacity = [5, 8, 10, 15, 20]


for node_cnt in num_nodes:
    for shard_cnt in num_shards:
        for mbc in mini_block_capacity:
            # if (node_cnt != 15 and shard_cnt <= 2) or (node_cnt == 15 and shard_cnt > 1):
            #     continue

            filename = 'config/params.json'
            with open(filename, 'r') as f:
                data = json.load(f)
                data['num_nodes'] = node_cnt
                data['num_shards'] = shard_cnt
                data['verbose'] = 0 if node_cnt > 15 else 1
                data['mini_block_capacity'] = mbc
                
            os.remove(filename)
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)

            cmd = ['python', 'simulate.py']
            subprocess.Popen(cmd, shell=True).wait()