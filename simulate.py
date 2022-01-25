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

    env.run(until=params["simulation_time"])
    for idx in range(params["num_epochs"]):
        network_obj.run_epoch()

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

    print(f"Simulation Time = {stop_time - start_time} seconds")


if __name__=="__main__":
    main()