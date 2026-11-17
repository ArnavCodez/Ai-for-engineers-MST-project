"""Build demo/index.html: one offline page that runs our trained MLP and Ridge models in the browser.

It packs the 6 test sessions (the 8 controller signals and the real winding temperature), the
saved Phase 5 predictions, the model weights and the result files into a single page. Before
writing, it re-runs the page's maths in numpy and stops if it differs from the saved predictions.

Run from the repo root with the project venv (needs the git-ignored data and the saved models):
    python demo/build_demo.py
"""
import ast
import base64
import gzip
import json
import re
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src import config  # noqa: E402
from src.data import load_split  # noqa: E402

R = config.RESULTS_DIR
PRED_COLS = {"m6": "pred_m6", "m3": "pred_m3", "m5": "pred_m5"}
MODEL_NAMES = {"m6": "M6 MLP (64-32)", "m5": "M5 LightGBM", "m3": "M3 Ridge"}


def read_json(name):
    return json.loads((R / name).read_text(encoding="utf-8"))


def f32_list(a):
    """Shortest decimals that round-trip to the same float32 (the page applies Math.fround)."""
    return [float(np.format_float_positional(np.float32(v), unique=True, trim="-")) for v in np.ravel(a)]


def _eval_presets(value):
    out = {}
    for key, call in zip(value.keys, value.values):
        out[ast.literal_eval(key)] = {kw.arg: float(ast.literal_eval(kw.value)) for kw in call.keywords}
    return out


def browser_features(df, features):
    """Same maths as the page: float64 arithmetic, every feature rounded to float32, EWMA reset per session."""
    f = lambda a: np.asarray(a, dtype=np.float32).astype(np.float64)  # noqa: E731
    cols = {c: f(df[c]) for c in config.INPUTS}
    i_s = np.sqrt(cols["i_d"] ** 2 + cols["i_q"] ** 2)
    cols["u_s"] = f(np.sqrt(cols["u_d"] ** 2 + cols["u_q"] ** 2))
    cols["i_s_sq"] = f(i_s ** 2)
    cols["i_s"] = f(i_s)
    cols["p_el"] = f(1.5 * (cols["u_d"] * cols["i_d"] + cols["u_q"] * cols["i_q"]))
    cols["p_mech"] = f(cols["torque"] * cols["motor_speed"] * 2 * np.pi / 60)
    groups = df[config.GROUP].to_numpy()
    starts = np.r_[True, groups[1:] != groups[:-1]]
    for name in features:
        if "_ewma_" not in name:
            continue
        base, span = name.rsplit("_ewma_", 1)
        w = 1 - 2 / (int(span) + 1)
        x, out = cols[base], np.empty(len(df))
        num = den = 0.0
        for i in range(len(df)):
            if starts[i]:
                num = den = 0.0
            num = x[i] + w * num
            den = 1 + w * den
            out[i] = num / den
        cols[name] = f(out)
    return np.column_stack([cols[c] for c in features])


