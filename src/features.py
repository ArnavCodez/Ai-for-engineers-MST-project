"""Feature engineering: physics features and EWMA "thermal memory" features.

The SAME functions are used for training, evaluation and the demo app, so a
model always gets its inputs built in exactly the same way.

Important rules (plan nuances N3 and N9):
- the DataFrame must be in the file's original row order (= time order);
- EWMA is computed separately for every session (profile_id);
- EWMA only uses the current and PAST rows of a session (pandas ewm is causal).
"""
import numpy as np

from src import config

# EWMA spans in samples. At 2 Hz: 120 = 1 min, 600 = 5 min, 1800 = 15 min, 5400 = 45 min
EWMA_SPANS = [120, 600, 1800, 5400]

# Signals that get EWMA "memory" versions
EWMA_BASES = ["i_s", "i_s_sq", "p_el", "u_s", "motor_speed", "torque", "coolant", "ambient"]

# Physics features built from the raw signals
PHYSICS = ["i_s", "u_s", "i_s_sq", "p_el", "p_mech"]


def ewma_name(col, span):
    return f"{col}_ewma_{span}"


def add_physics_features(df):
    """Add current/voltage magnitude, current squared, electrical and mechanical power."""
    i_d = df["i_d"].astype("float64")
    i_q = df["i_q"].astype("float64")
    u_d = df["u_d"].astype("float64")
    u_q = df["u_q"].astype("float64")

    out = df.copy()
    out["i_s"] = np.sqrt(i_d ** 2 + i_q ** 2)              # current magnitude (A)
    out["u_s"] = np.sqrt(u_d ** 2 + u_q ** 2)              # voltage magnitude (V)
    out["i_s_sq"] = out["i_s"] ** 2                        # proportional to copper loss I²R (A²)
    out["p_el"] = 1.5 * (u_d * i_d + u_q * i_q)            # electrical power in the dq frame (W)
    out["p_mech"] = df["torque"].astype("float64") * df["motor_speed"].astype("float64") * 2 * np.pi / 60  # W

    for col in PHYSICS:
        out[col] = out[col].astype("float32")
    return out


def add_ewma_features(df, spans=EWMA_SPANS, bases=EWMA_BASES):
    """Add an EWMA column for every (base signal, span), computed per session, past only."""
    out = df.copy()
    groups = out.groupby(config.GROUP, sort=False)
    for col in bases:
        for span in spans:
            ewma = groups[col].transform(lambda s, sp=span: s.ewm(span=sp, adjust=True).mean())
            out[ewma_name(col, span)] = ewma.astype("float32")
    return out


def build_features(df):
    """Physics features first, then EWMA features. df must be in original row order."""
    return add_ewma_features(add_physics_features(df))


def feature_sets():
    """The named input lists used by models and the ablation study (Phase 6)."""
    raw = list(config.INPUTS)
    ewma_all = [ewma_name(c, s) for c in EWMA_BASES for s in EWMA_SPANS]
    full = raw + PHYSICS + ewma_all

    raw_bases = [c for c in EWMA_BASES if c in raw]
    ewma_raw_only = [ewma_name(c, s) for c in raw_bases for s in EWMA_SPANS]
    torque_cols = {"torque", "p_mech"} | {ewma_name("torque", s) for s in EWMA_SPANS}

    return {
        "raw": raw,
        "full": full,
        "no_ewma": raw + PHYSICS,
        "no_engineered": raw + ewma_raw_only,
        "no_torque": [c for c in full if c not in torque_cols],
        "with_leakage": full + list(config.FORBIDDEN),
    }
