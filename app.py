"""Streamlit demo: winding-temperature virtual sensor.

Run from the repo root (venv active):
    streamlit run app.py

Three tabs:
- Replay: replays one of the 6 test sessions. The real sensor value is shown ONLY
  for comparison; the model's inputs are the 45 features from src/features.py.
- Try your own values: you set an operating point (the 8 measured signals) and how
  long the motor runs at it. The app builds the same 45 features over that run and
  shows how the estimated winding temperature climbs.
- Model performance: the measured test and cross-validation results.

Replay has two modes:
- live model: needs data/processed/features.parquet (notebook 03) and the saved
  model (notebook 04). The app runs the model on the chosen session.
- fallback: if those files are missing, it replays the predictions saved in
  outputs/results/test_predictions.csv (made once in notebook 05).
"""
import json
import time

import altair as alt
import joblib
import numpy as np
import pandas as pd
import streamlit as st

from src import config
from src.data import load_split
from src.features import build_features

FEATURES_FILE = config.PROJECT_DIR / "data" / "processed" / "features.parquet"

# Operating points taken from the medians of training rows near each speed/torque.
PRESETS = {
    "Idle": dict(motor_speed=0.0, torque=0.0, i_d=-2.0, i_q=1.1, u_d=0.8, u_q=-0.7),
    "Light load (1000 rpm, 25 Nm)": dict(motor_speed=1000.0, torque=25.0, i_d=-6.4, i_q=36.9, u_d=-13.6, u_q=48.0),
    "Medium load (2000 rpm, 47 Nm)": dict(motor_speed=1960.0, torque=46.6, i_d=-13.6, i_q=64.2, u_d=-44.5, u_q=91.5),
    "Heavy load (3500 rpm, 100 Nm)": dict(motor_speed=3500.0, torque=100.0, i_d=-172.4, i_q=107.2, u_d=-124.3, u_q=41.3),
    "High speed (6000 rpm, 49 Nm)": dict(motor_speed=6000.0, torque=49.2, i_d=-168.1, i_q=52.3, u_d=-116.0, u_q=57.7),
}
# (label, min, max, step) for each input, from the full dataset's range
INPUT_SPECS = {
    "motor_speed": ("Motor speed (rpm)", -300.0, 6100.0, 50.0),
    "torque": ("Torque (Nm)", -250.0, 265.0, 1.0),
    "i_d": ("Current i_d (A)", -280.0, 1.0, 1.0),
    "i_q": ("Current i_q (A)", -295.0, 305.0, 1.0),
    "u_d": ("Voltage u_d (V)", -132.0, 132.0, 1.0),
    "u_q": ("Voltage u_q (V)", -26.0, 134.0, 1.0),
}


@st.cache_data
def load_json(name):
    with open(config.RESULTS_DIR / name) as f:
        return json.load(f)


@st.cache_data
def load_csv(name):
    return pd.read_csv(config.RESULTS_DIR / name)


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


@st.cache_data
def simulate(point, ambient, coolant, idle_minutes, run_minutes):
    """Constant-input run at 2 Hz: idle first, then the chosen operating point."""
    n_idle = int(idle_minutes * 60 * config.SAMPLE_RATE_HZ)
    n_run = int(run_minutes * 60 * config.SAMPLE_RATE_HZ)
    rows = [PRESETS["Idle"]] * n_idle + [point] * n_run
    df = pd.DataFrame(rows)
    df["ambient"] = ambient
    df["coolant"] = coolant
    df[config.GROUP] = 0
    return build_features(df[[config.GROUP] + config.INPUTS])


st.set_page_config(page_title="Winding temperature virtual sensor", layout="wide")
st.title("Virtual winding-temperature sensor")
st.caption("Paderborn PMSM test bench, Kaggle dataset v3. Not connected to a real motor. "
           "GE Power Systems is the assignment scenario.")

