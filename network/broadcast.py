def broadcast(env, object, object_type, source, neighbour_list, nodes):
    """
    Broadcasts the object from the source to destination
    """

    if object_type == "Tx":
        # Broadcast a transaction to all neighbours
        for neighbour in neighbour_list:
            env.process(
                nodes[neighbour].transaction_pool.put_transaction(object, nodes[source].location)
            )

    elif object_type == "Mini-block":
        # Broadcast Mini-block to the Principal Committee members
        print("[Propagation in Process]")