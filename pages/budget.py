import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from generate_direct_graph import generate_graph
import warnings
import io

# Importa o Backend
import felipedanielpaulo as backend

warnings.filterwarnings("ignore", category=RuntimeWarning, module="torch._classes")

try:
    from networkx.drawing.nx_pydot import graphviz_layout
except ImportError:
    st.error("The graphviz module is not installed. Install it with: pip install pygraphviz or pydot.")

# Configuração da Página
st.set_page_config(page_title="Probabilistic Project Planning", layout="wide")
st.title("Probabilistic Project Planning")

# --------------------------------------------------------------------
# 1. UPLOAD E LEITURA INICIAL
# --------------------------------------------------------------------
uploaded_file = st.file_uploader("Upload the Excel file with project data", type=["xlsx"])

if uploaded_file is not None:
    xls, sheet_names = backend.load_excel_data(uploaded_file)

    st.subheader("Data Selection")
    col_sel1, col_sel2, col_sel3 = st.columns(3)
    
    # Tenta auto-selecionar os índices corretos pelo nome
    idx_plan = sheet_names.index('Plan') if 'Plan' in sheet_names else 0
    idx_budget = sheet_names.index('Budget') if 'Budget' in sheet_names else (1 if len(sheet_names) > 1 else 0)
    idx_indirect = sheet_names.index('Indirect costs') if 'Indirect costs' in sheet_names else (2 if len(sheet_names) > 2 else 0)

    # 1. Seleção da aba de Cronograma (Grafo)
    with col_sel1:
        selected_sheet = st.selectbox("1. Schedule (Plan) Sheet:", sheet_names, index=idx_plan)
        df = pd.read_excel(xls, sheet_name=selected_sheet)
    
    # 2. Seleção da aba de Custos Diretos (Budget)
    with col_sel2:
        budget_sheet = st.selectbox("2. Direct Costs (Budget) Sheet:", sheet_names, index=idx_budget)
        df_budget = pd.read_excel(xls, sheet_name=budget_sheet)

    # 3. Seleção da aba de Custos Indiretos
    with col_sel3:
        indirect_sheet = st.selectbox("3. Indirect Costs Sheet:", sheet_names, index=idx_indirect)
        df_indirect = pd.read_excel(xls, sheet_name=indirect_sheet)

else:
    st.warning("Please upload an Excel file containing the Project Data (.xlsx)")
    st.stop()

# --------------------------------------------------------------------
# 2. GERAÇÃO DE AMOSTRAS DE TEMPO & MAKESPAN GLOBAL
# --------------------------------------------------------------------
distribuicao = "triangular"
n = 10000  # Número fixo de amostras

# Backend: Gera amostras
df_amostras = backend.run_time_simulation(df, n_samples=n, distribution=distribuicao)

st.header("Activity Parameters & Statistics")
col1, col2 = st.columns(2)
with col1:
    st.write("**Schedule Input:**")
    st.dataframe(df)
with col2:
    st.write("**Simulated Time Stats:**")
    st.dataframe(df_amostras.describe().T)

# Backend: Pré-cálculo do Makespan (Duração total) para custos globais
simulated_makespans, s_node_auto, e_node_auto = backend.calculate_simulated_makespans(df, df_amostras, n)

# --------------------------------------------------------------------
# 3. ANÁLISE FINANCEIRA (BUDGET SAMPLING)
# --------------------------------------------------------------------
st.markdown("---")
st.header("💰 Financial Analysis")

if df_budget is not None:
    try:
        # Backend: Retorna custos totais E o relatório, usando as duas planilhas
        total_project_costs, df_breakdown = backend.calculate_project_costs(
            df_budget, df_indirect, df_amostras, simulated_makespans, n
        )

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
        
        # --- TABELA DE DETALHAMENTO ---
        st.subheader("📋 Cost Type Breakdown")
        st.caption("Detailed view of how Direct and Indirect costs were calculated.")
        
        # Formatação para ficar bonito
        st.dataframe(
            df_breakdown.style.format({
                "Base Cost/Rate": "$ {:.2f}",
                "Avg Total Cost": "$ {:.2f}",
                "Avg Duration Used": "{:.1f} days"
            }).background_gradient(subset=["Avg Total Cost"], cmap="Greens"),
            use_container_width=True
        )

        # --- VaR e CVaR Financeiro ---
        st.subheader("Financial Risk (VaR & CVaR)")
        confidence_level_cost = st.slider("Select Confidence Level for Cost:", 0.90, 0.99, 0.95, 0.01)
        
        var_cost, cvar_cost = backend.get_risk_metrics(total_project_costs, confidence_level_cost)
        
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