metadata = load_json("model_metadata.json")
modelling = load_json("modelling_summary.json")
evaluation = load_json("evaluation_summary.json")
eda = load_json("eda_summary.json")
split = load_split()
FEATURES = metadata["features"]
finalists = [m["model"] for m in metadata["finalists"]]
sigma = float(modelling["oof_best"]["residual_std"])

with st.sidebar:
    st.header("Settings")
    model_name = st.selectbox("Model", finalists, index=0)
    t_hot = st.number_input("Alarm threshold (°C)", value=float(eda["target_train_stats"]["90%"]), step=1.0,
                            help="Default: 90th percentile of the training winding temperatures.")
    k = st.radio("Safety margin", [0, 1, 2], index=2, format_func=lambda v: f"k = {v} (+{v * sigma:.1f} °C)",
                 help="Alarm if estimate + k·σ ≥ threshold. σ = out-of-fold error std from cross-validation.")
    st.divider()
    st.header("Replay")
    profile_id = st.selectbox("Test session (never used for training)", split["test_profiles"])
    speed = st.slider("Replay speed (minutes of data per frame)", 1, 20, 5)

info = next(m for m in metadata["finalists"] if m["model"] == model_name)
model_path = config.PROJECT_DIR / info["file"]
model_ready = model_path.exists()

tab_replay, tab_values, tab_perf = st.tabs(["Replay a test session", "Try your own values", "Model performance"])

# ---------------------------------------------------------------- replay
with tab_replay:
    live = FEATURES_FILE.exists() and model_ready
    if live:
        session = session_from_features(profile_id, FEATURES)
        pred = load_model(model_path).predict(session[FEATURES])
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
    per_minute = pd.DataFrame({"minute": np.floor(minutes).astype(int), "actual": actual, "estimate": pred,
                               "coolant": coolant}).groupby("minute").mean()
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
        if now["estimate"] + k * sigma >= t_hot:
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

# ---------------------------------------------------------------- your own values
with tab_values:
    st.write("Set the motor's operating point and how long it runs there. The motor idles first, then switches "
             "to your values; the model gets the same 45 features it was trained on, built from this run.")
    if not model_ready:
        st.warning(f"Model file {info['file']} not found. Run notebook 04 first.")
    else:
        if "preset" not in st.session_state:
            st.session_state.preset = "Medium load (2000 rpm, 47 Nm)"
            st.session_state.update(PRESETS[st.session_state.preset])

        def apply_preset():
            st.session_state.update(PRESETS[st.session_state.preset])

        left, right = st.columns([1, 2])
        with left:
            st.selectbox("Start from a typical operating point", list(PRESETS), key="preset", on_change=apply_preset)
            a, b = st.columns(2)
            ambient = a.number_input("Ambient (°C)", 8.0, 31.0, 25.0, 0.5)
            coolant_in = b.number_input("Coolant (°C)", 10.0, 102.0, 25.0, 0.5)
            point = {}
            cols = st.columns(2)
            for i, (name, (label, lo, hi, step)) in enumerate(INPUT_SPECS.items()):
                point[name] = cols[i % 2].number_input(label, lo, hi, step=step, key=name)
            idle_minutes = st.slider("Idle before the step (minutes)", 0, 60, 10)
            run_minutes = st.slider("Run at this point (minutes)", 5, 180, 90)

        feats = simulate(point, ambient, coolant_in, idle_minutes, run_minutes)
        est = load_model(model_path).predict(feats[FEATURES])
        t = np.arange(len(est)) / config.SAMPLE_RATE_HZ / 60 - idle_minutes
        curve = pd.DataFrame({"minute": t, "estimate": est}).iloc[:: config.SAMPLE_RATE_HZ * 15]
        final = float(est[-1])
        i_s = float(np.hypot(point["i_d"], point["i_q"]))
        p_el = 1.5 * (point["u_d"] * point["i_d"] + point["u_q"] * point["i_q"])

        with right:
            if final + k * sigma >= t_hot:
                st.error(f"🔴 OVERHEATING ALARM after {run_minutes} min: {final:.1f} °C + margin ≥ {t_hot:.1f} °C")
            else:
                st.success(f"🟢 OK after {run_minutes} min: {final:.1f} °C + margin < {t_hot:.1f} °C")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Estimated winding", f"{final:.1f} °C")
            m2.metric("Rise above coolant", f"{final - coolant_in:+.1f} °C")
            m3.metric("Current magnitude", f"{i_s:.0f} A")
            m4.metric("Electrical power", f"{p_el / 1000:.1f} kW")
            band = curve.assign(low=curve["estimate"] - k * sigma, high=curve["estimate"] + k * sigma)
            x = alt.X("minute:Q", title="minutes since the step (negative = idle)")
            chart = (
                alt.Chart(band).mark_area(opacity=0.2).encode(x=x, y=alt.Y("low:Q", title="temperature (°C)"), y2="high:Q")
                + alt.Chart(band).mark_line(strokeWidth=2.5).encode(x=x, y="estimate:Q")
                + alt.Chart(pd.DataFrame({"y": [t_hot]})).mark_rule(color="#d62728", strokeDash=[6, 4]).encode(y="y:Q")
                + alt.Chart(pd.DataFrame({"y": [coolant_in]})).mark_rule(color="#7f7f7f", strokeDash=[2, 2]).encode(y="y:Q")
            )
            st.altair_chart(chart, width="stretch")
            st.caption(f"Line: estimate. Shaded band: ± k·σ ({k * sigma:.1f} °C). Red dashed: alarm threshold. "
                       "Grey dotted: coolant. Combinations far from the test-bench data (for example high current at "
                       "zero speed) are outside what the model has seen, so treat those numbers with care.")

