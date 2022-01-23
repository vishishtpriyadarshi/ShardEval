import string
import random

def generate_hash(k):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=k))


class Block:
    """
    This class models the block which is propagated by the Principal Committee to
    update the state of the Blockchain maintained by the nodes.
    """

    def __init__(self, id, transactions_list, params):
        self.params = params
        self.id = id
        self.transactions_list = transactions_list
        self.hash = self.id + "_" + generate_hash(10)