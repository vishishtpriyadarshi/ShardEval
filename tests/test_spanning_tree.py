import numpy as np
from utils.spanning_tree import SpanningTree

class TestNode:
    def __init__(self, id, neighbours_ids):
        self.id = id
        self.neighbours_ids = neighbours_ids


num_nodes = 5
degree = num_nodes // 2 + 1
node_ids = [i for i in range(num_nodes)]

nodes = {}
for node_id in range(num_nodes):
    possible_neighbours = node_ids.copy()
    possible_neighbours.remove(node_id)

    neighbours = np.random.choice(
                    possible_neighbours,
                    size=degree,
                    replace=False
                )
    nodes[node_id] = TestNode(node_id, neighbours)
    print(f"Node {node_id} has neighbours - {neighbours}")

spanning_tree = SpanningTree(nodes)
network_info = spanning_tree.Kruskal_MST()

print("\n====== SPANNING TREE ======")
print(network_info)
