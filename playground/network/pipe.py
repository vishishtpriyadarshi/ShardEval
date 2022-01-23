import simpy
from utils import get_transmission_delay


class Pipe(object):
    """This class represents the propagation through a cable."""

    def __init__(self, env, identifier, allNodes):
        self.env = env
        self.allNodes = allNodes
        self.identifier = identifier
        self.store = simpy.Store(self.env)

    def latencyPut(self, value, delay):
        yield self.env.timeout(delay)
        return self.store.put(value)

    def put(self, value, sourceLocation):
        destLocation = self.allNodes[self.identifier].location
        delay = get_transmission_delay(sourceLocation, destLocation)
        return self.env.process(self.latencyPut(value, delay))

    def get(self):
        return self.store.get()