# Backend: Construção e dados do Grafo
G = backend.build_graph(df)
node_map, no_final_projeto = backend.get_graph_nodes(df)

if not no_final_projeto:
    st.error("Could not find an end node in the project graph.")
    st.stop()

opcoes = list(node_map.keys())

# Lógica de seleção default
try:
    valor_default = [k for k, v in node_map.items() if v == no_final_projeto][0]
    idx_default = opcoes.index(valor_default)
except:
    idx_default = 0

col_g1, col_g2 = st.columns(2)
start_node_name = col_g1.selectbox("Start Node:", opcoes)
end_node_name = col_g2.selectbox("End Node:", opcoes, index=idx_default)

if st.button("Generate Critical Path Analysis"):
    start_code = node_map[start_node_name]
    end_code = node_map[end_node_name]

    with st.spinner("Simulating critical paths..."):
        # Backend: Simulação de caminhos
        # Passamos os makespans calculados no início para otimizar caso os nós sejam os mesmos
        paths, times = backend.simulate_critical_paths(
            G, df, df_amostras, start_code, end_code, n,
            simulated_makespans=simulated_makespans, 
            s_auto=s_node_auto, e_auto=e_node_auto
        )

    # Armazena resultados na sessão
    st.session_state.df_resultado = pd.DataFrame({
        "Caminho Crítico": paths,
        "Makespan": times
    })

    st.subheader("Makespan Statistics")
    st.dataframe(st.session_state.df_resultado["Makespan"].describe().to_frame().T)

# --------------------------------------------------------------------
# 5. REDE BAYESIANA (DINÂMICA)
# --------------------------------------------------------------------
st.markdown("---")
st.header("Bayesian Network Analysis (Dynamic Inference)")

with st.spinner("Building Bayesian Network..."):
    # Constrói BN apenas se necessário
    if 'modelo_bayesiano' not in st.session_state or st.button("Rebuild Bayesian Network"):
        # Backend: Construção da BN
        model_bn, params_bn = backend.init_bayesian_model(df, df_amostras)
        
        st.session_state.params_discretizacao_bayesiano = params_bn
        st.session_state.modelo_bayesiano = model_bn
        st.session_state.no_final_projeto_bayesiano = no_final_projeto
        
        # Backend: Inferência inicial
        res_inicial = backend.run_bayesian_inference(model_bn, no_final_projeto)
        st.session_state.resultado_bayesiano = res_inicial

if "resultado_bayesiano" in st.session_state:
    res = st.session_state.resultado_bayesiano
    var_name = res.variables[0]
    states = res.state_names[var_name]
    probs = res.values
    
    # Plot inicial
    fig_bn, ax_bn = plt.subplots()
    ax_bn.bar(states, probs, color='coral', edgecolor='black')
    ax_bn.set_title("Probabilistic Completion Time (Bayesian Prior)")
    ax_bn.set_xlabel("Days")
    st.pyplot(fig_bn)

    # Formulário de Evidências (What-if)
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
            # Backend: Inferência condicional
            res_cond = backend.run_bayesian_inference(model, target, evidence=evidence_values)
            
            c_states = res_cond.state_names[res_cond.variables[0]]
            c_probs = res_cond.values
            
            # Plot Comparativo
            fig_cond, ax_cond = plt.subplots()
            ax_cond.bar(c_states, c_probs, color='#9b59b6', edgecolor='black')
            ax_cond.set_title("Updated Completion Time Distribution")
            ax_cond.set_xlabel("Days")
            st.pyplot(fig_cond)
            
            max_prob_idx = np.argmax(c_probs)
            st.success(f"Most probable completion time: **{c_states[max_prob_idx]} days** (Prob: {c_probs[max_prob_idx]:.2%})")
            
        except Exception as e:
            st.error(f"Inference error (contradictory evidence?): {e}")