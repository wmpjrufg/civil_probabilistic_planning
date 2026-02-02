from io import BytesIO
import io
import warnings
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from caminho_critico_node import max_path_dag_node_weights
from generate_direct_graph import generate_graph
from probabilist_project_plan import generate_samples
from var_cvar import value_at_risk, conditional_value_at_risk

from complex_network.discretize_samples import discretize_by_whole_days
from complex_network.create_bayesian_network import build_generic_bayesian_network
from pgmpy.inference import VariableElimination

warnings.filterwarnings("ignore", category=RuntimeWarning, module="torch._classes")

try:
    from networkx.drawing.nx_pydot import graphviz_layout
except ImportError:
    st.error("The graphviz module is not installed. Install it with: pip install pygraphviz or pydot.")

# Função auxiliar para limpar números (ex: 1.000,00 -> 1000.00)
def safe_float_conversion(val):
    if pd.isna(val) or val == "NA":
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        # Remove pontos de milhar e troca vírgula decimal por ponto
        clean_val = val.replace('.', '').replace(',', '.')
        try:
            return float(clean_val)
        except ValueError:
            return np.nan
    return np.nan

st.title("Probabilistic Project Planning")

# --------------------------------------------------------------------
# 1. UPLOAD E LEITURA INICIAL
# --------------------------------------------------------------------
uploaded_file = st.file_uploader("Upload the Excel file with project data", type=["xlsx"])

if uploaded_file is not None:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names

    # Seleção da aba de Cronograma (Grafo)
    st.subheader("1. Schedule Data")
    selected_sheet = st.selectbox("Select the sheet with Schedule/Graph Data:", sheet_names, index=0)
    df = pd.read_excel(xls, sheet_name=selected_sheet)
    
    # Seleção da aba de Custos (Budget)
    st.subheader("2. Budget Data")
    budget_sheet = st.selectbox("Select the sheet with Cost/Budget Data:", sheet_names, index=0 if len(sheet_names) == 1 else 1, key="budget_selector")
    df_cost = pd.read_excel(xls, sheet_name=budget_sheet)

else:
    st.warning("Please upload an Excel file containing the Graph (.xlsx)")
    st.stop()

# --------------------------------------------------------------------
# 2. GERAÇÃO DE AMOSTRAS DE TEMPO (UPDATED)
# --------------------------------------------------------------------
distribuicao = "triangular"
n = 10000  # Número fixo de amostras para performance

# Gera amostras de tempo (Durações)
df_amostras = generate_samples(df, distribuicao, n)

st.header("Activity Parameters & Statistics")
col1, col2 = st.columns(2)
with col1:
    st.write("**Schedule Input:**")
    st.dataframe(df)
with col2:
    st.write("**Simulated Time Stats:**")
    st.dataframe(df_amostras.describe().T)

# --- PRE-CALCULATION: PROJECT MAKESPAN FOR GLOBAL COSTS ---
# We need the total project time (Makespan) to calculate time-dependent global costs
# (like Engineers who work the whole duration) before running the Budget analysis.
simulated_makespans = np.zeros(n)
try:
    # Build a temporary graph for calculation
    G_calc = nx.DiGraph()
    for _, row in df.iterrows():
        G_calc.add_node(row['Code'])
        if row['Predecessors'] != '-':
            for pred in str(row['Predecessors']).split(','):
                G_calc.add_edge(pred.strip(), row['Code'])
    
    # Auto-detect start and end nodes
    starts = [n for n, d in G_calc.in_degree() if d == 0]
    ends = [n for n, d in G_calc.out_degree() if d == 0]
    
    if starts and ends:
        s_node, e_node = starts[0], ends[0]
        # Run simplified simulation for makespan
        for i in range(n):
            pesos = {code: df_amostras.at[i, code] for code in df['Code']}
            res = max_path_dag_node_weights(G_calc, pesos, s_node, e_node)
            simulated_makespans[i] = res['peso_total']
except Exception as e:
    st.warning(f"Could not pre-calculate global project time: {e}")

# --------------------------------------------------------------------
# 3. ANÁLISE FINANCEIRA (BUDGET SAMPLING)
# --------------------------------------------------------------------
st.markdown("---")
st.header("💰 Financial Analysis")

