import pandas as pd
import numpy as np
import networkx as nx
from caminho_critico_node import max_path_dag_node_weights
from probabilist_project_plan import generate_samples
from var_cvar import value_at_risk, conditional_value_at_risk
from complex_network.discretize_samples import discretize_by_whole_days
from complex_network.create_bayesian_network import build_generic_bayesian_network
from pgmpy.inference import VariableElimination

# --------------------------------------------------------------------
# UTILS & DATA CLEANING
# --------------------------------------------------------------------
def safe_float_conversion(val):
    """Converte strings financeiras/numéricas para float de forma segura."""
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

def load_excel_data(uploaded_file):
    """Carrega o arquivo Excel e retorna o objeto ExcelFile e nomes das abas."""
    xls = pd.ExcelFile(uploaded_file)
    return xls, xls.sheet_names

# --------------------------------------------------------------------
# SIMULAÇÃO DE TEMPO (MONTE CARLO)
# --------------------------------------------------------------------
def run_time_simulation(df_plan, n_samples=10000, distribution="triangular"):
    """Gera as amostras de tempo (Monte Carlo) para as atividades."""
    return generate_samples(df_plan, distribution, n_samples)

def calculate_simulated_makespans(df_plan, df_amostras, n_samples):
    """
    Pré-calcula a duração total do projeto (Makespan) para todas as simulações.
    Essencial para calcular custos de recursos globais (ex: Engenheiros).
    """
    simulated_makespans = np.zeros(n_samples)
    try:
        # Cria grafo temporário apenas para cálculo
        G_calc = nx.DiGraph()
        for _, row in df_plan.iterrows():
            G_calc.add_node(row['Code'])
            if row['Predecessors'] != '-':
                for pred in str(row['Predecessors']).split(','):
                    G_calc.add_edge(pred.strip(), row['Code'])
        
        # Auto-detecta nós de início e fim
        starts = [n for n, d in G_calc.in_degree() if d == 0]
        ends = [n for n, d in G_calc.out_degree() if d == 0]
        
        if starts and ends:
            s_node, e_node = starts[0], ends[0]
            # Roda simulação simplificada
            for i in range(n_samples):
                pesos = {code: df_amostras.at[i, code] for code in df_plan['Code']}
                res = max_path_dag_node_weights(G_calc, pesos, s_node, e_node)
                simulated_makespans[i] = res['peso_total']
            
            return simulated_makespans, s_node, e_node
    except Exception as e:
        print(f"Error calculating makespans: {e}")
        return np.zeros(n_samples), None, None
    
    return np.zeros(n_samples), None, None

# --------------------------------------------------------------------
# ANÁLISE FINANCEIRA
# --------------------------------------------------------------------
def calculate_project_costs(df_budget, df_indirect, df_amostras, simulated_makespans, n_samples):
    """
    Calcula o custo total e gera um relatório detalhado de como cada item foi processado.
    Lida com duas planilhas separadas com base na nova estrutura:
    1. df_budget: Custos diretos (fixos por tarefa).
    2. df_indirect: Custos indiretos (diários, multiplicados pela duração total do projeto).
    Retorna: (total_project_costs, df_breakdown)
    """
    total_project_costs = np.zeros(n_samples)
    breakdown_data = [] # Lista para guardar o relatório detalhado
    
    # --- 1. PROCESSAMENTO DOS CUSTOS DIRETOS (ABA BUDGET) ---
    if df_budget is not None and not df_budget.empty:
        for _, row in df_budget.iterrows():
            code = row.get('Code', row.get('Código', ''))
            task_name = row.get('Task Name', row.get('Name', ''))
            
            # Custo Base (Sempre Fixo nesta aba)
            raw_cost = safe_float_conversion(row.get('Costs', row.get('Cost', 0)))
            if pd.isna(raw_cost): raw_cost = 0.0

            # Como é custo direto fixo, o valor é o mesmo em todas as simulações
            item_costs = np.full(n_samples, raw_cost)

            # Soma ao custo total do projeto
            total_project_costs += item_costs
            
            # Adiciona ao relatório
            breakdown_data.append({
                "Code": code,
                "Task Name/Item": task_name,
                "Type": "Direct (Fixed)",
                "Base Cost/Rate": raw_cost,
                "Calculation": "Fixed Amount",
                "Avg Duration Used": None,
                "Avg Total Cost": item_costs.mean()
            })

    # --- 2. PROCESSAMENTO DOS CUSTOS INDIRETOS (ABA INDIRECT COSTS) ---
    if df_indirect is not None and not df_indirect.empty:
        # Tenta encontrar dinamicamente as colunas principais
        col_daily_cost = next((c for c in df_indirect.columns if 'diário' in c.lower() or 'daily' in c.lower()), 'Custo Total Diário($)')
        col_item_name = next((c for c in df_indirect.columns if 'item' in c.lower() or 'nome' in c.lower()), 'Item de Custo Indireto')
        col_code = next((c for c in df_indirect.columns if 'código' in c.lower() or 'code' in c.lower()), 'Código')

        for _, row in df_indirect.iterrows():
            code = row.get(col_code, '')
            item_name = row.get(col_item_name, '')
            
            # Pega o Custo Total Diário
            daily_rate = safe_float_conversion(row.get(col_daily_cost, 0))
            if pd.isna(daily_rate): daily_rate = 0.0

            # Custo Variável: Multiplica o custo diário pela duração de cada cenário (Makespan)
            item_costs = daily_rate * simulated_makespans

            # Soma ao custo total do projeto
            total_project_costs += item_costs
            
            # Adiciona ao relatório
            breakdown_data.append({
                "Code": code,
                "Task Name/Item": item_name,
                "Type": "Indirect (Time Dependent)",
                "Base Cost/Rate": daily_rate,
                "Calculation": "Daily Rate x Project Duration",
                "Avg Duration Used": simulated_makespans.mean(),
                "Avg Total Cost": item_costs.mean()
            })

    return total_project_costs, pd.DataFrame(breakdown_data)

