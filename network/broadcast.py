def broadcast(env, object, object_type, source, neighbour_list, nodes, params):
    """
    Broadcast the object from the source to destination
    """

    if object_type == "Tx":
        # Broadcast a transaction to all neighbours
        for neighbour in neighbour_list:
            env.process(
                nodes[neighbour].transaction_pool.put_transaction(object, nodes[source].location)
            )

    elif object_type == "Mini-block":
        # Broadcast Mini-block to the Principal Committee members
        print("[Mini-block]: Propagation in Process")

    elif object_type == "Tx-block":
        # Broadcast Tx-block to the shard nodes
        events = []
        for neighbour in neighbour_list:
            source_location = nodes[neighbour].location
            store = nodes[neighbour].pipes
            events.append(store.put_data(object, source_location))

        if params["verbose"]:
            print(
                "%7.4f" % env.now
                + " : "
                + "Node %s propagated Tx-block %s" % (source, object.id)
            )
        return env.all_of(events)