import os, sys
import simpy
import numpy as np
import json
import pathlib
import time

from network.network import Network
from utils.color_print import ColorPrint


def execute_simulation(name, env, params):
    network_obj = Network(name, env, params)
    network_obj.execute_sybil_resistance_mechanism()


    for idx in range(params["num_epochs"]):
        network_obj.run_epoch()
    
    """
    To-Do:  Decide where it should be put.
            Putting it before prev loop doesn't generate transactions.
    """
    env.run(until=params["simulation_time"])


def load_parameters():
    params_file = "config/params.json"
    if len(sys.argv) > 2:
        params_file = sys.argv[1]

    with open(params_file, "r") as f:
        params = f.read()
    params = json.loads(params)

    return params


def main():
    np.random.seed(7)
    params = load_parameters()

    orig_stdout = sys.stdout
    dir_suffix = sys.argv[1] if len(sys.argv) > 1 else time.strftime('%Y-%m-%d/%H-%M')
    dir_name = f"simulation_logs/{dir_suffix}"
    
    if not os.path.exists(dir_name):
        ColorPrint.print_info(f"\n[Info]: Creating directory '{dir_name}' for storing the simulation logs")
    pathlib.Path(dir_name).mkdir(parents=True, exist_ok=True)
    # file_name = f"{dir_name}/simulation_results_txLimit{params['tx_block_capacity']}_n{params['num_nodes']}_sh{params['num_shards']}_sim{params['simulation_time']}.log"
    file_name = f"{dir_name}/simulation_results_cstx{params['cross_shard_tx_percentage']}_n{params['num_nodes']}_sh{params['num_shards']}_sim{params['simulation_time']}.log"
    
    f = open(file_name, 'w')
    ColorPrint.print_info(f"\n[Info]: Writing simulation logs to the file '{file_name}'")
    sys.stdout = f

    params["generated_tx_count"], params["processed_tx_count"] = 0, 0
    params["generated_cross_shard_tx_count"], params["generated_intra_shard_tx_count"] = 0, 0
    params["processed_cross_shard_tx_count"], params["processed_intra_shard_tx_count"] = 0, 0

    start_time = time.time()
    env = simpy.Environment()
    execute_simulation("Test Network", env, params)
    stop_time = time.time()

    sim_time = stop_time - start_time
    
    print("\n\n============  SIMULATION DETAILS  ============")
    print(f"\nNumber of nodes = {params['num_nodes']}")
    print(f"Number of shards = {params['num_shards']}")
    print(f"Fraction of cross-shard tx = {params['cross_shard_tx_percentage']}")
    print(f"Simulation Time = {sim_time} seconds")

    if 'chain' in params:
        count, cross_shard_tx_count, intra_shard_tx_count = 0, 0, 0
        for block in params['chain']:
            count += len(block.transactions_list)

            for tx in block.transactions_list:
                intra_shard_tx_count += 1 - tx.cross_shard_status
                cross_shard_tx_count += tx.cross_shard_status
        
        print(f"\nLength of Blockchain = {len(params['chain'])}")
        print(f"Total no of transactions included in Blockchain = {count}")
        print(f"Total no of intra-shard transactions included in Blockchain = {intra_shard_tx_count}")
        print(f"Total no of cross-shard transactions included in Blockchain = {cross_shard_tx_count}")
        
        time_tx_processing = params['simulation_time'] - params['tx_start_time']
        time_network_configuration = params['tx_start_time'] - params['network_config_start_time']

        print(f"\nTotal no of transactions processed = {params['processed_tx_count']}")
        print(f"Total no of intra-shard transactions processed = {params['processed_intra_shard_tx_count']}")
        print(f"Total no of cross-shard transactions processed = {params['processed_cross_shard_tx_count']}")

        print(f"\nTotal no of transactions generated = {params['generated_tx_count']}")
        print(f"Total no of intra-shard transactions generated = {params['generated_intra_shard_tx_count']}")
        print(f"Total no of cross-shard transactions generated = {params['generated_cross_shard_tx_count']}")

        print(f"\nProcessed TPS = {params['processed_tx_count']/params['simulation_time']}")
        print(f"Accepted TPS = {count/params['simulation_time']}")

        # print(f"\nLatency of network configuration (in simpy units) = {time_network_configuration}")
    else:
        print("Simulation didn't execute for sufficiently long time")

    sys.stdout = orig_stdout
    f.close()

if __name__=="__main__":
    main()