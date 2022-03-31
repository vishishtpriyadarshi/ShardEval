from network.block import Block


class MiniBlock(Block):
    """
    This class models the mini-block which is propagated by the leader of the shard to
    the Principal Committee for the final verification.
    """

    def __init__(self, id, transactions_list, params, shard_id, generation_time):
        super().__init__(id, transactions_list, params)

        self.shard_id = shard_id
        self.publisher_info = {}
        # self.message_data = []
        self.message_data = {}
        self.generation_time = generation_time