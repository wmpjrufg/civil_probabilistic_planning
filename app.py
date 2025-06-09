import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from caminho_critico_node import max_path_dag_node_weights
from generate_direct_graph import generate_graph

try:
    from networkx.drawing.nx_pydot import graphviz_layout
except ImportError:
    st.error("O módulo graphviz não está instalado. Instale com: pip install pygraphviz ou pydot.")

st.title("Visualização de Grafos direcionados")
# # Carregar os dados
uploaded_file = st.file_uploader("Faça o upload do arquivo Excel para exibir o grafo", type=["xlsx"])

if uploaded_file is not None:
    # Carrega todas as planilhas disponíveis
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names

    # Permite o usuário selecionar a planilha
    selected_sheet = st.selectbox("Selecione a aba (sheet):", sheet_names)

    # Lê a planilha selecionada
    df = pd.read_excel(xls, sheet_name=selected_sheet)

else:
    st.warning("Por favor, faça o upload de um arquivo Excel contendo o Grafo (.xlsx)")
    st.stop()

# Criar o grafo direcionado
G = nx.DiGraph()
G.graph['graph'] = {'rankdir': 'LR'}

# Adicionar nós e arestas no grafo
for _, row in df.iterrows():
    # Adiciona o nó (atividade)
    G.add_node(row['Código'], label=row['Atividade'], duration=row['Durações'])
    
    # Se houver predecessoras, adicionar aresta
    if row['Predecessoras'] != '-':
        predecessors = row['Predecessoras'].split(',')
        for pred in predecessors:
            G.add_edge(pred, row['Código'])



#CALCULAR CAMINHO CRÍTICO
atividades = df["Atividade"].tolist()
atividade_para_codigo = {f"{row['Atividade']} ({row['Código']})": row['Código'] for _, row in df.iterrows()}
start_node = st.selectbox("Nó inicial para calcular caminho crítico:",list(atividade_para_codigo.keys()))
end_node = st.selectbox("Nó final para calcular caminha crítico:", list(atividade_para_codigo.keys()))
caminho_critico = {}


if st.button("Gerar Caminho Crítico"):
    caminho_critico =  max_path_dag_node_weights(G, df.set_index('Código')['Durações'].to_dict(), atividade_para_codigo[start_node], atividade_para_codigo[end_node])
    codigo_para_atividade = df.set_index('Código')['Atividade'].to_dict()
    atividades_caminho = [codigo_para_atividade[codigo] for codigo in caminho_critico['caminho']]
    caminho_str = " -> ".join(atividades_caminho)
   
    fig = generate_graph(G, critical_path=caminho_critico['caminho'])
    st.pyplot(fig)
    st.write("Caminho Crítico:", caminho_str)
    st.write("Peso Total:", caminho_critico['peso_total'])
else:
    fig = generate_graph(G)
    st.pyplot(fig)

