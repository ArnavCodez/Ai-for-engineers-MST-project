"""Builds showcase/motor_showcase.html: the interactive project showcase (one self-contained web page).

What it packs into the page:
- the 6 test sessions (8 raw input signals + the real winding temperature, exact float32 values);
- the saved Phase 5 test predictions of the 3 finalists (MLP, LightGBM, Ridge);
- the weights of the saved MLP and Ridge pipelines, so the page can run them in the browser;
- every result number it shows, read from outputs/results/ (nothing is typed in by hand).

Before writing the page, it re-runs the browser's maths in numpy and checks it against the saved
predictions and result files (per-session RMSE, the safety-alarm table). If a check fails, it stops.

Run from the repo root (needs the git-ignored data and models, i.e. notebooks 01, 03 and 04 run once):
    python showcase/build_showcase.py
It writes two files, both git-ignored because they embed test data:
- showcase/motor_showcase.html: a complete page; double-click it to present offline;
- showcase/motor_showcase_artifact.html: the same page without <html>/<head>, for publishing online.
"""
import base64
import gzip
import json
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
from src import config  # noqa: E402
from src.data import load_split  # noqa: E402

SHOWCASE_DIR = PROJECT_DIR / "showcase"
TEMPLATE = SHOWCASE_DIR / "template.html"
OUTPUT = SHOWCASE_DIR / "motor_showcase.html"
OUTPUT_ARTIFACT = SHOWCASE_DIR / "motor_showcase_artifact.html"
R = config.RESULTS_DIR

PRED_COLS = {"m6": "pred_m6", "m5": "pred_m5", "m3": "pred_m3"}
MODEL_NAMES = {"m6": "M6 MLP (64-32)", "m5": "M5 LightGBM", "m3": "M3 Ridge", "b1": "B1 coolant + offset", "b0": "B0 mean"}


def read_json(name):
    with open(R / name, encoding="utf-8") as f:
        return json.load(f)


def f32_list(a):
    """float32 array -> shortest decimals that round-trip to the same float32 (JS uses Math.fround)."""
    return [float(np.format_float_positional(np.float32(v), unique=True, trim="-")) for v in np.ravel(a)]


def f64_list(a):
    return [float(v) for v in np.ravel(a)]


def clean(obj):
    """Make results JSON-safe (NaN -> None)."""
    if isinstance(obj, float) and np.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean(v) for v in obj]
    return obj


# ---------------------------------------------------------------- 1. test rows in file order
split = load_split()
raw = pd.read_parquet(config.PARQUET)
test = raw[raw[config.GROUP].isin(split["test_profiles"])].reset_index(drop=True)
preds = pd.read_csv(R / "test_predictions.csv")
assert len(test) == len(preds) == split["n_test_rows"]
assert (test[config.GROUP].to_numpy() == preds[config.GROUP].to_numpy()).all()
assert np.allclose(np.round(test[config.TARGET].to_numpy("float64"), 3), preds["actual"])

signal_cols = list(config.INPUTS) + [config.TARGET]
n = len(test)

# ---------------------------------------------------------------- 2. binary blob (gzip + base64)
# floats: byte-shuffled float32 (compresses better); predictions: int32 thousandths, delta-coded
parts, layout, offset = [], [], 0
for col in signal_cols:
    b = test[col].to_numpy(np.float32).tobytes()
    shuffled = np.frombuffer(b, np.uint8).reshape(-1, 4).T.copy().tobytes()
    parts.append(shuffled)
    layout.append({"name": col, "kind": "f32shuf", "offset": offset})
    offset += len(shuffled)
for key, col in PRED_COLS.items():
    q = np.round(preds[col].to_numpy("float64") * 1000).astype(np.int64)
    d = np.diff(q, prepend=0).astype("<i4")
    assert np.array_equal(np.cumsum(d.astype(np.int64)), q)
    parts.append(d.tobytes())
    layout.append({"name": key, "kind": "i32delta_milli", "offset": offset})
    offset += d.nbytes
