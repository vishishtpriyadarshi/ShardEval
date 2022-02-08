import numpy as np
from scipy.stats import norm


class Consensus:
    _mu, _sigma = 0, 0

    def __init__(self, mu, sigma):
        self._mu = mu
        self._sigma = sigma

    def set_consensus_params(self, mu, sigma):
        self._mu = mu
        self._sigma = sigma     

    def get_random_number(self):
        return self._mu + self._sigma * np.random.randn()

    def get_consensus_time(self):
        delay = self.get_random_number() + 1
        if delay < 0:
            return self.get_consensus_time()
        return delay
    
    def get_consensus_probability(self):
        prob = 1 - norm(self._mu, self._sigma).cdf(0.5)
        return prob