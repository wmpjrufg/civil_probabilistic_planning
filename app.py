import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from caminho_critico_node import max_path_dag_node_weights
from generate_direct_graph import generate_graph
from var_cvar import value_at_risk, conditional_value_at_risk
from parepy_toolbox import random_sampling
from complex_network.discretize_samples import discretizar_por_dias_inteiros
from complex_network.create_bayesian_network import construir_rede_bayesiana_generica
from pgmpy.inference import VariableElimination

# PROBABILISTIC

try:
    from networkx.drawing.nx_pydot import graphviz_layout
except ImportError:
    st.error("The graphviz module is not installed. Install it with: pip install pygraphviz or pydot.")

st.title("Probabilistic Project Planning")
# # Carregar os dados
uploaded_file = st.file_uploader("Upload the Excel file with project data", type=["xlsx"])

if uploaded_file is not None:
    # Carrega todas as planilhas disponíveis
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names

    # Permite o usuário selecionar a planilha
    selected_sheet = st.selectbox("Select the sheet:", sheet_names)

    # Lê a planilha selecionada
    df = pd.read_excel(xls, sheet_name=selected_sheet)

else:
    st.warning("Please upload an Excel file containing the Graph (.xlsx)")
    st.stop()

# --------------------------------------------------------------------
# Calculando distribuições

if "Distribuição" not in df.columns or pd.isna(df.loc[0, "Distribuição"]):
    st.warning("Please select a valid tab that contains the 'Distribution' column with value.")
    st.stop()

distribuicao = df.loc[0, "Distribuição"]


# Número de amostras
n = st.number_input(label="Enter the number of samples:", min_value=0, step=1, format="%d")
if n is None or n <= 0:
    st.warning("Please enter a positive integer number of samples.")
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
    st.error("Unsupported distribution specified in the Excel file.")

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
st.subheader("Activity parameters")
st.dataframe(df)

st.subheader(f"Sample Distributions (n={n})")
st.dataframe(df_amostras)

st.subheader("Sample Statistics")
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
start_node = st.selectbox("Starting node to calculate critical path:",list(atividade_para_codigo.keys()))
end_node = st.selectbox("End node to calculate critical path", list(atividade_para_codigo.keys()))
if st.button("Generate Critical Path"):
    for i in range(n):
        for codigo in df['Código']:
            G.nodes[codigo]['Durações'] = df_amostras.at[i, codigo] #atribui o valor de cada atividade naquela amostra ao grafo
        
        try:
            pesos = {codigo: G.nodes[codigo]['Durações'] for codigo in G.nodes}
            caminho = max_path_dag_node_weights(G, pesos, atividade_para_codigo[start_node], atividade_para_codigo[end_node])
            caminhos_encontrados.append(" → ".join(caminho['caminho']))
            tempos_caminho_critico.append(caminho['peso_total'])
        except Exception as e:
            caminhos_encontrados.append("Error")
            tempos_caminho_critico.append(np.nan)


    st.session_state.df_resultado = pd.DataFrame({
        "Caminho Crítico": caminhos_encontrados,
        "Tempo Total": tempos_caminho_critico
    })

    st.subheader("Critical Path by Sample")
    st.dataframe(st.session_state.df_resultado)

    st.subheader("Total Critical Path Time Statistics")
    st.dataframe(st.session_state.df_resultado["Tempo Total"].describe().to_frame())

if "df_resultado" in st.session_state:
    df_resultado = st.session_state.df_resultado
    st.header("Monte Carlo Simulation Results")
    tempos_finais = df_resultado["Tempo Total"].tolist()
    fig, ax = plt.subplots()
    ax.hist(tempos_finais, bins=30, color='skyblue', edgecolor='black', density=True)
    ax.set_title("Total time distribution")
    ax.set_xlabel("Value")
    ax.set_ylabel("Density")

    st.pyplot(fig)

    confidence_level = st.number_input("Enter the confidence rate:", min_value=0.00, max_value=1.00, step=0.01, format="%.2f")
    if(confidence_level <= 0.00):
        st.warning("Enter a confidence rate to calculate Var and Cvar")
        st.stop()
    var = value_at_risk(tempos_finais, confidence_level=confidence_level)

    cvar = conditional_value_at_risk(tempos_finais,confidence_level=confidence_level)

    # st.write(f"Em {confidence_level*100}% de confiança o var é de {var:.2f} e o cvar é de {cvar:.2f}")
    st.metric(label=f"Value at Risk (VaR) at {confidence_level*100:.0f}%", value=f"{var:.2f} days", help="The project duration will not exceed this value with the specified confidence.")
    st.metric(label=f"Conditional VaR (CVaR) at {confidence_level*100:.0f}%", value=f"{cvar:.2f} days", help="In the worst-case scenarios (beyond the VaR), this is the expected average project duration.")

