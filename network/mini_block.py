from network.block import Block


class MiniBlock(Block):
    """
    This class models the mini-block which is propagated by the leader of the shard to
    the Principal Committee for the final verification.
    """

    def __init__(self, id, transactions_list, params, leader_id):
        super().__init__(self, id, transactions_list, params)
        self.leader_id = leader_id