import numpy as np
import pandas as pd


def discretize_by_whole_days(samples_df: pd.DataFrame) -> dict:
    """
    Discretizes activity duration samples by rounding them to the nearest whole day.

    This function takes a DataFrame of continuous duration samples for various project
    activities and converts them into a discrete probability distribution. Each unique
    rounded day becomes a discrete state, and its probability is determined by its
    frequency in the rounded samples.

    :param samples_df: A pandas DataFrame where each column represents an activity
                       and contains its continuous duration samples.
    :return: A dictionary where each key is an activity code. The value is another
             dictionary containing the discrete 'labels' (states), a 'value_map'
             from state to value, and their corresponding 'probs' (probabilities).
    """
    # 1. Round all samples to the nearest integer and convert to int
    rounded_df = np.round(samples_df).astype(int)
    
    discretization_params = {}
    print("\nDiscretizing by Whole Days (rounding):")

    for activity_code in rounded_df.columns:
        counts = rounded_df[activity_code].value_counts(normalize=True).sort_index()

        states = counts.index.tolist()
        probabilities = counts.values.tolist()
     
        value_map = {state: state for state in states}
        
        discretization_params[activity_code] = {
            'labels': states,
            'value_map': value_map,
            'probs': probabilities
        }
        print(f" - Activity {activity_code}: {len(states)} states -> {states}")
        
    return discretization_params