def main():
    split = load_split()
    raw = pd.read_parquet(config.PARQUET)
    test = raw[raw[config.GROUP].isin(split["test_profiles"])].reset_index(drop=True)
    preds = pd.read_csv(R / "test_predictions.csv")
    assert len(test) == len(preds) == split["n_test_rows"]
    assert (test[config.GROUP].to_numpy() == preds[config.GROUP].to_numpy()).all()
    n = len(test)

    # test rows: byte-shuffled float32 columns; saved predictions as delta-coded thousandths; then gzip
    parts, layout, offset = [], [], 0
    for col in list(config.INPUTS) + [config.TARGET]:
        b = test[col].to_numpy(np.float32).tobytes()
        shuffled = np.frombuffer(b, np.uint8).reshape(-1, 4).T.copy().tobytes()
        parts.append(shuffled)
        layout.append({"name": col, "kind": "f32shuf", "offset": offset})
        offset += len(shuffled)
    for key, col in PRED_COLS.items():
        q = np.round(preds[col].to_numpy("float64") * 1000).astype(np.int64)
        d = np.diff(q, prepend=0).astype("<i4")
        parts.append(d.tobytes())
        layout.append({"name": key, "kind": "i32delta_milli", "offset": offset})
        offset += d.nbytes
    blob = base64.b64encode(gzip.compress(b"".join(parts), compresslevel=9, mtime=0)).decode("ascii")

    meta = json.loads((config.MODELS_DIR / "model_metadata.json").read_text(encoding="utf-8"))
    features = meta["features"]
    mlp_pipe = joblib.load(config.MODELS_DIR / "m6_mlp_64_32.joblib")
    ridge_pipe = joblib.load(config.MODELS_DIR / "m3_ridge.joblib")
    scale, mlp = mlp_pipe.named_steps["scale"], mlp_pipe.named_steps["model"]
    assert list(scale.feature_names_in_) == features
    assert mlp.activation == "relu" and mlp.out_activation_ == "identity"
    mlp_json = {"mean": scale.mean_.tolist(), "scale": scale.scale_.tolist(),
                "layers": [{"in": int(W.shape[0]), "out": int(W.shape[1]), "W": f32_list(W), "b": f32_list(b)}
                           for W, b in zip(mlp.coefs_, mlp.intercepts_)]}
    rscale, ridge = ridge_pipe.named_steps["scale"], ridge_pipe.named_steps["model"]
    ridge_json = {"mean": rscale.mean_.tolist(), "scale": rscale.scale_.tolist(),
                  "coef": f32_list(ridge.coef_), "intercept": f32_list([ridge.intercept_])[0]}

    # re-run the page's maths in numpy against the saved predictions
    X = browser_features(test, features)
    h = (X - np.array(mlp_json["mean"])) / np.array(mlp_json["scale"])
    for k, layer in enumerate(mlp_json["layers"]):
        h = h @ np.array(layer["W"]).reshape(layer["in"], layer["out"]) + np.array(layer["b"])
        h = np.maximum(h, 0) if k < len(mlp_json["layers"]) - 1 else h
    z = (X - np.array(ridge_json["mean"])) / np.array(ridge_json["scale"])
    ridge_out = z @ np.array(ridge_json["coef"]) + ridge_json["intercept"]
    diff_mlp = np.abs(h[:, 0] - preds["pred_m6"].to_numpy()).max()
    diff_ridge = np.abs(ridge_out - preds["pred_m3"].to_numpy()).max()
    print(f"page maths vs saved predictions: MLP {diff_mlp:.4f} °C, Ridge {diff_ridge:.4f} °C")
    assert diff_mlp < 0.05 and diff_ridge < 0.05

    per = pd.read_csv(R / "test_metrics_per_profile.csv")
    sessions = []
    for pid in split["test_profiles"]:
        idx = np.flatnonzero(test[config.GROUP].to_numpy() == pid)
        rows = per[per["profile_id"] == pid].set_index("model")
        sessions.append({"id": int(pid), "start": int(idx[0]), "rows": int(len(idx)),
                         "hours": float(rows["hours"].iloc[0]), "peak": float(rows["winding_max"].iloc[0]),
                         "rmse": {k: float(rows.loc[name, "rmse"]) for k, name in MODEL_NAMES.items()}})

    train = raw[raw[config.GROUP].isin(split["train_profiles"])]
    train_range = {c: [float(train[c].min()), float(train[c].max())] for c in config.INPUTS}
    evaluation, modelling = read_json("evaluation_summary.json"), read_json("modelling_summary.json")
    eda, check = read_json("eda_summary.json"), read_json("data_check_summary.json")
    payload = {
        "n": n, "layout": layout, "features": features, "inputs": list(config.INPUTS),
        "mlp": mlp_json, "ridge": ridge_json, "sessions": sessions, "trainRange": train_range,
        "presets": _eval_presets_from_app(),
        "facts": {"rows": check["n_rows"], "sessions": check["n_profiles"], "hours": check["total_hours"],
                  "testRows": evaluation["test_rows"], "testShare": split["test_share_of_rows"],
                  "trainSessions": len(split["train_profiles"]), "testOpened": evaluation["test_opened_at"],
                  "lagMin": eda["thermal_lag"]["median_best_lag_min"]},
        "targets": evaluation["targets"],
        "test": pd.read_csv(R / "test_metrics.csv")[["model", "rmse", "mae", "r2"]].to_dict("records"),
        "memory": pd.read_csv(R / "memory_curve.csv")[["memory", "cv_rmse"]].to_dict("records"),
        "ablation": pd.read_csv(R / "ablation.csv")[["variant", "cv_rmse"]].to_dict("records"),
        "safety": {"sigma": float(modelling["oof_best"]["residual_std"]),
                   "tHot": float(eda["target_train_stats"]["90%"]),
                   "table": pd.read_csv(R / "safety_alarm.csv")[["k", "caught_pct", "false_alarm_pct"]].to_dict("records")},
        "pythonCheck": {"mlp": float(diff_mlp), "ridge": float(diff_ridge)},
    }

    src = HERE / "src"
    page = (src / "index.html").read_text(encoding="utf-8")
    parts = {"/*CSS*/": (src / "style.css").read_text(encoding="utf-8"),
             "/*APP*/": (src / "app.js").read_text(encoding="utf-8"),
             "DATA_BLOB": blob,
             "/*META*/": json.dumps(payload, separators=(",", ":"))}
    for key, value in parts.items():
        assert page.count(key) == 1, key
        page = page.replace(key, re.sub(r"</(script)", r"<\\/\1", value, flags=re.I))
    out = HERE / "index.html"
    out.write_text(page, encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1e6:.1f} MB)")


def _eval_presets_from_app():
    """The typical operating points of the Streamlit app, read from app.py so both demos use the same ones."""
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "PRESETS":
            return _eval_presets(node.value)
    raise ValueError("PRESETS not found in app.py")


if __name__ == "__main__":
    main()