if df_cost is not None and not df_cost.empty:
    try:
        total_project_costs = np.zeros(n)
        
        # Helper to identify variable rate columns if they exist
        col_cost_var = next((c for c in df_cost.columns if c.lower() in ['variable', 'rate', 'taxa', 'hourly']), None)

        for _, row in df_cost.iterrows():
            code = row['Code']
            
            # Get Base Cost (usually Fixed or Rate)
            # Adapts to your sheet having "Costs" as the main column
            raw_cost = safe_float_conversion(row.get('Costs', row.get('Cost', 0)))
            if pd.isna(raw_cost): raw_cost = 0.0

            # Get Explicit Variable Rate if exists (optional column)
            var_rate = 0.0
            if col_cost_var:
                val = safe_float_conversion(row[col_cost_var])
                if not pd.isna(val): var_rate = val

            # --- COST CALCULATION LOGIC ---
            if code in df_amostras.columns:
                # CASE A: Task-Specific Cost
                # Calculates cost based on the specific duration of THIS task (e.g. Activity A)
                durations = df_amostras[code].values 
                item_costs = raw_cost + (var_rate * durations)
                
            else:
                # CASE B: Global/Resource Cost (e.g., Engineers, Management)
                # If the code is not a specific task, we assume it's a global resource.
                # If it has a cost value, we treat that value as a RATE dependent on TOTAL PROJECT TIME.
                # This fixes the issue where Engineers were treated as fixed costs.
                if raw_cost > 0:
                    item_costs = raw_cost * simulated_makespans
                else:
                    item_costs = np.full(n, raw_cost)

            total_project_costs += item_costs

        # --- Visualização dos Custos ---
        cost_col1, cost_col2 = st.columns([2, 1])
        
        with cost_col1:
            fig_cost, ax_cost = plt.subplots(figsize=(10, 5))
            ax_cost.hist(total_project_costs, bins=50, color='#85bb65', edgecolor='black', alpha=0.7, density=True)
            ax_cost.set_title("Project Total Cost Distribution")
            ax_cost.set_xlabel("Total Cost ($)")
            ax_cost.set_ylabel("Density")
            st.pyplot(fig_cost)
            
        with cost_col2:
            st.write("**Cost Statistics:**")
            stats_df = pd.DataFrame(total_project_costs, columns=["Total Cost"]).describe()
            st.dataframe(stats_df)
            
        # --- VaR e CVaR Financeiro ---
        st.subheader("Financial Risk (VaR & CVaR)")
        confidence_level_cost = st.slider("Select Confidence Level for Cost:", 0.90, 0.99, 0.95, 0.01)
        
        var_cost = value_at_risk(total_project_costs, confidence_level=confidence_level_cost)
        cvar_cost = conditional_value_at_risk(total_project_costs, confidence_level=confidence_level_cost)
        
        m1, m2 = st.columns(2)
        m1.metric(f"Cost VaR ({confidence_level_cost*100:.0f}%)", f"$ {var_cost:,.2f}")
        m2.metric(f"Cost CVaR ({confidence_level_cost*100:.0f}%)", f"$ {cvar_cost:,.2f}")

    except Exception as e:
        st.error(f"Error calculating costs: {e}")
else:
    st.info("Upload a file with valid Cost data to see Financial Analysis.")


# --------------------------------------------------------------------
# 4. ANÁLISE DO GRAFO E CAMINHO CRÍTICO
# --------------------------------------------------------------------
st.markdown("---")
st.header("Graph & Critical Path Analysis")

# Criar o grafo direcionado para visualização
G = nx.DiGraph()
G.graph['graph'] = {'rankdir': 'LR'}

for _, row in df.iterrows():
    G.add_node(row['Code'], label=row['Task Name'])
    if row['Predecessors'] != '-':
        predecessors = str(row['Predecessors']).split(',')
        for pred in predecessors:
            G.add_edge(pred.strip(), row['Code'])

nos_finais_grafo = [n for n, d in G.out_degree() if d == 0]
if not nos_finais_grafo:
    st.error("Could not find an end node in the project graph.")
    st.stop()

no_final_projeto = nos_finais_grafo[0]
atividade_para_codigo = {f"{row['Task Name']} ({row['Code']})": row['Code'] for _, row in df.iterrows()}
opcoes = list(atividade_para_codigo.keys())

# Tentativa de selecionar padrão
try:
    valor_default = [k for k, v in atividade_para_codigo.items() if v == no_final_projeto][0]
    idx_default = opcoes.index(valor_default)
except:
    idx_default = 0

col_g1, col_g2 = st.columns(2)
start_node_name = col_g1.selectbox("Start Node:", opcoes)
end_node_name = col_g2.selectbox("End Node:", opcoes, index=idx_default)

