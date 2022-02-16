import sys
import json
import networkx as nx
import matplotlib.pyplot as plt
import re


def extract_nodes(line):
    nodes = []
    start_idx = 0

    while True:
        idx1 = int(line.find("'", start_idx))
        if idx1 == -1:
            return nodes

        idx2 = int(line.find("'", idx1 + 1))
        nodes.append(line[idx1 + 1 : idx2])

        start_idx = idx2 + 1


def create_graph(log_file):
    ct = 0

    network_info = {}
    network_info['principal_committee'] = {}
    pc_flag = 0

    with open(log_file, 'r') as f:
        for line in f:
            ct += 1
            if ct == 28:
                break
            
            if 'Principal Committee Nodes' in line:
                pc_flag = 1
                nodes = extract_nodes(line)
                network_info['principal_committee']['Leader'] = extract_nodes(next(f))
                for node in nodes:
                    network_info['principal_committee'][node] = extract_nodes(next(f))
            
            elif 'SHARD' in line:
                num_shard = re.findall(r'\d+', line)[0]
                shard_name = 'Shard_' + num_shard
                network_info[shard_name] = {}

                shard_nodes = extract_nodes(next(f))
                network_info[shard_name]['Leader'] = extract_nodes(next(f))

                next(f)     # Read a whitespace line
                for node in shard_nodes:
                    duplicate_free_nodes = set(extract_nodes(next(f)))
                    network_info[shard_name][node] = list(duplicate_free_nodes.difference(["-1"]))
       
    print(
        json.dumps(
            network_info,
            indent=4,
            separators=(',', ': ')
        )
    )
            
    G = nx.Graph()
    total_nodes = []
    for key, val in network_info.items():
        total_nodes += val.keys()
    
    total_nodes = list(set(total_nodes).difference(["Leader"]))
    G.add_nodes_from(total_nodes)
    leaders = []

    for key, val in network_info.items():
        for id, neighbours in val.items():
            if id == 'Leader':
                leaders.append(neighbours[0])
            else:
                for node in neighbours:
                    G.add_edge(id, node)
    
    color_map = []
    for node in G:
        if node in leaders:
            color_map.append('blue')
        else: 
            color_map.append('green')
    
    nx.draw(G, node_color=color_map, with_labels = True)

    idx = [m.start() for m in re.finditer(r"_", sys.argv[1])]
    filename = "network_graph_" + sys.argv[1][idx[2] + 1 : idx[4]]
    plt.savefig(f"analyzer/plots/{filename}.png")


def main():
    log_file = sys.argv[1]
    create_graph(log_file)

if __name__=="__main__":
    main()