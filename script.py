import json
import os
import sys
import subprocess
import time

num_nodes = [100]
num_shards = [i for i in range(3, 60)]
# tx_block_capacity = [5, 8, 10, 15, 20]
cs_tx_fraction = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

dir_suffix = time.strftime('%Y-%m-%d/%H-%M')

for node_cnt in num_nodes:
    for shard_cnt in num_shards:
        if shard_cnt == int(0.65 * node_cnt / 3):
            break
        
        for cs_tx_ratio in cs_tx_fraction:
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

            cmd = ['python', 'simulate.py', dir_suffix]
            proc = subprocess.Popen(cmd)
            proc.wait()

            (stdout, stderr) = proc.communicate()
            if proc.returncode != 0:
                sys.exit("\n\x1b[1;31m[script.py]: Aw, Snap! An error has occurred")