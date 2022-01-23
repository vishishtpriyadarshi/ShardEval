import simpy
import numpy as np

from nodes.miner import Miner
from nodes.full_node import FullNode
from network.block import Block
from network.pipe import Pipe
from network.broadcast import broadcast
from transaction_factory.transaction import Transaction
from utils import get_transaction_delay


class Network:
    """docstring for Network"""

    def __init__(self, name, env, params):
        self.name = name
        self.env = env
        self.params = params
        self.locations = params["locations"]
        self.miners = {}
        self.fullNodes = {}
        self.nodes = {}
        self.pipes = {}
        self.data = {}
        self.data["blockProp"] = {}
        self.data["locationDist"] = {}
        self.data["numStaleBlocks"] = 0
        self.data["numTransactions"] = 0
        self.data["numForks"] = 0

        """Initialize the location distribution data"""
        for loc in self.locations:
            self.data["locationDist"][loc] = 0

        self.env.process(self.addTransaction())

    def addTransaction(self):
        num = 0
        while True:
            delay = get_transaction_delay(
                self.params["transactionMu"], self.params["transactionSigma"]
            )
            yield self.env.timeout(delay)

            value = np.random.randint(self.params["txLow"], self.params["txHigh"])
            reward = value * self.params["rewardPercentage"]

            transaction = Transaction("T%d" % num, self.env.now, value, reward)
            self.data["numTransactions"] += 1
            if self.params["verbose"]:
                print(
                    "%7.4f" % self.env.now
                    + " : "
                    + "%s added with reward %.2f"
                    % (transaction.identifier, transaction.reward)
                )
            """Broadcast transactions to all neighbours"""
            transactionNeighbours = list(
                np.random.choice(list(self.nodes.keys()), size=len(self.nodes) // 2)
            )
            broadcast(
                self.env,
                transaction,
                "Transaction",
                "TempID",
                transactionNeighbours,
                self.params,
                nodes=self.nodes,
            )
            num += 1

    def addNodes(self, numMiners, numFullNodes):
        """Add Nodes to network"""
        numNodes = numFullNodes + numMiners
        """Degree of network graph. Degree >= n/2 guarantees a connected graph"""
        degree = numNodes // 2 + 1
        for identifier in range(numNodes):
            """Possible neighbours are [0, 1, ... i-1, i+1, ... n]"""
            possibleNeighbours = list(range(identifier)) + list(
                range(identifier + 1, numNodes)
            )
            """Generate a random sample of size degree without replacement from possible neighbours"""
            randNeighbour = np.random.choice(
                possibleNeighbours, size=degree, replace=False
            )
            neighbourList = [
                "M%d" % x if x < numMiners else "F%d" % (x - numMiners)
                for x in randNeighbour
            ]

            """Generate a location of the node"""
            location = np.random.choice(self.locations, size=1)[0]
            self.data["locationDist"][location] += 1

            if identifier < numMiners:
                self.miners["M%d" % identifier] = Miner(
                    "M%d" % identifier,
                    self.env,
                    neighbourList,
                    self.pipes,
                    self.nodes,
                    location,
                    self.data,
                    self.params,
                )
                if bool(self.params["verbose"]):
                    print(
                        "%7.4f" % self.env.now
                        + " : "
                        + "%s added at location %s with neighbour list %s"
                        % ("M%d" % identifier, location, neighbourList)
                    )
            else:
                self.fullNodes["F%d" % (identifier - numMiners)] = FullNode(
                    "F%d" % (identifier - numMiners),
                    self.env,
                    neighbourList,
                    self.pipes,
                    self.nodes,
                    location,
                    self.data,
                    self.params,
                )
                if bool(self.params["verbose"]):
                    print(
                        "%7.4f" % self.env.now
                        + " : "
                        + "%s added at location %s with neighbour list %s"
                        % ("F%d" % identifier, location, neighbourList)
                    )
        self.nodes.update(self.miners)
        self.nodes.update(self.fullNodes)

    def addPipes(self, numMiners, numFullNodes):
        for identifier in range(numMiners):
            self.pipes["M%d" % identifier] = Pipe(
                self.env, "M%d" % identifier, self.nodes
            )
        for identifier in range(numFullNodes):
            self.pipes["F%d" % identifier] = Pipe(
                self.env, "F%d" % identifier, self.nodes
            )

    def displayChains(self):
        print("\n--------------------All Miners--------------------\n")
        for node in self.nodes.values():
            node.displayChain()