blob = gzip.compress(b"".join(parts), compresslevel=9, mtime=0)
blob_b64 = base64.b64encode(blob).decode("ascii")

# ---------------------------------------------------------------- 3. model weights
meta = json.load(open(config.MODELS_DIR / "model_metadata.json", encoding="utf-8"))
features = meta["features"]
mlp_pipe = joblib.load(PROJECT_DIR / "outputs/models/m6_mlp_64_32.joblib")
ridge_pipe = joblib.load(PROJECT_DIR / "outputs/models/m3_ridge.joblib")
for pipe in (mlp_pipe, ridge_pipe):
    assert list(pipe.named_steps["scale"].feature_names_in_) == features
scale, mlp = mlp_pipe.named_steps["scale"], mlp_pipe.named_steps["model"]
assert mlp.activation == "relu" and mlp.out_activation_ == "identity"
mlp_json = {
    "mean": f64_list(scale.mean_), "scale": f64_list(scale.scale_),
    "layers": [{"in": int(W.shape[0]), "out": int(W.shape[1]), "W": f32_list(W), "b": f32_list(b)}
               for W, b in zip(mlp.coefs_, mlp.intercepts_)],
}
rscale, ridge = ridge_pipe.named_steps["scale"], ridge_pipe.named_steps["model"]
ridge_json = {"mean": f64_list(rscale.mean_), "scale": f64_list(rscale.scale_),
              "coef": f32_list(ridge.coef_), "intercept": f32_list([ridge.intercept_])[0]}


# ---------------------------------------------------------------- 4. re-run the browser's maths in numpy
def browser_features(df):
    """Same maths as the page's JavaScript (and as src/features.py): float64 maths, float32 storage."""
    f = lambda a: np.asarray(a, dtype=np.float32).astype(np.float64)  # noqa: E731
    cols = {c: f(df[c]) for c in config.INPUTS}
    i_s = np.sqrt(cols["i_d"] ** 2 + cols["i_q"] ** 2)
    cols["u_s"] = f(np.sqrt(cols["u_d"] ** 2 + cols["u_q"] ** 2))
    cols["i_s_sq"] = f(i_s ** 2)
    cols["i_s"] = f(i_s)
    cols["p_el"] = f(1.5 * (cols["u_d"] * cols["i_d"] + cols["u_q"] * cols["i_q"]))
    cols["p_mech"] = f(cols["torque"] * cols["motor_speed"] * 2 * np.pi / 60)
    groups = df[config.GROUP].to_numpy()
    for name in features:
        if "_ewma_" not in name:
            continue
        base, span = name.rsplit("_ewma_", 1)
        w = 1 - 2 / (int(span) + 1)
        out = np.empty(len(df))
        x = cols[base]
        num = den = 0.0
        for i in range(len(df)):
            if i == 0 or groups[i] != groups[i - 1]:
                num = den = 0.0
            num = x[i] + w * num
            den = 1 + w * den
            out[i] = num / den
        cols[name] = f(out)
    return np.column_stack([cols[c] for c in features])


def browser_mlp(X):
    h = (X - mlp_json["mean"]) / np.array(mlp_json["scale"])
    for k, layer in enumerate(mlp_json["layers"]):
        W = np.array(layer["W"], dtype=np.float64).reshape(layer["in"], layer["out"])
        h = h @ W + np.array(layer["b"])
        if k < len(mlp_json["layers"]) - 1:
            h = np.maximum(h, 0)
    return h[:, 0]


def browser_ridge(X):
    z = (X - ridge_json["mean"]) / np.array(ridge_json["scale"])
    return z @ np.array(ridge_json["coef"]) + ridge_json["intercept"]


