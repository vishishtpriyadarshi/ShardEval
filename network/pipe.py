import simpy
from utils.helper import get_transmission_delay


class Pipe(object):
    """
    This class represents the propagation of data through a cable.
    """

    def __init__(self, env, id, all_nodes):
        self.env = env
        self.id = id
        self.all_nodes = all_nodes
        self.store = simpy.Store(self.env)

    def put_data_with_latency(self, value, delay):
        yield self.env.timeout(delay)
        return self.store.put(value)

    def put_data(self, value, source_location):
        dest_location = self.all_nodes[self.id].location
        delay = get_transmission_delay(source_location, dest_location)
        return self.env.process(self.put_data_with_latency(value, delay))

    def get(self):
        return self.store.get()