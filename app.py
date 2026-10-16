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

Theme lives in .streamlit/config.toml (light, teal accent).
"""
import json
import re
import time

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from src import config
from src.data import load_split

FEATURES_FILE = config.PROJECT_DIR / "data" / "processed" / "features.parquet"

WARMUP_MIN = 3  # minutes at the start of a session where the estimate is flagged as unreliable


# ---------------------------------------------------------------- data loading
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


# ---------------------------------------------------------------- page + style
st.set_page_config(page_title="Motor temperature estimator", layout="centered")
st.markdown("""
<style>
.block-container { max-width: 860px; padding-top: 2.5rem; padding-bottom: 4rem; }
header[data-testid="stHeader"] { background: transparent; }
.top-bar { position: fixed; top: 0; left: 0; right: 0; height: 4px; background: #2a7f8a; z-index: 1000; }

.main-title { font-size: 30px; font-weight: 650; letter-spacing: -0.01em; color: #1f2933; margin: 0 0 10px; }
.main-subtitle { font-size: 16px; color: #6b7785; margin: 0 0 32px; max-width: 560px; line-height: 1.6; }

/* every bordered container becomes a soft white card */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff; border: 1px solid #e3e8ed !important; border-radius: 14px;
    padding: 0.6rem 0.8rem; box-shadow: 0 1px 2px rgba(31, 41, 51, 0.04);
}

.status { display: flex; align-items: center; gap: 12px; font-size: 17px; margin: 4px 0 18px; }
.dot { width: 11px; height: 11px; border-radius: 50%; flex: none; }
.dot.ok { background: #3f9468; box-shadow: 0 0 0 4px rgba(63, 148, 104, 0.15); }
.dot.warn { background: #d99a2b; box-shadow: 0 0 0 4px rgba(217, 154, 43, 0.18); }
.dot.alarm { background: #c4564a; box-shadow: 0 0 0 4px rgba(196, 86, 74, 0.16); }

[data-testid="stMetricValue"] { font-size: 30px; font-weight: 550; }
[data-testid="stMetricLabel"] { color: #6b7785; }

.card-title { font-size: 17px; font-weight: 600; margin: 0 0 8px; color: #1f2933; }
.card-text { font-size: 15px; line-height: 1.6; margin: 0; }
</style>
<div class="top-bar"></div>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">Motor temperature, estimated from sensors</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-subtitle">Replays a recorded test run and compares what the model predicts '
    'with what the winding sensor actually measured.</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- load everything first
metadata = load_json("model_metadata.json")
modelling = load_json("modelling_summary.json")
evaluation = load_json("evaluation_summary.json")
eda = load_json("eda_summary.json")
split = load_split()
FEATURES = metadata["features"]
finalists = [m["model"] for m in metadata["finalists"]]
sigma = float(modelling["oof_best"]["residual_std"])


def nice_name(name):
    """'M6 MLP (64-32)' -> 'MLP (64-32)' for display; the raw name is still used internally."""
    return re.sub(r"^M\d+\s+", "", name)


# ---------------------------------------------------------------- controls
with st.sidebar:
    st.header("Advanced settings")
    model_name = st.selectbox("Model", finalists, index=0, format_func=nice_name)
    speed = st.slider("Replay speed (minutes of data per frame)", 1, 20, 5)

with st.container(border=True):
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        profile_id = st.selectbox("Test session", split["test_profiles"])
    with c2:
        t_hot = st.number_input(
            "Limit (°C)",
            value=float(round(eda["target_train_stats"]["90%"])),
            step=1.0,
            format="%.0f",
            help="Default is the 90th percentile of winding temperatures seen in training.",
        )
    with c3:
        k = st.radio(
            "Safety margin",
            [0, 1, 2],
            index=1,
            horizontal=True,
            format_func=lambda i: "None" if i == 0 else f"+{i * sigma:.1f} °C",
            help="Added to the estimate before it is compared with the limit. "
                 "+1 and +2 are one and two times the model's typical error on validation data.",
        )

# ---------------------------------------------------------------- run the model (or replay saved predictions)
info = next(m for m in metadata["finalists"] if m["model"] == model_name)
model_path = config.PROJECT_DIR / info["file"]
live = FEATURES_FILE.exists() and model_path.exists()

if live:
    session = session_from_features(profile_id, FEATURES)
    model = load_model(model_path)
    pred = model.predict(session[FEATURES])
    actual = session[config.TARGET].to_numpy()
    coolant = session["coolant"].to_numpy()
    mode = f"Live: {nice_name(model_name)} is running on the session's {len(FEATURES)} input features."
else:
    saved = saved_predictions()
    saved = saved[saved[config.GROUP] == profile_id]
    col = "pred_" + model_name.split(" ")[0].lower()
    pred = saved[col].to_numpy()
    actual = saved["actual"].to_numpy()
    coolant = saved["coolant"].to_numpy()
    mode = "Showing saved predictions from a held-out test run, not a live motor."

minutes = np.arange(len(actual)) / config.SAMPLE_RATE_HZ / 60
per_minute = pd.DataFrame({
    "minute": np.floor(minutes).astype(int),
    "actual": actual,
    "estimate": pred,
    "coolant": coolant,
}).groupby("minute").mean()

total = int(per_minute.index.max())
if "position" not in st.session_state or st.session_state.get("session_id") != profile_id:
    st.session_state.position = min(30, total)
    st.session_state.session_id = profile_id

# ---------------------------------------------------------------- live view card
with st.container(border=True):
    lamp = st.empty()
    metrics = st.empty()
    chart = st.empty()
    b1, b2, b3 = st.columns([1, 1, 3])
    play = b1.button("Play to the end")
    if b2.button("Reset"):
        st.session_state.position = min(30, total)
    st.session_state.position = b3.slider("Minute", 0, total, st.session_state.position)


def draw(pos):
    view = per_minute.loc[:pos].copy()
    view["estimate + margin"] = view["estimate"] + k * sigma
    view["threshold"] = t_hot
    now = view.iloc[-1]
    with_margin = now["estimate + margin"]

    if with_margin >= t_hot:
        kind, text = "alarm", f"Over the limit at minute {pos} ({with_margin:.1f} °C with margin)"
    elif pos < WARMUP_MIN:
        kind, text = "warn", "Warming up, estimate not reliable yet"
    else:
        kind, text = "ok", f"Within the limit at minute {pos} ({with_margin:.1f} °C with margin)"
    lamp.markdown(f'<div class="status"><span class="dot {kind}"></span><span>{text}</span></div>',
                  unsafe_allow_html=True)

    with metrics.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Estimate", f"{now['estimate']:.1f} °C")
        m2.metric("Sensor reading", f"{now['actual']:.1f} °C")
        m3.metric("Difference", f"{now['estimate'] - now['actual']:+.1f} °C")
        m4.metric("Coolant", f"{now['coolant']:.1f} °C")

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

# ---------------------------------------------------------------- notes + results
first = per_minute.iloc[0]
start_gap = first["estimate"] - first["actual"]
if abs(start_gap) >= 10:
    notice = (f"At minute 0 the estimate is {first['estimate']:.0f} °C while the sensor reads "
              f"{first['actual']:.0f} °C. The model only sees the current moment, so it cannot tell a cold start "
              f"from a motor that has been running hard. The two lines usually agree after the first few minutes.")
else:
    notice = (f"At minute 0 the estimate ({first['estimate']:.0f} °C) is close to the sensor "
              f"({first['actual']:.0f} °C). Try other sessions: the start of a run is where the model is least reliable.")

row = next(r for r in evaluation["overall"] if r["model"] == model_name)
results = (f"Typical error <b>{row['rmse']:.1f} °C</b> (RMSE), average miss <b>{row['mae']:.1f} °C</b>, "
           f"R² <b>{row['r2']:.2f}</b>. Worst single miss was {row['max_abs_error']:.0f} °C, and the model leans "
           f"{abs(row['mean_signed_error']):.1f} °C {'low' if row['mean_signed_error'] < 0 else 'high'} on average. "
           f"Tested on one motor only, so it would need new data before being trusted on another.")

n1, n2 = st.columns(2)
with n1:
    with st.container(border=True):
        st.markdown('<div class="card-title">What to notice</div>'
                    f'<p class="card-text">{notice}</p>', unsafe_allow_html=True)
with n2:
    with st.container(border=True):
        st.markdown('<div class="card-title">Results on all 6 test sessions</div>'
                    f'<p class="card-text">{results}</p>', unsafe_allow_html=True)

st.caption(mode)
st.caption("Your Name, course or assignment. Data: Paderborn PMSM test bench (Kaggle dataset v3). "
           "Test data up to 141.36 °C.")