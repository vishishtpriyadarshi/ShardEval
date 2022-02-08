from network.consensus.consensus import Consensus

obj = Consensus(0, 1)
print(obj.get_consensus_time())

obj.set_consensus_params(1, 1)
print(obj.get_consensus_time())

print(obj.get_delay_probability())