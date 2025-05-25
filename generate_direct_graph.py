import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from networkx.drawing.nx_pydot import graphviz_layout
import streamlit as st

# Cores
cor_inicio = '#0072B2'    # Azul escuro
cor_fim = '#E69F00'       # Laranja
cor_intermediario = '#999999'  # Cinza escuro
cor_critical = '#D55E00'  # Vermelho

def generate_graph(G, critical_path=None):
    try:
        pos = graphviz_layout(G, prog="dot")
    except ImportError:
        st.error("Erro: o módulo graphviz não está instalado. Instale com: pip install pygraphviz ou pydot.")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao aplicar layout do Graphviz: {e}")
        st.stop()

    # Identificar nós iniciais e finais
    nos_iniciais = [n for n, d in G.in_degree() if d == 0]
    nos_finais = [n for n, d in G.out_degree() if d == 0]

    fig, ax = plt.subplots(figsize=(12, 10))
    
    node_colors = []
    for node in G.nodes():
        if node in nos_iniciais:
            node_colors.append(cor_inicio)
        elif node in nos_finais:
            node_colors.append(cor_fim)
        else:
            node_colors.append(cor_intermediario)

    # Cores das arestas (vermelho para caminho crítico)
    edge_colors = []
    for u, v in G.edges():
        if critical_path and u in critical_path and v in critical_path:
            if critical_path.index(v) - critical_path.index(u) == 1:
                edge_colors.append(cor_critical)
            else:
                edge_colors.append("black")
        else:
            edge_colors.append("black")

    # Desenhar os nós
    nx.draw_networkx(
        G,
        pos,
        arrows=True,
        arrowstyle='-|>',
        arrowsize=20,
        node_color=node_colors,
        node_size=2000,
        edge_color=edge_colors,
        font_weight='bold',
        font_color='black',
        labels={node: f"{G.nodes[node]['label']}\n({G.nodes[node]['duration']})" for node in G.nodes},
        ax=ax
    )
    #Legendas
    legenda = [
        mpatches.Patch(color=cor_inicio, label='Nó Inicial'),
        mpatches.Patch(color=cor_fim, label='Nó Final'),
        mpatches.Patch(color=cor_intermediario, label='Nó Intermediário'),
        
        ]
    if critical_path:
        legenda.append(mlines.Line2D([], [], color=cor_critical, lw=2, label='Caminho Crítico'))

    ax.legend(handles=legenda, loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=3, frameon=False)

    ax.set_axis_off()
    plt.tight_layout()
    return fig