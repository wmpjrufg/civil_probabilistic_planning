import numpy as np
import itertools
from pgmpy.factors.discrete import TabularCPD


def criar_cpt_termino(model, codigo, num_termino_states, termino_labels, params_discretizacao):
    t_node = f"T_{codigo}"
    d_node = f"D_{codigo}"
    
    activity_params = params_discretizacao[codigo]
    duration_labels = activity_params['labels']
    num_duration_states = len(duration_labels)

    parents = sorted(list(model.predecessors(t_node)))
    
    evidence = parents
    evidence_card = []
    state_names = {t_node: termino_labels}
    
    t_parents = [p for p in parents if p.startswith('T_')]
    
    for parent in parents:
        if parent.startswith('T_'):
            evidence_card.append(num_termino_states)
            state_names[parent] = termino_labels
        else:
            parent_code = parent.split('_')[1]
            parent_labels = params_discretizacao[parent_code]['labels']
            evidence_card.append(len(parent_labels))
            state_names[parent] = parent_labels
            
    parent_state_combinations = itertools.product(*[range(card) for card in evidence_card])
    values = np.zeros((num_termino_states, np.prod(evidence_card)))
    
    for col_idx, combo in enumerate(parent_state_combinations):
        state_map = dict(zip(parents, combo))
        t_parent_states_indices = [state_map[p] for p in t_parents]
        max_of_t_parents = max(t_parent_states_indices) if t_parent_states_indices else -1
        
        d_state_index = state_map[d_node]
        d_state_value = params_discretizacao[codigo]['labels'][d_state_index] # Pega o valor real do dia
        
        # A lógica da soma agora usa valores de dias, não mais índices
        # Se T_A terminou na fase 5, e D_B dura 3 dias, T_B termina na fase 8
        result_state = min(max_of_t_parents + d_state_value, num_termino_states - 1)
        
        values[result_state, col_idx] = 1
        
    return TabularCPD(variable=t_node, variable_card=num_termino_states, values=values,
                      evidence=evidence, evidence_card=evidence_card, state_names=state_names)