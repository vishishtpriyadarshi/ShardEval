"""
python simulate.py <params.json> <netDump.pkl>
"""
import sys
import simpy
import numpy as np
import json
import pickle as pkl
from network.block import Block
from network.network import Network
from time import time


def simulate(env, params):
    """Begin simulation"""
    net = Network("Blockchain", env, params)
    net.addNodes(params["numMiners"], params["numFullNodes"])
    net.addPipes(params["numMiners"], params["numFullNodes"])
    return net


"""Load parameters from params.json"""
paramsFile = sys.argv[1]
with open(paramsFile, "r") as f:
    params = f.read()
params = json.loads(params)

np.random.seed(7)
start = time()
env = simpy.Environment()
net = simulate(env, params)
env.run(until=params["simulationTime"])
net.displayChains()
stop = time()

totalNodes = params["numFullNodes"] + params["numMiners"]
print("\n\n\t\t\t\t\t\tPARAMETERS")
print(f"Number of Full nodes = {params['numFullNodes']}")
print(f"Number of Miners = {params['numMiners']}")
print(f"Degree of nodes = {totalNodes//2 + 1}")
print(f"Simulation time = {params['simulationTime']} seconds")

print("\t\t\t\t\t\tSIMULATION DATA")
"""Location distribution"""
print("Location Distribution Data")
for key, value in net.data["locationDist"].items():
    print(f"{key} : {100*value/totalNodes}%")

"""Block Propagation"""
print("\nBlock Propagation Data")
blockPropData = []
for key, value in net.data["blockProp"].items():
    blockPropData.append(value[1] - value[0])
    print(f"{key} : {blockPropData[-1]} seconds")

print(f"Mean Block Propagation time = {np.mean(blockPropData)} seconds")
print(f"Median Block Propagation time = {np.median(blockPropData)} seconds")
print(f"Minimum Block Propagation time = {np.min(blockPropData)} seconds")
print(f"Maximum Block Propagation time = {np.max(blockPropData)} seconds")

longestChain = []
longestChainNode = net.nodes["M0"]

for node in net.nodes.values():
    if len(node.blockchain) > len(longestChain):
        longestChainNode = node
        longestChain = node.blockchain

numTxs = 0
for block in longestChain:
    numTxs += len(block.transactionList)
meanBlockSize = (numTxs * 250) / len(longestChain)

print(f"\nTotal number of Blocks = {len(longestChain)}")
print(f"Mean block size = {meanBlockSize} bytes")
print(f"Total number of Stale Blocks = {net.data['numStaleBlocks']}")
print(f"Total number of Transactions = {net.data['numTransactions']}")

txWaitTimes = []
txRewards = []

for block in longestChain:
    for transaction in block.transactionList:
        txRewards.append(transaction.reward)
        txWaitTimes.append(transaction.miningTime - transaction.creationTime)

print(f"\nNode with longest chain = {longestChainNode.identifier}")
print(
    f"Min waiting time = {np.min(txWaitTimes)} with reward = {txRewards[np.argmin(txWaitTimes)]}"
)
print(f"Median waiting time = {np.median(txWaitTimes)}")
print(
    f"Max waiting time = {np.max(txWaitTimes)} with reward = {txRewards[np.argmax(txWaitTimes)]}"
)

print(f"\nNumber of forks observed = {net.data['numForks']}")

print(f"\nSimulation Time = {stop-start} seconds")

toStore = net.nodes.copy()

# netDump = {}

# for node in net.nodes.values():
#     netDump[node.identifier] = {}
#     netDump[node.identifier]["neighbourList"] = node.neighbourList
#     netDump[node.identifier]["location"] = node.location
#     netDump[node.identifier]["data"] = node.data
#     netDump[node.identifier]["blockchain"] = node.blockchain

# with open(sys.argv[2], "wb") as f:
#     pkl.dump(netDump, f)
