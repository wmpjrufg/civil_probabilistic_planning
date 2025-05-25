from collections import defaultdict, deque

def max_path_dag_node_weights(graph, node_weights, start, end):
    # Ordenação topológica
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

    # Inicialização
    dist = {u: -float('inf') for u in graph}
    prev = {u: None for u in graph}
    dist[start] = node_weights[start]

    # Relaxamento
    for u in topo_order:
        for v in graph[u]:
            if dist[v] < dist[u] + node_weights[v]:
                dist[v] = dist[u] + node_weights[v]
                prev[v] = u

    # Reconstrução do caminho
    path = []
    current = end
    if dist[end] == -float('inf'):
        return f"Nenhum caminho de {start} até {end}."

    while current is not None:
        path.append(current)
        current = prev[current]

    path.reverse()

    return {
        "peso_total": dist[end],
        "caminho": path
    }

# Exemplo de grafo direcionado
# Exemplo de uso
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

resultado = max_path_dag_node_weights(graph, node_weights, start_node, end_node)
print(resultado)
