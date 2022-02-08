def broadcast(env, object, object_type, source, neighbour_list, nodes, params, vote=""):
    """
    Broadcast the object from the source to destination
    """

    if object_type == "Tx":
        # Broadcast a transaction to all neighbours
        for neighbour in neighbour_list:
            env.process(
                nodes[neighbour].transaction_pool.put_transaction(object, nodes[source].location)
            )

    elif object_type == "Tx-block" or object_type == "Mini-block-consensus" or object_type == "Mini-block":
        # Broadcast Tx-block to the shard nodes
        # OR Broadcast Mini-block to the Principal Committee members
        # OR Intra-committee broadcast Mini-block between the Principal Committee members
        events = []
        for neighbour in neighbour_list:
            source_location = nodes[neighbour].location
            store = nodes[neighbour].pipes
            events.append(store.put_data(object, source_location))

        if params["verbose"]:
            print(
                "%7.4f" % env.now
                + " : "
                + "Node %s propagated %s %s" % (source, object_type, object.id)
            )
        return env.all_of(events)