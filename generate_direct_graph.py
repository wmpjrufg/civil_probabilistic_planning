import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from networkx.drawing.nx_pydot import graphviz_layout
import streamlit as st

# Colors
START_NODE_COLOR = '#0072B2'    # Dark Blue
END_NODE_COLOR = '#E69F00'       # Orange
INTERMEDIATE_NODE_COLOR = '#999999'  # Dark Gray
CRITICAL_PATH_COLOR = '#D55E00'  # Vermilion (better for colorblindness than pure red)

def generate_graph(G: nx.DiGraph, critical_path: list = None) -> plt.Figure:
    """
    Generates a plot of the project graph, highlighting the critical path.

    This function takes a NetworkX DiGraph and an optional critical path, then
    creates a matplotlib Figure visualizing the project network. It colors nodes
    based on their role (start, end, intermediate) and highlights the edges
    and nodes belonging to the critical path.

    :param G: The NetworkX DiGraph object representing the project network.
              Nodes are expected to have 'label' and 'duration' attributes.
    :param critical_path: A list of node identifiers representing the critical path.
                          If provided, these nodes and their connecting edges will be
                          highlighted. Defaults to None.
    :return: A matplotlib Figure object containing the plotted graph.
    """
    try:
        pos = graphviz_layout(G, prog="dot")
    except ImportError:
        st.error(
            "Error: The graphviz layout module is not installed. "
            "Please install it with: `pip install pygraphviz` or `pip install pydot`."
        )
        st.stop()
    except Exception as e:
        st.error(f"Error applying Graphviz layout: {e}")
        st.stop()

    # Identify start and end nodes
    start_nodes = [n for n, d in G.in_degree() if d == 0]
    end_nodes = [n for n, d in G.out_degree() if d == 0]

    fig, ax = plt.subplots(figsize=(12, 10))
    
    node_colors = []
    for node in G.nodes():
        if node in start_nodes:
            node_colors.append(START_NODE_COLOR)
        elif node in end_nodes:
            node_colors.append(END_NODE_COLOR)
        else:
            node_colors.append(INTERMEDIATE_NODE_COLOR)

    # Edge colors (highlighting the critical path)
    edge_colors = []
    edge_widths = []
    for u, v in G.edges():
        if critical_path and u in critical_path and v in critical_path:
            # Check if the edge is part of the sequential critical path
            if critical_path.index(v) - critical_path.index(u) == 1:
                edge_colors.append(CRITICAL_PATH_COLOR)
                edge_widths.append(4)
            else:
                edge_colors.append("black")
                edge_widths.append(1.0)
        else:
            edge_colors.append("black")
            edge_widths.append(1.0)

    # Draw the graph
    nx.draw_networkx(
        G,
        pos,
        arrows=True,
        arrowstyle='-|>',
        arrowsize=20,
        node_color=node_colors,
        node_size=2000,
        edge_color=edge_colors,
        width=edge_widths,
        font_weight='bold',
        font_color='black',
        labels={node: f"{G.nodes[node]['label']}\n({G.nodes[node]['duration']})" for node in G.nodes},
        ax=ax
    )
    # Legends
    legend_handles = [
        mpatches.Patch(color=START_NODE_COLOR, label='Start Node'),
        mpatches.Patch(color=END_NODE_COLOR, label='End Node'),
        mpatches.Patch(color=INTERMEDIATE_NODE_COLOR, label='Intermediate Node'),
    ]
    if critical_path:
        legend_handles.append(mlines.Line2D([], [], color=CRITICAL_PATH_COLOR, lw=4, label='Critical Path'))

    ax.legend(handles=legend_handles, loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=4, frameon=False)

    ax.set_axis_off()
    plt.tight_layout()
    return fig