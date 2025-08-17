import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from caminho_critico_node import max_path_dag_node_weights
from generate_direct_graph import generate_graph
from var_cvar import value_at_risk, conditional_value_at_risk
from parepy_toolbox import random_sampling

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
# Calculando distribuições

if "Distribuição" not in df.columns or pd.isna(df.loc[0, "Distribuição"]):
    st.warning("Por favor, selecione uma aba válida que contenha a coluna 'Distribuição' com valor.")
    st.stop()

distribuicao = df.loc[0, "Distribuição"]


# Número de amostras
n = st.number_input(label="Digite o número de amostras:", min_value=0, step=1, format="%d")
if n is None or n <= 0:
    st.warning("Por favor, insira um número inteiro positivo de amostras.")
    st.stop()


samples = {}
params = {}
# Calculando distribuição triangular
if distribuicao == "triangular":
    params = {
        row["Código"]: {
            "min": float(p[0]),
            "mode": float(p[1]),
            "max": float(p[2]),
        }
        for _, row in df.iterrows()
        for p in [row["Parâmetros"].split(",")]
    }
# Calculando distribuição normal
elif distribuicao == "normal":
    params = {
        row["Código"]: {
            "mean": float(p[0]),
            "std": float(p[1]),
        }
        for _, row in df.iterrows()
        for p in [row["Parâmetros"].split(",")]
    }
else: 
    print("Distribuição não suportada")

# Geração das amostras
for k, p in params.items():
    samples[k] = random_sampling(
        dist=distribuicao,
        parameters=p,
        method='lhs',
        n_samples=n
    )

# Converter amostras para DataFrame
df_amostras = pd.DataFrame(samples)
# --------------------------------------------------------------------

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
            G.nodes[codigo]['Durações'] = df_amostras.at[i, codigo] #atribui o valor de cada atividade naquela amostra ao grafo
        
        try:
            pesos = {codigo: G.nodes[codigo]['Durações'] for codigo in G.nodes}
            caminho = max_path_dag_node_weights(G, pesos, atividade_para_codigo[start_node], atividade_para_codigo[end_node])
            caminhos_encontrados.append(" → ".join(caminho['caminho']))
            tempos_caminho_critico.append(caminho['peso_total'])
        except Exception as e:
            caminhos_encontrados.append("Erro")
            tempos_caminho_critico.append(np.nan)


    st.session_state.df_resultado = pd.DataFrame({
        "Caminho Crítico": caminhos_encontrados,
        "Tempo Total": tempos_caminho_critico
    })

    st.subheader("Caminho Crítico por Amostra")
    st.dataframe(st.session_state.df_resultado)

    st.subheader("Estatísticas do Tempo Total do Caminho Crítico")
    st.dataframe(st.session_state.df_resultado["Tempo Total"].describe().to_frame())

if "df_resultado" in st.session_state:
    df_resultado = st.session_state.df_resultado
    st.title("Histograma")
    tempos_finais = df_resultado["Tempo Total"].tolist()
    fig, ax = plt.subplots()
    ax.hist(tempos_finais, bins=30, color='skyblue', edgecolor='black', density=True)
    ax.set_title("Distribuição do tempo total")
    ax.set_xlabel("Valor")
    ax.set_ylabel("Densidade")

    st.pyplot(fig)

    confidence_level = st.number_input("Digite a taxa de confiança:", min_value=0.00, max_value=1.00, step=0.01, format="%.2f")
    if(confidence_level <= 0.00):
        st.warning("Digite uma taxa de confiança para calcular o Var e Cvar")
        st.stop()
    var = value_at_risk(tempos_finais, confidence_level=confidence_level)

    cvar = conditional_value_at_risk(tempos_finais,confidence_level=confidence_level)

    # st.write(f"Em {confidence_level*100}% de confiança o var é de {var:.2f} e o cvar é de {cvar:.2f}")
    st.write(f"Com {confidence_level*100}% de confiança, o tempo da obra não excederá {var:.2f} dias. Nos cenários restante e não otimistas, o atraso médio será de {cvar:.2f} dias.")
