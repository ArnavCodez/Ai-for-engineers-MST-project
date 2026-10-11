"""Streamlit demo: recorded-data replay of the winding-temperature virtual sensor.

Run from the repo root (venv active):
    streamlit run app.py

It replays one of the 6 test sessions. The real sensor value is shown ONLY for
comparison; the model's inputs are the 45 features from src/features.py.

Two modes:
- live model: needs data/processed/features.parquet (notebook 03) and the saved
  model (notebook 04). The app runs the model on the chosen session.
- fallback: if those files are missing, it replays the predictions saved in
  outputs/results/test_predictions.csv (made once in notebook 05).
"""
import json
import time

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from src import config
from src.data import load_split

FEATURES_FILE = config.PROJECT_DIR / "data" / "processed" / "features.parquet"


@st.cache_data
def load_json(name):
    with open(config.RESULTS_DIR / name) as f:
        return json.load(f)


@st.cache_resource
def load_model(path):
    return joblib.load(path)


@st.cache_data
def session_from_features(profile_id, feature_names):
    df = pd.read_parquet(FEATURES_FILE, columns=[config.GROUP, config.TARGET] + feature_names,
                         filters=[(config.GROUP, "==", profile_id)])
    return df


@st.cache_data
def saved_predictions():
    return pd.read_csv(config.RESULTS_DIR / "test_predictions.csv")


st.set_page_config(page_title="Winding temperature virtual sensor", layout="wide")
st.title("Virtual winding-temperature sensor")
st.caption("Recorded-data replay of a held-out test session (Paderborn PMSM test bench, Kaggle dataset v3). "
           "Not connected to a real motor. GE Power Systems is the assignment scenario.")

metadata = load_json("model_metadata.json")
modelling = load_json("modelling_summary.json")
evaluation = load_json("evaluation_summary.json")
eda = load_json("eda_summary.json")
split = load_split()
FEATURES = metadata["features"]
finalists = [m["model"] for m in metadata["finalists"]]
sigma = float(modelling["oof_best"]["residual_std"])

with st.sidebar:
    st.header("Replay settings")
    profile_id = st.selectbox("Test session (never used for training)", split["test_profiles"])
    model_name = st.selectbox("Model", finalists, index=0)
    t_hot = st.number_input("Alarm threshold (°C)", value=float(eda["target_train_stats"]["90%"]), step=1.0,
                            help="Default: 90th percentile of the training winding temperatures.")
    k = st.radio("Safety margin", [0, 1, 2], index=2, format_func=lambda v: f"k = {v} (+{v * sigma:.1f} °C)",
                 help="Alarm if estimate + k·σ ≥ threshold. σ = out-of-fold error std from cross-validation.")
    speed = st.slider("Replay speed (minutes of data per frame)", 1, 20, 5)

info = next(m for m in metadata["finalists"] if m["model"] == model_name)
model_path = config.PROJECT_DIR / info["file"]
live = FEATURES_FILE.exists() and model_path.exists()

if live:
    session = session_from_features(profile_id, FEATURES)
    model = load_model(model_path)
    pred = model.predict(session[FEATURES])
    actual = session[config.TARGET].to_numpy()
    coolant = session["coolant"].to_numpy()
    mode = f"live model: {model_name} runs on the session's 45 features"
else:
    saved = saved_predictions()
    saved = saved[saved[config.GROUP] == profile_id]
    col = "pred_" + model_name.split(" ")[0].lower()
    pred = saved[col].to_numpy()
    actual = saved["actual"].to_numpy()
    coolant = saved["coolant"].to_numpy()
    mode = "fallback: replaying the predictions saved in Phase 5 (run notebooks 03-04 for live mode)"

minutes = np.arange(len(actual)) / config.SAMPLE_RATE_HZ / 60
per_minute = pd.DataFrame({"minute": np.floor(minutes).astype(int), "actual": actual, "estimate": pred, "coolant": coolant}).groupby("minute").mean()
st.info(f"Mode: {mode}")

total = int(per_minute.index.max())
if "position" not in st.session_state or st.session_state.get("session_id") != profile_id:
    st.session_state.position = min(30, total)
    st.session_state.session_id = profile_id

c1, c2, c3 = st.columns([1, 1, 3])
play = c1.button("▶ Play to the end")
if c2.button("⟲ Reset"):
    st.session_state.position = min(30, total)
st.session_state.position = c3.slider("Position in the session (minutes)", 0, total, st.session_state.position)

lamp = st.empty()
metrics = st.empty()
chart = st.empty()


def draw(pos):
    view = per_minute.loc[:pos].copy()
    view["estimate + margin"] = view["estimate"] + k * sigma
    now = view.iloc[-1]
    alarm = now["estimate"] + k * sigma >= t_hot
    if alarm:
        lamp.error(f"🔴 OVERHEATING ALARM at minute {pos}: estimate {now['estimate']:.1f} °C + margin ≥ {t_hot:.1f} °C")
    else:
        lamp.success(f"🟢 OK at minute {pos}: estimate {now['estimate']:.1f} °C + margin < {t_hot:.1f} °C")
    with metrics.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Estimated winding", f"{now['estimate']:.1f} °C")
        m2.metric("Actual (sensor, for comparison)", f"{now['actual']:.1f} °C")
        m3.metric("Error (estimate − actual)", f"{now['estimate'] - now['actual']:+.1f} °C")
        m4.metric("Coolant", f"{now['coolant']:.1f} °C")
    view["threshold"] = t_hot
    chart.line_chart(view[["actual", "estimate", "estimate + margin", "coolant", "threshold"]],
                     x_label="minutes since session start", y_label="temperature (°C)")


if play:
    pos = st.session_state.position
    while pos < total:
        pos = min(pos + speed, total)
        draw(pos)
        time.sleep(0.15)
    st.session_state.position = pos
else:
    draw(st.session_state.position)

row = next(r for r in evaluation["overall"] if r["model"] == model_name)
st.subheader("Measured test results (Phase 5, all 6 test sessions)")
st.write(f"RMSE **{row['rmse']:.2f} °C**, MAE **{row['mae']:.2f} °C**, R² **{row['r2']:.3f}**, "
         f"max |error| **{row['max_abs_error']:.2f} °C**, mean signed error **{row['mean_signed_error']:+.2f} °C**.")
st.caption("Limitations: one test-bench motor, data up to 141.36 °C, recorded replay rather than live hardware. "
           "Transfer to another motor would need new data and validation.")
