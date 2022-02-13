"""
Run: python simulate.py config/params.json > simulation_logs/simulation_results.log
"""

import sys
import simpy
import numpy as np
import json
from time import time

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
    params_file = sys.argv[1]
    with open(params_file, "r") as f:
        params = f.read()
    params = json.loads(params)

    return params


def main():
    np.random.seed(7)
    params = load_parameters()
    
    start_time = time()
    env = simpy.Environment()
    execute_simulation("Test Network", env, params)
    stop_time = time()

    sim_time = stop_time - start_time
    
    print("\n\n============  SIMULATION DETAILS  ============")
    print(f"\nSimulation Time = {sim_time} seconds")

    if 'chain' in params:
        print(f"Blockchain = {params['chain']}")
        count = 0
        for block in params['chain']:
            count += len(block.transactions_list)
        
        print(f"Length of Blockchain = {len(params['chain'])}")
        # print(f"\nTotal no of transactions accepted = {count}")
        # print(f"(accepted) TPS = {count/sim_time}")

        time_tx_processing = params['simulation_time'] - params['tx_start_time']
        time_network_configuration = params['tx_start_time'] - params['network_config_start_time']

        print(f"\nTotal no of transactions processed = {params['tx_count']}")
        # print(f"(total) TPS = {params['tx_count']/sim_time}")
        print(f"Simpy TPS = {params['tx_count']/params['simulation_time']}")

        # print(f"\nLatency of network configuration (in simpy units) = {time_network_configuration}")
    else:
        print("Simulation didn't execute for sufficiently long time")


if __name__=="__main__":
    main()