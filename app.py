import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from caminho_critico_node import max_path_dag_node_weights
from generate_direct_graph import generate_graph

# PROBABILISTIC

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

# --------------------------------------------------------------------
# Calculando distribuição triangular

df[['min', 'mode', 'max']] = df['Parâmetros'].str.split(',', expand=True).astype(float)

# Número de amostras
n = 1000

# Gerar DataFrame com amostras
samples = {}

for _, row in df.iterrows():
    if row['Distribuição'] == 'triangular':
        samples[row['Código']] = np.random.triangular(
            left=row['min'], mode=row['mode'], right=row['max'], size=n
        )

# Converter para DataFrame
df_amostras = pd.DataFrame(samples)

# Exibir os dois DataFrames
st.subheader("Parâmetros das Atividades")
st.dataframe(df)

st.subheader(f"Amostras de Distribuições Triangulares (n={n})")
st.dataframe(df_amostras)

st.subheader("Estatísticas das Amostras")
st.dataframe(df_amostras.describe().T)


# Criar o grafo direcionado
G = nx.DiGraph()
G.graph['graph'] = {'rankdir': 'LR'}

# Adicionar nós e arestas no grafo
for _, row in df.iterrows():
    # Adiciona o nó (atividade)
    G.add_node(row['Código'], label=row['Atividade'])
    
    # Se houver predecessoras, adicionar aresta
    if row['Predecessoras'] != '-':
        predecessors = row['Predecessoras'].split(',')
        for pred in predecessors:
            G.add_edge(pred, row['Código'])

#Mostrar grafo
tempos_caminho_critico = []
caminhos_encontrados = []

#Selecionar nós para calcular caminho crítico
atividades = df["Atividade"].tolist()
atividade_para_codigo = {f"{row['Atividade']} ({row['Código']})": row['Código'] for _, row in df.iterrows()}
start_node = st.selectbox("Nó inicial para calcular caminho crítico:",list(atividade_para_codigo.keys()))
end_node = st.selectbox("Nó final para calcular caminha crítico:", list(atividade_para_codigo.keys()))
if st.button("Gerar Caminho Crítico"):
    for i in range(n):
        for codigo in df['Código']:
            G.nodes[codigo]['Durações'] = df_amostras.at[i, codigo]
        
        try:
            pesos = {codigo: G.nodes[codigo]['Durações'] for codigo in G.nodes}
            caminho = max_path_dag_node_weights(G, pesos, atividade_para_codigo[start_node], atividade_para_codigo[end_node])
            caminhos_encontrados.append(" → ".join(caminho['caminho']))
            tempos_caminho_critico.append(caminho['peso_total'])
        except Exception as e:
            caminhos_encontrados.append("Erro")
            tempos_caminho_critico.append(np.nan)


    df_resultado = pd.DataFrame({
        "Caminho Crítico": caminhos_encontrados,
        "Tempo Total": tempos_caminho_critico
    })

    st.subheader("Caminho Crítico por Amostra")
    st.dataframe(df_resultado)

    st.subheader("Estatísticas do Tempo Total do Caminho Crítico")
    st.dataframe(df_resultado["Tempo Total"].describe().to_frame())

