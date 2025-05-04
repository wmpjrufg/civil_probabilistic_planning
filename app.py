import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

# Carregar os dados
df = pd.read_excel("exemplo_aldo_dorea_pag170livro.xlsx")

# Título da aplicação
st.title("Visualização de Grafos direcionados")

# Criar o grafo direcionado
G = nx.DiGraph()

# Adicionar nós e arestas no grafo
for _, row in df.iterrows():
    # Adiciona o nó (atividade)
    G.add_node(row['Código'], label=row['Atividade'], duration=row['Durações'])
    
    # Se houver predecessoras, adicionar aresta
    if row['Predecessoras'] != '-':
        predecessors = row['Predecessoras'].split(',')
        for pred in predecessors:
            G.add_edge(pred, row['Código'])

# Definir o layout para o grafo
pos = nx.spring_layout(G, seed=3, k=0.15)

# Desenhar o grafo usando matplotlib
fig, ax = plt.subplots(figsize=(12, 10))  

# Desenhar os nós e as arestas
nx.draw(G, pos, with_labels=False, node_color="yellow", node_size=2000, font_size=12, font_weight='bold', arrows=True, ax=ax)

# Adicionar os rótulos das atividades (label) e a duração (duration) nos nós
labels = {node: f"{G.nodes[node]['label']}\n({G.nodes[node]['duration']})" for node in G.nodes}

# Exibir os rótulos no grafo
nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, font_color="black", font_weight="bold")

# Ajustar automaticamente o layout
plt.tight_layout()

# Mostrar o gráfico no Streamlit
st.pyplot(fig)