print("Re-running the browser maths in numpy...")
X = browser_features(test)
diff_mlp = np.abs(browser_mlp(X) - preds["pred_m6"].to_numpy())
diff_ridge = np.abs(browser_ridge(X) - preds["pred_m3"].to_numpy())
print(f"  MLP   max |browser - saved| = {diff_mlp.max():.4f} °C")
print(f"  Ridge max |browser - saved| = {diff_ridge.max():.4f} °C")
assert diff_mlp.max() < 0.05 and diff_ridge.max() < 0.05

# ---------------------------------------------------------------- 5. result numbers (all from files)
per = pd.read_csv(R / "test_metrics_per_profile.csv")
actual = test[config.TARGET].to_numpy("float64")
sessions = []
for pid in split["test_profiles"]:
    idx = np.flatnonzero(test[config.GROUP].to_numpy() == pid)
    assert np.array_equal(idx, np.arange(idx[0], idx[-1] + 1))
    rows = per[per["profile_id"] == pid].set_index("model")
    info = {"id": int(pid), "start": int(idx[0]), "rows": int(len(idx)),
            "hours": float(rows["hours"].iloc[0]), "winding_max": float(rows["winding_max"].iloc[0]),
            "rmse": {}, "mae": {}}
    for key, name in MODEL_NAMES.items():
        info["rmse"][key] = float(rows.loc[name, "rmse"])
        info["mae"][key] = float(rows.loc[name, "mae"])
    for key, col in PRED_COLS.items():  # check: saved CSV predictions reproduce the saved per-session RMSE
        err = preds[col].to_numpy()[idx] - actual[idx]
        assert abs(np.sqrt(np.mean(err ** 2)) - info["rmse"][key]) < 1e-3, (pid, key)
    sessions.append(info)

evaluation = read_json("evaluation_summary.json")
modelling = read_json("modelling_summary.json")
innovation = read_json("innovation_summary.json")
eda = read_json("eda_summary.json")
check = read_json("data_check_summary.json")
feats = read_json("features_summary.json")

sigma = float(modelling["oof_best"]["residual_std"])
t_hot = float(eda["target_train_stats"]["90%"])
safety_csv = pd.read_csv(R / "safety_alarm.csv")
hot = actual >= t_hot
for _, row in safety_csv.iterrows():  # check: the page's live safety maths gives the saved table
    alarm = preds["pred_m6"].to_numpy() + row["k"] * sigma >= t_hot
    assert int(hot.sum()) == int(row["hot_rows"])
    assert abs(100 * (alarm & hot).sum() / hot.sum() - row["caught_pct"]) < 1e-9
    assert abs(100 * (alarm & ~hot).sum() / (~hot).sum() - row["false_alarm_pct"]) < 1e-9

train = raw[raw[config.GROUP].isin(split["train_profiles"])]
i_s_train = np.sqrt(train["i_d"].astype("float64") ** 2 + train["i_q"].astype("float64") ** 2)
train_range = {c: [float(train[c].min()), float(train[c].max())] for c in config.INPUTS}
train_range["i_s"] = [float(i_s_train.min()), float(i_s_train.max())]

# one what-if example for the log and the viva: session 66, coolant 10 °C warmer, final MLP
pid_example, coolant_shift = 66, 10.0
rows_ex = test[test[config.GROUP] == pid_example]
shifted = rows_ex.copy()
shifted["coolant"] = (shifted["coolant"].astype("float64") + coolant_shift).astype("float32")
base_ex, what_ex = browser_mlp(browser_features(rows_ex)), browser_mlp(browser_features(shifted))
whatif_example = {
    "session": pid_example, "model": evaluation["final_model"],
    "coolant_shift_c": coolant_shift, "mean_shift_c": float(np.mean(what_ex - base_ex)),
    "peak_before_c": float(base_ex.max()), "peak_after_c": float(what_ex.max()),
    "minutes_at_or_above_t_hot_before": float((base_ex >= t_hot).sum() / 120),
    "minutes_at_or_above_t_hot_after": float((what_ex >= t_hot).sum() / 120),
}
# same "outside the training range" rule as the page (coolant, current magnitude, torque)
i_s_ex = np.sqrt(shifted["i_d"].astype("float64") ** 2 + shifted["i_q"].astype("float64") ** 2)
outside = ((shifted["coolant"] < train_range["coolant"][0]) | (shifted["coolant"] > train_range["coolant"][1])
           | (i_s_ex > train_range["i_s"][1])
           | (shifted["torque"] < train_range["torque"][0]) | (shifted["torque"] > train_range["torque"][1]))
