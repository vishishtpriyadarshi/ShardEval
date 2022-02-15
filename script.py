import json
import os
import subprocess

num_nodes = [15, 35, 70]
num_shards = [1, 2, 3, 4, 5]

for node_cnt in num_nodes:
    for shard_cnt in num_shards:
        if (node_cnt != 15 and shard_cnt <= 2) or (node_cnt == 15 and shard_cnt > 1):
            continue

        filename = 'config/params.json'
        with open(filename, 'r') as f:
            data = json.load(f)
            data['num_nodes'] = node_cnt
            data['num_shards'] = shard_cnt
            data['verbose'] = 0 if node_cnt > 15 else 1
            
        os.remove(filename)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

        cmd = ['python', 'simulate.py']
        subprocess.Popen(cmd).wait()