"""Small helpers to load our data and the frozen train/test split."""
import json

import pandas as pd

from src import config


def load_data():
    """Load the float32 parquet copy made by notebook 01 (row order = time order)."""
    return pd.read_parquet(config.PARQUET)


def load_split():
    """Return the frozen split as a dict with 'train_profiles' and 'test_profiles' lists.

    The split is made once in notebooks/02_eda.ipynb and saved to
    outputs/results/split_profiles.json. Everybody loads it from there and
    never draws a new one.
    """
    with open(config.SPLIT_FILE) as f:
        return json.load(f)


def train_rows(df, split):
    """Keep only the rows of training sessions (keeps the original row order)."""
    return df[df[config.GROUP].isin(split["train_profiles"])]
