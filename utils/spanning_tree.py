class SpanningTree:
    """
    Spanning Tree class for efficient broadcast of the blocks
    """

    def __init__(self, nodes):
        self.V = len(nodes)         # No. of vertices
        self.graph = []             # Dictionary to store graph
        self.nodes = nodes

        for id, node in self.nodes.items():
            for neighbour_id in node.neighbours_ids:
                self.add_edge(node.id, neighbour_id, 1)

    def add_edge(self, u, v, w):
        """ Establishe edge from u to v with weight w """
        self.graph.append([u, v, w])

    def find(self, parent, i):
        """ Find set of an element i (uses path compression technique) """
        if parent[i] == i:
            return i
        return self.find(parent, parent[i])

    def union(self, parent, rank, x, y):
        """ Perform union of two sets of x and y (uses union by rank) """
        xroot = self.find(parent, x)
        yroot = self.find(parent, y)

        # Attach smaller rank tree under root of
        # high rank tree (Union by Rank)
        if rank[xroot] < rank[yroot]:
            parent[xroot] = yroot
        elif rank[xroot] > rank[yroot]:
            parent[yroot] = xroot

        # If ranks are same, then make one as root
        # and increment its rank by one
        else:
            parent[yroot] = xroot
            rank[xroot] += 1

    def Kruskal_MST(self):
        """ Perform Spanning Tree computation using Kruskal's algorithm """
        result = []     # Store the resultant MST

        # Step 1: Sort all the edges in non-decreasing order of their weight
        # Note - (not required in ShardEval)
        # self.graph = sorted(self.graph,
        # 					key=lambda item: item[2])

        parent, rank = {}, {}

        # Create V subsets with single elements
        for node_id in self.nodes:
            parent[node_id] = node_id
            rank[node_id] = 0

        i = 0   # An index variable, used for sorted edges
        e = 0   # An index variable, used for result[]

        # Number of edges to be taken is equal to V-1
        while e < self.V - 1:

            # Step 2: Pick the smallest edge and increment the index for next iteration
            u, v, w = self.graph[i]
            i += 1
            x = self.find(parent, u)
            y = self.find(parent, v)

            # If including this edge does't cause cycle, include it in result
            # and increment the indexof result for next edge
            if x != y:
                e += 1
                result.append([u, v, w])
                self.union(parent, rank, x, y)
            # Else discard the edge

        minimum_cost = 0
        network_info = {}
        for node_id in self.nodes:
            network_info[node_id] = set()

        for u, v, weight in result:
            minimum_cost += weight
            network_info[u].add(v)

        if minimum_cost != self.V - 1:
            raise RuntimeError("Spanning Tree has weighted edges.")

        return network_info