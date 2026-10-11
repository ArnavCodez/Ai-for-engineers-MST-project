"""Model helpers: the coolant baseline, error metrics and session-aware cross-validation."""
import time

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.model_selection import GroupKFold


class CoolantPlusOffset(BaseEstimator, RegressorMixin):
    """Baseline B1: winding temperature = coolant temperature + one constant offset.

    The only class in the project. It exists so this physics-naive baseline can go
    through exactly the same cross-validation code as the real models.
    """

    def fit(self, X, y):
        self.offset_ = float(np.mean(np.asarray(y) - X["coolant"].to_numpy()))
        return self

    def predict(self, X):
        return X["coolant"].to_numpy() + self.offset_


def regression_metrics(y_true, y_pred):
    """All the error numbers we report, in °C (MSE in °C²). error = predicted - actual."""
    y_true = np.asarray(y_true, dtype="float64")
    y_pred = np.asarray(y_pred, dtype="float64")
    error = y_pred - y_true
    ss_res = float(np.sum(error ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    return {
        "mse": float(np.mean(error ** 2)),
        "rmse": float(np.sqrt(np.mean(error ** 2))),
        "mae": float(np.mean(np.abs(error))),
        "r2": 1 - ss_res / ss_tot if ss_tot > 0 else float("nan"),
        "max_abs_error": float(np.max(np.abs(error))),
        "p95_abs_error": float(np.percentile(np.abs(error), 95)),
        "mean_signed_error": float(np.mean(error)),
    }


def group_cv(model, X, y, groups, n_splits=5):
    """GroupKFold cross-validation: every session stays inside one fold.

    Returns (per-fold metrics DataFrame, out-of-fold predictions array).
    The model is cloned for every fold, so nothing is shared between folds.
    """
    folds = GroupKFold(n_splits=n_splits)
    oof = np.full(len(y), np.nan)
    rows = []
    for fold, (train_idx, val_idx) in enumerate(folds.split(X, y, groups)):
        fold_model = clone(model)
        start = time.time()
        fold_model.fit(X.iloc[train_idx], y.iloc[train_idx])
        fit_seconds = time.time() - start
        pred = fold_model.predict(X.iloc[val_idx])
        oof[val_idx] = pred
        m = regression_metrics(y.iloc[val_idx], pred)
        # error on the rows the model was trained on: compare with val error to spot overfitting
        m["train_rmse"] = regression_metrics(y.iloc[train_idx], fold_model.predict(X.iloc[train_idx]))["rmse"]
        m["fold"] = fold
        m["fit_seconds"] = fit_seconds
        rows.append(m)
    return pd.DataFrame(rows), oof


def summarise_cv(name, fold_table, n_features):
    """One row of the CV results table (mean ± std over the folds)."""
    return {
        "model": name,
        "rmse_mean": fold_table["rmse"].mean(),
        "rmse_std": fold_table["rmse"].std(ddof=0),
        "mae_mean": fold_table["mae"].mean(),
        "r2_mean": fold_table["r2"].mean(),
        "max_abs_error_mean": fold_table["max_abs_error"].mean(),
        "train_rmse_mean": fold_table["train_rmse"].mean(),
        "fit_seconds_per_fold": fold_table["fit_seconds"].mean(),
        "n_features": n_features,
    }