def get_risk_metrics(data, confidence_level=0.95):
    """Retorna VaR e CVaR para um array de dados."""
    var = value_at_risk(data, confidence_level=confidence_level)
    cvar = conditional_value_at_risk(data, confidence_level=confidence_level)
    return var, cvar

# --------------------------------------------------------------------
# GRAFO E CAMINHO CRÍTICO
# --------------------------------------------------------------------
def build_graph(df_plan):
    """Constrói o objeto NetworkX DiGraph."""
    G = nx.DiGraph()
    G.graph['graph'] = {'rankdir': 'LR'}
    for _, row in df_plan.iterrows():
        G.add_node(row['Code'], label=row['Task Name'])
        if row['Predecessors'] != '-':
            predecessors = str(row['Predecessors']).split(',')
            for pred in predecessors:
                G.add_edge(pred.strip(), row['Code'])
    return G

def get_graph_nodes(df_plan):
    """Retorna dicionário de mapeamento Nome->Código e nós finais."""
    G = build_graph(df_plan) # Apenas para pegar estrutura
    ends = [n for n, d in G.out_degree() if d == 0]
    mapping = {f"{row['Task Name']} ({row['Code']})": row['Code'] for _, row in df_plan.iterrows()}
    return mapping, ends[0] if ends else None

def simulate_critical_paths(G, df_plan, df_amostras, start_code, end_code, n_samples, 
                           simulated_makespans=None, s_auto=None, e_auto=None):
    """
    Roda a simulação de caminho crítico detalhada para obter os caminhos (nós).
    Reutiliza os makespans pré-calculados se os nós coincidirem para otimizar.
    """
    caminhos_encontrados = []
    tempos_caminho_critico = []
    
    # Verifica se pode reutilizar o cálculo anterior
    reuse_calc = False
    if simulated_makespans is not None and s_auto and e_auto:
         if start_code == s_auto and end_code == e_auto and len(simulated_makespans) == n_samples:
             reuse_calc = True
             tempos_caminho_critico = simulated_makespans.tolist()

    # Loop principal (pode ser usado com barra de progresso no frontend se adaptado, 
    # mas aqui roda direto para simplificar a separação)
    for i in range(n_samples):
        pesos = {code: df_amostras.at[i, code] for code in df_plan['Code']}
        try:
            caminho = max_path_dag_node_weights(G, pesos, start_code, end_code)
            caminhos_encontrados.append(caminho['caminho'])
            if not reuse_calc:
                tempos_caminho_critico.append(caminho['peso_total'])
        except:
            tempos_caminho_critico.append(np.nan)
            
    return caminhos_encontrados, tempos_caminho_critico

# --------------------------------------------------------------------
# REDE BAYESIANA
# --------------------------------------------------------------------
def init_bayesian_model(df_plan, df_amostras):
    """Prepara a rede bayesiana e parâmetros."""
    params = discretize_by_whole_days(df_amostras)
    model = build_generic_bayesian_network(df_plan, params)
    return model, params

def run_bayesian_inference(model, target_node, evidence=None):
    """Executa a inferência na rede."""
    infer = VariableElimination(model)
    target_var = f"T_{target_node}"
    
    if evidence:
        return infer.query([target_var], evidence=evidence, show_progress=False)
    else:
        return infer.query([target_var], show_progress=False)



'''# função de expressão regular

# aplicar aqui no total time uma distribuição triangular min=0.8 * total_time, mode=total_time, max=1.2 * total_time
# gera 10 mil amostras

index, time
0, 111.11
1, 95
2, 130
3, 85
..
9999, 120


# custo exemplo U$ 1095 por dia
cost_fix = sum(df["type of cost"=='Construction'])
cost_var = sum(df["type of cost"=='by time'])
index, time, cost (cost_var * ['time'] + cost_fix)'''
