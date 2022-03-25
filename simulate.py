import os, sys
import simpy
import numpy as np
import json
import pathlib
import time

from network.network import Network


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
    
    dir_name = f"simulation_logs/{time.strftime('%Y-%m-%d')}"
    if not os.path.exists(dir_name):
        print(f"Creating directory '{dir_name}' for storing the simulation logs")
    pathlib.Path(dir_name).mkdir(parents=True, exist_ok=True)
    file_name = f"{dir_name}/simulation_results_txLimit{params['tx_block_capacity']}_n{params['num_nodes']}_sh{params['num_shards']}_sim{params['simulation_time']}.log"
    
    f = open(file_name, 'w')
    print(f"Writing simulation logs to the file '{file_name}'\n")
    sys.stdout = f

    params["generated_tx_count"], params["processed_tx_count"] = 0, 0

    start_time = time.time()
    env = simpy.Environment()
    execute_simulation("Test Network", env, params)
    stop_time = time.time()

    sim_time = stop_time - start_time
    
    print("\n\n============  SIMULATION DETAILS  ============")
    print(f"\nNumber of nodes = {params['num_nodes']}")
    print(f"Number of shards = {params['num_shards']}")
    print(f"Simulation Time = {sim_time} seconds")

    if 'chain' in params:
        count = 0
        for block in params['chain']:
            count += len(block.transactions_list)
        
        print(f"\nLength of Blockchain = {len(params['chain'])}")
        print(f"Total no of transactions included in Blockchain = {count}")
        
        time_tx_processing = params['simulation_time'] - params['tx_start_time']
        time_network_configuration = params['tx_start_time'] - params['network_config_start_time']

        print(f"Total no of transactions processed = {params['processed_tx_count']}")
        print(f"Total no of transactions generated = {params['generated_tx_count']}")

        print(f"\nSimpy TPS (processed) = {params['processed_tx_count']/params['simulation_time']}")
        print(f"Simpy TPS (accepted) = {count/params['simulation_time']}")

        print(f"\nLatency of network configuration (in simpy units) = {time_network_configuration}")
    else:
        print("Simulation didn't execute for sufficiently long time")

    sys.stdout = orig_stdout
    f.close()

if __name__=="__main__":
    main()