whatif_example["pct_rows_outside_training_range"] = float(100 * outside.mean())
check_out = {
    "built": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "rows": n,
    "browser_mlp_max_abs_diff_vs_saved_c": float(diff_mlp.max()),
    "browser_ridge_max_abs_diff_vs_saved_c": float(diff_ridge.max()),
    "per_session_rmse_reproduced": True,
    "safety_table_reproduced": True,
    "whatif_example": whatif_example,
}
with open(R / "showcase_check.json", "w", encoding="utf-8") as f:
    json.dump(check_out, f, indent=2)
print("  what-if example:", {k: round(v, 3) if isinstance(v, float) else v for k, v in whatif_example.items()})

payload = {
    "built": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "n": n, "layout": layout, "features": features, "inputs": list(config.INPUTS),
    "mlp": mlp_json, "ridge": ridge_json,
    "browser_check_python": {"mlp_max_abs_diff": float(diff_mlp.max()), "ridge_max_abs_diff": float(diff_ridge.max())},
    "sessions": sessions, "train_range": train_range,
    "facts": {"rows": check["n_rows"], "sessions": check["n_profiles"], "hours": check["total_hours"],
              "winding_max": eda["target_train_stats"]["max"], "test_rows": evaluation["test_rows"],
              "test_share": split["test_share_of_rows"], "n_train_sessions": len(split["train_profiles"]),
              "cv_rows": modelling["cv_rows"], "test_opened_at": evaluation["test_opened_at"],
              "n_features": feats["n_features"], "within_2c_pct": evaluation["within_2c_pct"],
              "within_5c_pct": evaluation["within_5c_pct"], "thermal_lag_min": eda["thermal_lag"]["median_best_lag_min"]},
    "targets": evaluation["targets"], "final_model": evaluation["final_model"],
    "cv": clean(pd.read_csv(R / "cv_results.csv").drop(columns=["params"]).to_dict("records")),
    "test": clean(pd.read_csv(R / "test_metrics.csv").to_dict("records")),
    "ablation": innovation["ablation"], "memory": innovation["memory_curve"],
    "importance": clean(pd.read_csv(R / "permutation_importance_grouped.csv").to_dict("records")),
    "importance_base_rmse": evaluation["permutation_base_rmse_sample"],
    "safety": {"sigma": sigma, "t_hot": t_hot, "table": safety_csv.to_dict("records")},
    "session_start": innovation["session_start"]["table"],
    "data_efficiency": clean(innovation["data_efficiency"]["table"]),
    "under": evaluation["under_prediction"][evaluation["final_model"]],
}

# ---------------------------------------------------------------- 6. write the page
payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = TEMPLATE.read_text(encoding="utf-8")
assert html.count("__PAYLOAD__") == 1 and html.count("__BLOB__") == 1
html = html.replace("__PAYLOAD__", payload_json).replace("__BLOB__", blob_b64)
OUTPUT_ARTIFACT.write_text(html, encoding="utf-8")
standalone = "\n".join([
    "<!doctype html>",
    '<html lang="en">',
    "<head>",
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
    "</head>",
    "<body>",
    html,
    "</body>",
    "</html>",
])
OUTPUT.write_text(standalone, encoding="utf-8")
print(f"Wrote {OUTPUT.relative_to(PROJECT_DIR)}: {OUTPUT.stat().st_size / 1e6:.2f} MB "
      f"(data blob {len(blob) / 1e6:.2f} MB gzip, payload {len(payload_json) / 1e3:.0f} kB)")
