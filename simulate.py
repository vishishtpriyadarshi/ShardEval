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

def load_parameters():
    params_file = sys.argv[1]
    with open(params_file, "r") as f:
        params = f.read()
    params = json.loads(params)

    return params

def main():
    params = load_parameters()
    execute_simulation("Test 1", "", params)


if __name__=="__main__":
    main()