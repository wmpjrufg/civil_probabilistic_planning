import pandas as pd
from parepy_toolbox import random_sampling
import streamlit as st

def generate_samples(df: pd.DataFrame, distribution: str, n_samples: int) -> pd.DataFrame:
    """
    Generate activity duration samples based on a specified probability distribution.

    This function reads parameters from a DataFrame, builds parameter dictionaries
    for the 'triangular' or 'normal' distribution, and then generates 'n_samples'
    for each activity using Latin Hypercube Sampling (LHS).

    :param df: DataFrame containing the project activity data.
               It must include the 'Code' and 'Parameters' columns.
    :param distribution: The type of probability distribution to use ('triangular' or 'normal').
    :param n_samples: The number of samples to generate for each activity.

    :return: A pandas DataFrame where each column represents an activity (by its 'Code')
             and each row contains a sample of the activity duration.

    :raises st.error: If an unsupported distribution type is specified in the Excel file.
    """

    samples = {}
    params = {}
    # Calculate for triangular distribution
    if distribution == "triangular":
        params = {
            row["Código"]: {
                "min": float(p[0]),
                "mode": float(p[1]),
                "max": float(p[2]),
            }
            for _, row in df.iterrows()
            for p in [row["Parâmetros"].split(",")]
        }
    # Calculate for normal distribution
    elif distribution == "normal":
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

    # Generate samples
    for k, p in params.items():
        samples[k] = random_sampling(
            dist=distribution,
            parameters=p,
            method='lhs',
            n_samples=n_samples
        )

    # Convert samples to DataFrame
    return pd.DataFrame(samples)