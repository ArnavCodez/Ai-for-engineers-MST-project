"""Shared settings for the whole project.

One place for the target, the allowed inputs, the forbidden columns, the seed
and the paths. Every notebook (and later the demo app) imports from here, so no
teammate can accidentally use a different column list.
"""
from pathlib import Path

# Folders (built from this file's location, so they work on every laptop)
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_CSV = PROJECT_DIR / "data" / "raw" / "measures_v2.csv"
PARQUET = PROJECT_DIR / "data" / "processed" / "measures_v2.parquet"
RESULTS_DIR = PROJECT_DIR / "outputs" / "results"
FIGURES_DIR = PROJECT_DIR / "outputs" / "figures"
MODELS_DIR = PROJECT_DIR / "outputs" / "models"
SPLIT_FILE = RESULTS_DIR / "split_profiles.json"

# Reproducibility
SEED = 42

# The data: one row every 0.5 s
SAMPLE_RATE_HZ = 2

# What we predict
TARGET = "stator_winding"

# Session ID: used ONLY to split the data, never as a model input
GROUP = "profile_id"

# The 8 measured signals a real motor controller has (the statement's parameters)
INPUTS = ["ambient", "coolant", "u_d", "u_q", "i_d", "i_q", "motor_speed", "torque"]

# Temperatures measured next to the winding: never model inputs (leakage, plan nuance N1)
FORBIDDEN = ["pm", "stator_tooth", "stator_yoke"]