# ------------------- REDE BAYESIANA -------------------
st.header("Bayesian Network Analysis")

if st.button("Analyze with Bayesian Network"):
    with st.spinner("Discretizing samples and building the Bayesian Network... This may take a few minutes."):
 
        params_discretizacao = discretizar_por_dias_inteiros(df_amostras)

        st.session_state.params_discretizacao_bayesiano = params_discretizacao

        modelo_bayesiano = construir_rede_bayesiana_generica(df, params_discretizacao)
        st.session_state.modelo_bayesiano = modelo_bayesiano

        nos_finais_grafo = [n for n, d in G.out_degree() if d == 0]
        if not nos_finais_grafo:
            st.error("Could not find an end node in the project graph.")
            st.session_state.clear()
            st.stop()
        
        # Assumindo um único nó final para simplificar
        no_final_projeto = nos_finais_grafo[0]
        st.info(f"Project end node identified for inference: T_{no_final_projeto}")

        inferencia = VariableElimination(modelo_bayesiano)
        resultado_inferencia = inferencia.query(variables=[f"T_{no_final_projeto}"], show_progress=False)

        st.session_state.resultado_bayesiano = resultado_inferencia
        st.session_state.no_final_projeto_bayesiano = no_final_projeto

if "resultado_bayesiano" in st.session_state:
    st.subheader("Bayesian Inference Result (Prior Probability)")
    resultado_inferencia = st.session_state.resultado_bayesiano
    no_final_projeto = st.session_state.no_final_projeto_bayesiano

    st.write(f"Probability distribution for project completion (T_{no_final_projeto}):")
    
    # Extrair valores e probabilidades para o histograma
    variable_name = resultado_inferencia.variables[0]
    tempos_bn = resultado_inferencia.state_names[variable_name]
    probabilidades_bn = resultado_inferencia.values

    fig_bn, ax_bn = plt.subplots()
    ax_bn.bar(tempos_bn, probabilidades_bn, color='coral', edgecolor='black')
    ax_bn.set_title("Total Time Distribution (Bayesian Network))")
    ax_bn.set_xlabel("Days to Completion")
    ax_bn.set_ylabel("Probability")
    st.pyplot(fig_bn)

    # --- Seção de Evidências ---
    st.subheader("Conditional Analysis with Evidence")
    st.write("Select the duration of one or more activities to see how it affects the project's end date.")

    params_discretizacao = st.session_state.params_discretizacao_bayesiano
    
    evidence_values = {}
    cols = st.columns(3)
    col_idx = 0
    
    with st.form(key='evidence_form'):
        for codigo, params in params_discretizacao.items():
            label = f"Duration of '{df[df['Código'] == codigo]['Atividade'].values[0]}'"
            # Adiciona uma opção para não especificar a evidência
            options = ["Not specified"] + params['labels']
            selected_value = cols[col_idx].selectbox(label, options=options, key=f"evidence_{codigo}")
            
            if selected_value != "Not specified":
                # O valor selecionado já é o estado correto (int)
                evidence_values[f"D_{codigo}"] = selected_value
            
            col_idx = (col_idx + 1) % 3
        
        submitted = st.form_submit_button("Analyze with Evidence")

    if submitted:
        if not evidence_values:
            st.warning("Please select at least one evidence value to run the conditional analysis.")
        else:
            st.spinner("Calculating inference with the provided evidence...")
            modelo_bayesiano = st.session_state.modelo_bayesiano
            no_final_projeto = st.session_state.no_final_projeto_bayesiano

            inferencia = VariableElimination(modelo_bayesiano)
            resultado_condicional = inferencia.query(
                variables=[f"T_{no_final_projeto}"],
                evidence=evidence_values,
                show_progress=False
            )

            st.write("Conditional Probability Distribution:")
            variable_name = resultado_condicional.variables[0]
            tempos_bn_cond = resultado_condicional.state_names[variable_name]
            probabilidades_bn_cond = resultado_condicional.values

            # st.bar_chart(pd.DataFrame(probabilidades_bn_cond, index=tempos_bn_cond))
            fig_bn, ax_bn = plt.subplots()
            ax_bn.bar(tempos_bn_cond, probabilidades_bn_cond, color='coral', edgecolor='black')
            ax_bn.set_title("Total Time Distribution (Bayesian Network)")
            ax_bn.set_xlabel("Days to Completion")
            ax_bn.set_ylabel("Probability")
            st.pyplot(fig_bn)
