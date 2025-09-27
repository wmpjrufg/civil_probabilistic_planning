import numpy as np
import networkx as nx
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD

from complex_network.create_cpt_final import criar_cpt_termino


def construir_rede_bayesiana_generica(df_projeto, params_discretizacao):
    G = nx.DiGraph()
    for _, row in df_projeto.iterrows():
        if row['Predecessoras'] != '-':
            for pred in row['Predecessoras'].split(','):
                G.add_edge(pred, row['Código'])
    
    # Estima o número de estados de término necessários (soma das durações máximas)
    max_duration_sum = 0
    if G.nodes:
        path = nx.dag_longest_path(G)
        max_duration_sum = sum(max(params['labels']) for code, params in params_discretizacao.items() if code in path)
    
    num_termino_states = max_duration_sum + 5
    termino_labels = list(range(num_termino_states)) 
    print(f"\nCriando {num_termino_states} estados de término (dias) para cobrir todas as possibilidades.\n")

    model = DiscreteBayesianNetwork()
    for _, row in df_projeto.iterrows():
        codigo = row['Código']
        model.add_edge(f"D_{codigo}", f"T_{codigo}")
        if row['Predecessoras'] != '-':
            for pred in row['Predecessoras'].split(','):
                model.add_edge(f"T_{pred}", f"T_{codigo}")

    all_cpds = []
    for _, row in df_projeto.iterrows():
        codigo = row['Código']
        params = params_discretizacao[codigo]
        d_node = f"D_{codigo}"
        prior_probs_array = np.array(params['probs']).reshape(len(params['labels']), 1)
        
        cpd_d = TabularCPD(variable=d_node, variable_card=len(params['labels']), 
                           values=prior_probs_array, state_names={d_node: params['labels']})
        all_cpds.append(cpd_d)
    
    # Adiciona as CPTs de Duração primeiro, para que a info esteja disponível
    model.add_cpds(*all_cpds)
    all_cpds = [] # Limpa a lista para adicionar as de término

    for _, row in df_projeto.iterrows():
        codigo = row['Código']
        cpd_t = criar_cpt_termino(model, codigo, num_termino_states, termino_labels, params_discretizacao)
        all_cpds.append(cpd_t)
        
    model.add_cpds(*all_cpds)

    print(f"Modelo Válido? {model.check_model()}\n")
    return model
