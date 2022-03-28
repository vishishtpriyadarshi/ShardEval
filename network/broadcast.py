from network.packet import Packet

def broadcast(env, object, object_type, source, neighbour_list, nodes, params):
    """
    Broadcast the object from the source to destination
    """
    if neighbour_list:
        if object_type == "Tx":
            # Broadcast a transaction to all neighbours
            for neighbour in neighbour_list:
                env.process(
                    nodes[neighbour].transaction_pool.put_transaction(object, nodes[source].location)
                )
            
            if params["verbose"]:
                print(
                    "%7.4f" % env.now
                    + " : "
                    + "%s added to tx-pool of %s"
                    % (object.id, neighbour_list)
                )

        else:
            # Broadcast Block to the network
            # OR Broadcast Tx-block to the shard nodes
            # OR Broadcast Mini-block to the Principal Committee members
            # OR Intra-committee broadcast Mini-block between the Principal Committee members
            events = []
            for neighbour in neighbour_list:
                source_location = nodes[neighbour].location
                packeted_object = Packet(source, object, neighbour)
                store = nodes[neighbour].pipes
                events.append(store.put_data(packeted_object, source_location))

            if params["verbose"]:
                debug_info = "Mini-block-voting-list" if isinstance(object, list) else object.id
                print(
                    "%7.4f" % env.now
                    + " : "
                    + "Node %s propagated %s %s to its neighbours %s" % (source, object_type, debug_info, neighbour_list)
                )
                
            return env.all_of(events)
        