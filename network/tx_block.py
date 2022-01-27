from network.block import Block


class TxBlock(Block):
    """
    This class models the Tx-block which is propagated by the leader of the shard to
    the shard nodes.
    """

    def __init__(self, id, transactions_list, params, shard_id):
        super().__init__(id, transactions_list, params)
        self.shard_id = shard_id