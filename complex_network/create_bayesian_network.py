import numpy as np
import networkx as nx
import pandas as pd
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD

from complex_network.create_cpt_final import create_completion_cpt


def build_generic_bayesian_network(project_df: pd.DataFrame, discretization_params: dict) -> DiscreteBayesianNetwork:
    """
    Builds a generic Bayesian Network for project planning based on activity dependencies and durations.

    This function creates a `pgmpy.DiscreteBayesianNetwork` where each activity is represented by two nodes:
    - A 'D' node (e.g., 'D_A') for the discretized duration of the activity.
    - A 'T' node (e.g., 'T_A') for the discretized completion time of the activity.

    The network structure is defined by the project's precedence constraints. The completion time of an
    activity ('T_node') depends on its own duration ('D_node') and the completion times of all its
    predecessors ('T_predecessor').

    :param project_df: A DataFrame containing project data, including 'Code' and 'Predecessors' columns.
    :param discretization_params: A dictionary with discretized duration data for each activity.
                                  Each entry should contain 'labels' (the possible duration values) and
                                  'probs' (their corresponding probabilities).

    :return: A `pgmpy.DiscreteBayesianNetwork` model representing the project, with all CPDs defined.
    """
    dependency_graph = nx.DiGraph()
    for _, row in project_df.iterrows():
        if row['Predecessoras'] != '-':
            for pred in row['Predecessoras'].split(','):
                dependency_graph.add_edge(pred, row['Código'])
    
    # Estimate the number of completion states required (sum of maximum durations on the longest path)
    max_duration_sum = 0
    if dependency_graph.nodes:
        path = nx.dag_longest_path(dependency_graph)
        max_duration_sum = sum(max(params['labels']) for code, params in discretization_params.items() if code in path) # type: ignore
    
    # Add a buffer to the number of states to avoid out-of-bounds issues
    num_completion_states = max_duration_sum + 5
    completion_labels = list(range(num_completion_states))
    print(f"\nCreating {num_completion_states} completion states (days) to cover all possibilities.\n")

    bayesian_model = DiscreteBayesianNetwork()
    for _, row in project_df.iterrows():
        activity_code = row['Código']
        bayesian_model.add_edge(f"D_{activity_code}", f"T_{activity_code}")
        if row['Predecessoras'] != '-':
            for pred in row['Predecessoras'].split(','):
                bayesian_model.add_edge(f"T_{pred}", f"T_{activity_code}")

    # First, create and add all duration CPDs (prior probabilities)
    duration_cpds = []
    for _, row in project_df.iterrows():
        activity_code = row['Código']
        params = discretization_params[activity_code]
        d_node = f"D_{activity_code}"
        prior_probs_array = np.array(params['probs']).reshape(len(params['labels']), 1)
        
        cpd_d = TabularCPD(variable=d_node, variable_card=len(params['labels']), 
                           values=prior_probs_array, state_names={d_node: params['labels']})
        duration_cpds.append(cpd_d)
    
    bayesian_model.add_cpds(*duration_cpds)

    # Then, create and add all completion time CPDs
    completion_cpds = []
    for _, row in project_df.iterrows():
        activity_code = row['Código']
        cpd_t = create_completion_cpt(bayesian_model, activity_code, num_completion_states, completion_labels, discretization_params)
        completion_cpds.append(cpd_t)
        
    bayesian_model.add_cpds(*completion_cpds)

    print(f"Is the model valid? {bayesian_model.check_model()}\n")
    return bayesian_model
