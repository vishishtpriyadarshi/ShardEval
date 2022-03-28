from asyncio.windows_events import NULL


class Transaction:
    """
    This class models a transaction
    """

    def __init__(self, id, creation_time, value, reward, state, cross_shard_status=0):
        self.id = id
        self.creation_time = creation_time
        self.miningTime = 0
        self.value = value
        self.reward = reward
        self.state = {}
        self.cross_shard_status = cross_shard_status    # 0 - Intra-shard;  1 - Cross-shard
        self.receiver = None

    def display(self):
        print(self.id)
    
    def set_receiver(self, receiver_node_id):
        self.receiver = receiver_node_id