import numpy as np
import itertools
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD


def create_completion_cpt(model: DiscreteBayesianNetwork, activity_code: str, num_completion_states: int, completion_labels: list, discretization_params: dict) -> TabularCPD:
    """
    Creates the Conditional Probability Table (CPT) for an activity's completion time node.

    The completion time of an activity (`T_node`) is determined by the maximum completion time
    among all its predecessor activities, plus its own duration. This function builds a
    deterministic CPT that encodes this relationship.

    For each combination of parent states (predecessor completion times and own duration),
    it calculates the resulting completion time and assigns a probability of 1 to that
    specific state, with 0 for all others.

    :param model: The `pgmpy.DiscreteBayesianNetwork` model being constructed.
    :param activity_code: The code for the current activity (e.g., 'A').
    :param num_completion_states: The total number of discrete states for any completion time node.
    :param completion_labels: A list of labels for the completion time states (e.g., [0, 1, 2, ...]).
    :param discretization_params: A dictionary with discretized duration data for all activities.

    :return: A `pgmpy.factors.discrete.TabularCPD` object for the activity's completion time node.
    """
    t_node = f"T_{activity_code}"
    d_node = f"D_{activity_code}"
    
    # Identify all parent nodes for the current completion time node (T_node)
    parents = sorted(list(model.predecessors(t_node)))
    
    evidence = parents
    evidence_card = []
    state_names = {t_node: completion_labels}
    
    # Filter for parents that are also completion time nodes
    t_parents = [p for p in parents if p.startswith('T_')]
    
    for parent in parents:
        if parent.startswith('T_'):
            evidence_card.append(num_completion_states)
            state_names[parent] = completion_labels
        else:
            # This handles the duration node (D_node)
            parent_code = parent.split('_')[1]
            parent_labels = discretization_params[parent_code]['labels']
            evidence_card.append(len(parent_labels))
            state_names[parent] = parent_labels
            
    # Generate all possible combinations of parent states
    parent_state_combinations = itertools.product(*[range(card) for card in evidence_card])
    cpt_values = np.zeros((num_completion_states, np.prod(evidence_card)))
    
    for col_idx, combo in enumerate(parent_state_combinations):
        state_map = dict(zip(parents, combo))
        t_parent_states_indices = [state_map[p] for p in t_parents]
        # The start time is the maximum of the predecessors' completion times
        max_of_t_parents = max(t_parent_states_indices) if t_parent_states_indices else -1
        
        d_state_index = state_map[d_node]
        d_state_value = discretization_params[activity_code]['labels'][d_state_index]
        
        # Completion_Time = max(Predecessor_Completion_Times) + Own_Duration
        result_state = min(max_of_t_parents + d_state_value, num_completion_states - 1)
        
        # This is a deterministic CPT, so the probability is 1 for the calculated state
        cpt_values[result_state, col_idx] = 1
        
    return TabularCPD(variable=t_node, variable_card=num_completion_states, values=cpt_values,
                      evidence=evidence, evidence_card=evidence_card, state_names=state_names)