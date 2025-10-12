from collections import defaultdict, deque
from typing import Any, Dict, List, Union


def max_path_dag_node_weights(graph: Dict[Any, List[Any]], node_weights: Dict[Any, float], start: Any, end: Any) -> Union[Dict[str, Any], str]:
    """
    Calculates the longest path in a Directed Acyclic Graph (DAG) with weights on the nodes.

    This algorithm is suitable for finding the critical path in project networks where activities
    are represented as nodes and their durations as node weights. It uses topological sorting
    to process nodes in a linear order, ensuring that all paths to a node are calculated
    before processing the node itself.

    :param graph: A dictionary representing the DAG, where keys are nodes and values are lists of their successors.
    :param node_weights: A dictionary mapping each node to its corresponding weight (e.g., duration).
    :param start: The starting node for the path search.
    :param end: The ending node for the path search.
    :return: A dictionary containing the total weight ('peso_total') and the path ('caminho') as a list of nodes,
             or a string message if no path exists from start to end.
    """
    # Topological Sort
    in_degree = defaultdict(int)
    topo_order = []
    queue = deque()

    for u in graph:
        for v in graph[u]:
            in_degree[v] += 1

    for u in graph:
        if in_degree[u] == 0:
            queue.append(u)

    while queue:
        u = queue.popleft()
        topo_order.append(u)
        for v in graph[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    # Initialization
    dist = {u: -float('inf') for u in graph}
    prev = {u: None for u in graph}
    dist[start] = node_weights[start]

    # Relaxation step
    for u in topo_order:
        for v in graph[u]:
            if dist[v] < dist[u] + node_weights[v]:
                dist[v] = dist[u] + node_weights[v]
                prev[v] = u

    # Path reconstruction
    path = []
    current = end
    if dist[end] == -float('inf'):
        return f"No path from {start} to {end}."

    while current is not None:
        path.append(current)
        current = prev[current]

    path.reverse()

    return {
        "peso_total": dist[end],
        "caminho": path
    }

# Example of a directed graph
# Example usage
graph = {
    'A': ['B', 'C'],
    'B': ['D'],
    'C': ['D'],
    'D': []
}

node_weights = {
    'A': 2,
    'B': 3,
    'C': 4,
    'D': 5
}

start_node = 'A'
end_node = 'D'

result = max_path_dag_node_weights(graph, node_weights, start_node, end_node)
print(result)
