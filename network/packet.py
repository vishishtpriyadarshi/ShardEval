class Packet:
    """
    This class models a wrapper for the exchange of the blocks, mini-blocks and tx-blocks.
    The wrapper wraps the underlying message with the other necessary information.
    """

    def __init__(self, sender, message, receiver):
        self.sender_id = sender
        self.message = message
        self.receiver_id = receiver