# ---------------------------------------------------------------- performance
with tab_perf:
    overall = pd.DataFrame(evaluation["overall"])
    best = overall.set_index("model").loc[evaluation["final_model"]]
    st.subheader(f"Final model: {evaluation['final_model']} on the 6 held-out test sessions")
    c = st.columns(5)
    c[0].metric("RMSE", f"{best['rmse']:.2f} °C")
    c[1].metric("MAE", f"{best['mae']:.2f} °C")
    c[2].metric("R²", f"{best['r2']:.3f}")
    c[3].metric("Within ±2 °C", f"{evaluation['within_2c_pct']:.0f}%")
    c[4].metric("Within ±5 °C", f"{evaluation['within_5c_pct']:.0f}%")

    left, right = st.columns(2)
    with left:
        st.markdown("**Test error by model** (lower is better; B0/B1 are simple baselines)")
        long = overall.melt(id_vars="model", value_vars=["rmse", "mae"], var_name="metric", value_name="°C")
        st.altair_chart(alt.Chart(long).mark_bar().encode(
            y=alt.Y("model:N", sort="x", title=None), x="°C:Q", color="metric:N", yOffset="metric:N",
            tooltip=["model", "metric", alt.Tooltip("°C:Q", format=".2f")]), width="stretch")
    with right:
        st.markdown("**Cross-validation vs test RMSE** (error bar = CV std across folds)")
        cvt = pd.DataFrame(evaluation["cv_vs_test"])
        base = alt.Chart(cvt).encode(y=alt.Y("model:N", title=None))
        st.altair_chart(
            base.mark_errorbar().encode(x=alt.X("lo:Q", title="RMSE (°C)"), x2="hi:Q").transform_calculate(
                lo="datum.cv_rmse - datum.cv_std", hi="datum.cv_rmse + datum.cv_std")
            + base.mark_point(filled=True, size=80).encode(x="cv_rmse:Q", color=alt.value("#1f77b4"),
                                                           tooltip=["model", "cv_rmse", "cv_std"])
            + base.mark_point(shape="diamond", filled=True, size=80).encode(x="test_rmse:Q", color=alt.value("#ff7f0e"),
                                                                            tooltip=["model", "test_rmse"]),
            width="stretch")
        st.caption("Blue: CV mean. Orange: test.")

    preds = saved_predictions()
    col = "pred_" + evaluation["final_model"].split(" ")[0].lower()
    sample = preds.sample(min(6000, len(preds)), random_state=config.SEED).assign(
        error=lambda d: d[col] - d["actual"], session=lambda d: d[config.GROUP].astype(str))
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Predicted vs actual** ({evaluation['final_model']}, 6000 random test rows)")
        lim = [15, 145]
        st.altair_chart(
            alt.Chart(sample).mark_circle(size=8, opacity=0.4).encode(
                x=alt.X("actual:Q", scale=alt.Scale(domain=lim), title="actual (°C)"),
                y=alt.Y(f"{col}:Q", scale=alt.Scale(domain=lim), title="predicted (°C)"), color="session:N")
            + alt.Chart(pd.DataFrame({"a": lim})).mark_line(color="black", strokeDash=[4, 4]).encode(x="a:Q", y="a:Q"),
            width="stretch")
    with right:
        st.markdown("**Error distribution** (predicted − actual)")
        st.altair_chart(alt.Chart(sample).mark_bar().encode(
            x=alt.X("error:Q", bin=alt.Bin(maxbins=60), title="error (°C)"), y=alt.Y("count()", title="rows")),
            width="stretch")

    left, right = st.columns(2)
    with left:
        st.markdown("**RMSE per test session**")
        per = load_csv("test_metrics_per_profile.csv")
        per = per[per["model"].isin(finalists)].assign(session=lambda d: d[config.GROUP].astype(str))
        st.altair_chart(alt.Chart(per).mark_bar().encode(
            x=alt.X("session:N", title="test session"), xOffset="model:N", y=alt.Y("rmse:Q", title="RMSE (°C)"),
            color="model:N", tooltip=["session", "model", alt.Tooltip("rmse:Q", format=".2f")]),
            width="stretch")
    with right:
        st.markdown("**Which inputs matter** (RMSE increase when the group is shuffled)")
        imp = load_csv("permutation_importance_grouped.csv")
        st.altair_chart(alt.Chart(imp).mark_bar().encode(
            y=alt.Y("family:N", sort="-x", title=None), x=alt.X("rmse_increase:Q", title="RMSE increase (°C)")),
            width="stretch")

    left, right = st.columns(2)
    with left:
        st.markdown("**Feature ablation** (CV RMSE with parts of the features removed)")
        abl = load_csv("ablation.csv")
        st.altair_chart(alt.Chart(abl).mark_bar().encode(
            y=alt.Y("variant:N", sort="x", title=None), x=alt.X("cv_rmse:Q", title="CV RMSE (°C)"),
            color=alt.condition(alt.datum.variant == "full", alt.value("#2ca02c"), alt.value("#9ecae1")),
            tooltip=["variant", "n_features", alt.Tooltip("cv_rmse:Q", format=".2f")]), width="stretch")
        st.caption("'with leakage' uses forbidden sensor columns, so its low error is not achievable in practice.")
    with right:
        st.markdown("**Safety alarm trade-off by margin k**")
        alarm = load_csv("safety_alarm.csv")
        st.dataframe(alarm.rename(columns={"margin_c": "margin (°C)", "caught_pct": "hot rows caught (%)",
                                           "false_alarm_pct": "false alarms (%)", "precision_pct": "precision (%)"})
                     [["k", "margin (°C)", "hot rows caught (%)", "false alarms (%)", "precision (%)"]].round(1),
                     hide_index=True, width="stretch")

    st.caption("Limitations: one test-bench motor, data up to 141.36 °C, recorded data rather than live hardware. "
               "Transfer to another motor would need new data and validation.")
