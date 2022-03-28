from network.block import Block


class CrossShardBlock(Block):
    """
    This class models the Cross-shard block which is propagated by the leader of the shard to
    the other shard leaders.
    """

    def __init__(self, id, transactions_list, params, shard_id, shard_nodes):
        super().__init__(id, transactions_list, params)
        self.id = id
        self.originating_shard_id = shard_id
        self.shard_votes_status = {}
        self.transactions_list = transactions_list        
        self.add_shard_info_for_voting(shard_id, shard_nodes)
    

    def add_shard_info_for_voting(self, shard_id, shard_nodes):
        """
        Adds initial shard info in preparation of voting -
            Initialisation of the dict containing vote of each node for every tx as -1
        """

        self.shard_votes_status[shard_id] = {}

        if shard_id == self.originating_shard_id:
            # cross-shard tx doesn't require voting from current shard
            return

        """
        In Cross-shard block the self.shard_votes_status var is an dict consisting of votes_status for each shard
        (compared to the Tx-block)
        """

        for tx in self.transactions_list:
            self.shard_votes_status[shard_id][tx.id] = {}
            for node_id in shard_nodes:
                self.shard_votes_status[shard_id][tx.id][node_id] = -1
                # -1 means votes has not been casted