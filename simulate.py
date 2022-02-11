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
    print(f"\nSimulation Time = {sim_time} seconds")

    if 'chain' in params:
        print(f"Blockchain = {params['chain']}")
        count = 0
        for block in params['chain']:
            count += len(block.transactions_list)
        
        print(f"TPS = {count/sim_time}")
    else:
        print("Simulation didn't execute for sufficiently long time")


if __name__=="__main__":
    main()