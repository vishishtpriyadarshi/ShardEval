import sys
import json
import re
import csv
from prettytable import PrettyTable

import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt


def get_file_suffix():
    idx = [m.start() for m in re.finditer(r"_", sys.argv[1])]
    return sys.argv[1][idx[2] + 1 : idx[4]]


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


def create_graph(log_file, verbose=False):
    ct = 0

    network_info = {}
    network_info['principal_committee'] = {}
    pc_flag = 0
    leaders = []

    with open(log_file, 'r') as f:
        for line in f:
            if 'Principal Committee Nodes' in line:
                pc_flag = 1
                nodes = extract_nodes(line)
                network_info['principal_committee']['Leader'] = extract_nodes(next(f))
                leaders.append(network_info['principal_committee']['Leader'][0])
                for node in nodes:
                    network_info['principal_committee'][node] = extract_nodes(next(f))
            
            elif 'SHARD' in line:
                num_shard = re.findall(r'\d+', line)[0]
                shard_name = 'Shard_' + num_shard
                network_info[shard_name] = {}

                shard_nodes = extract_nodes(next(f))
                network_info[shard_name]['Leader'] = extract_nodes(next(f))
                leaders.append(network_info[shard_name]['Leader'][0])

                next(f)     # Read a whitespace line
                for node in shard_nodes:
                    duplicate_free_nodes = set(extract_nodes(next(f)))
                    network_info[shard_name][node] = list(duplicate_free_nodes.difference(["-1"]))

    if verbose:   
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
    for node in total_nodes:
        c = 'blue' if node in leaders else 'green'
        G.add_node(node, color=c)

    for key, val in network_info.items():
        for id, neighbours in val.items():
            if id != 'Leader':
                for node in neighbours:
                    G.add_edge(id, node)
    
    nx.draw(G, with_labels = True)

    filename = "network_graph_" + get_file_suffix()
    print(f"Saving static graph in file 'logs_data/plots/{filename}.png'\n")
    plt.savefig(f"logs_data/plots/{filename}.png")

    vis_net = Network(height='750px', width='100%')
    vis_net.from_nx(G)
    # vis_net.show_buttons(filter_=['physics'])
    print(f"Saving interactive graph in file 'logs_data/interactive_plots/{filename}.html'\n")
    vis_net.save_graph(f"logs_data/interactive_plots/{filename}.html")


def analyse_tx_blocks(log_file):
    relevant_lines = []
    ids = set()
    keywords = ['propagated', 'received', 'voted']

    with open(log_file, 'r') as f:
        for line in f:
            res = re.search('TB_FN[0-9]+_[0-9]+', line)
            if res:
                relevant_lines.append(line)
                ids.add(line[res.start() : res.end()])
    
    filename = "metadata_" + get_file_suffix()
    col_names = ['Tx-Block ID', 'Timestamp', 'Sender', 'Receiver']

    print(f"Preparing csv file 'logs_data/metadata/{filename}.csv'\n")
    writer = csv.writer(open(f"logs_data/metadata/{filename}.csv", 'w'))
    writer.writerow(col_names)
    pt = PrettyTable()
    pt.field_names = col_names

    for id in ids:
        writer.writerow([id, '', '', ''])
        pt.add_row([id, '', '', ''])
        for line in relevant_lines:
            if id in line:
                timestamp = line[0 : line.find(':') - 1]
                # print(timestamp)
                receiver, sender = None, None
                if keywords[0] in line:
                    receiver = extract_nodes(line)
                    sender = line[line.find('Node') + 4 : line.find('propagated') - 1]
                elif keywords[1] in line:
                    receiver = line[line.find('Node') + 4 : line.find('received') - 1]
                    sender = "[voted block]" if line.find('from') == -1 else line[line.find('from') + 4 : line.find('\n')]
                else:
                    continue

                writer.writerow(['', timestamp, sender, receiver])
                pt.add_row(['', timestamp, sender, receiver])

    print(f"Writing metadata in file 'logs_data/metadata/{filename}.txt'\n")
    with open(f"logs_data/metadata/{filename}.txt", "w") as text_file:
        text_file.write(pt.get_string())


def main():
    log_file = sys.argv[1]
    create_graph(log_file)
    analyse_tx_blocks(log_file)
    

if __name__=="__main__":
    main()