if st.button("Generate Critical Path Analysis"):
    caminhos_encontrados = []
    tempos_caminho_critico = []
    
    start_code = atividade_para_codigo[start_node_name]
    end_code = atividade_para_codigo[end_node_name]

    progress_bar = st.progress(0)
    
    # Check if we can reuse the pre-calculated makespans to save time
    # We only reuse if the user selects the auto-detected start/end nodes
    reuse_calc = False
    if 's_node' in locals() and 'e_node' in locals():
         if start_code == s_node and end_code == e_node and len(simulated_makespans) == n:
             reuse_calc = True
             tempos_caminho_critico = simulated_makespans.tolist()
             # We still need paths for the median visualization, so we run a partial simulation or full
             # For simplicity in this fix, we will run the loop again to get paths, 
             # but you could optimize this further.
    
    for i in range(n):
        pesos = {code: df_amostras.at[i, code] for code in df['Code']}
        
        try:
            caminho = max_path_dag_node_weights(G, pesos, start_code, end_code)
            caminhos_encontrados.append(caminho['caminho'])
            if not reuse_calc:
                tempos_caminho_critico.append(caminho['peso_total'])
        except:
            tempos_caminho_critico.append(np.nan)
        
        if i % 1000 == 0:
            progress_bar.progress(i / n)
            
    progress_bar.progress(100)

    st.session_state.df_resultado = pd.DataFrame({
        "Caminho Crítico": caminhos_encontrados,
        "Makespan": tempos_caminho_critico
    })

    st.subheader("Makespan Statistics")
    st.dataframe(st.session_state.df_resultado["Makespan"].describe().to_frame().T)

# --------------------------------------------------------------------
# 5. REDE BAYESIANA (DINÂMICA)
# --------------------------------------------------------------------
st.markdown("---")
st.header("Bayesian Network Analysis (Dynamic Inference)")

with st.spinner("Building Bayesian Network..."):
    # Discretiza e constrói BN apenas uma vez ou se mudar os dados
    if 'modelo_bayesiano' not in st.session_state or st.button("Rebuild Bayesian Network"):
        params_discretizacao = discretize_by_whole_days(df_amostras)
        st.session_state.params_discretizacao_bayesiano = params_discretizacao
        
        modelo_bayesiano = build_generic_bayesian_network(df, params_discretizacao)
        st.session_state.modelo_bayesiano = modelo_bayesiano
        st.session_state.no_final_projeto_bayesiano = no_final_projeto
        
        # Inferência inicial (sem evidências)
        inferencia = VariableElimination(modelo_bayesiano)
        res_inicial = inferencia.query(variables=[f"T_{no_final_projeto}"], show_progress=False)
        st.session_state.resultado_bayesiano = res_inicial

if "resultado_bayesiano" in st.session_state:
    res = st.session_state.resultado_bayesiano
    var_name = res.variables[0]
    states = res.state_names[var_name]
    probs = res.values
    
    # Plot distribuição inicial
    fig_bn, ax_bn = plt.subplots()
    ax_bn.bar(states, probs, color='coral', edgecolor='black')
    ax_bn.set_title("Probabilistic Completion Time (Bayesian Prior)")
    ax_bn.set_xlabel("Days")
    st.pyplot(fig_bn)

    # Formulário de Evidências
    st.subheader("Update Scenarios (What-if Analysis)")
    st.info("Set known durations for specific tasks to update the project completion forecast.")
    
    params = st.session_state.params_discretizacao_bayesiano
    evidence_values = {}
    
    cols = st.columns(3)
    idx = 0
    with st.form("bayes_form"):
        for code, p in params.items():
            task_name = df[df['Code'] == code]['Task Name'].values[0]
            opts = ["Unknown"] + list(p['labels'])
            val = cols[idx].selectbox(f"{task_name} ({code}) Duration:", opts, key=f"ev_{code}")
            if val != "Unknown":
                evidence_values[f"D_{code}"] = val
            idx = (idx + 1) % 3
        
        calc_bayes = st.form_submit_button("Update Probabilities")

    if calc_bayes and evidence_values:
        st.write(f"**Calculating scenario given:** {evidence_values}")
        model = st.session_state.modelo_bayesiano
        target = st.session_state.no_final_projeto_bayesiano
        
        try:
            infer = VariableElimination(model)
            res_cond = infer.query([f"T_{target}"], evidence=evidence_values, show_progress=False)
            
            c_states = res_cond.state_names[res_cond.variables[0]]
            c_probs = res_cond.values
            
            # Plot Comparativo
            fig_cond, ax_cond = plt.subplots()
            ax_cond.bar(c_states, c_probs, color='#9b59b6', edgecolor='black')
            ax_cond.set_title("Updated Completion Time Distribution")
            ax_cond.set_xlabel("Days")
            st.pyplot(fig_cond)
            
            # Estatísticas do cenário
            max_prob_idx = np.argmax(c_probs)
            st.success(f"Most probable completion time: **{c_states[max_prob_idx]} days** (Prob: {c_probs[max_prob_idx]:.2%})")
            
        except Exception as e:
            st.error(f"Inference error (contradictory evidence?): {e}")