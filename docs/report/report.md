# Machine-learning virtual sensor for electric-motor winding temperature

**UCS321 AI for Engineers · MST mini project, statement #6 (GE Power Systems scenario)** · TIET Patiala, B.E. ECE, Semester III · Team of 5 (see the contributions section)

> Every number in this report is copied from a file in `outputs/results/` (named in brackets), produced by the notebooks in `notebooks/`. The full step-by-step reasoning is in `LOG.md`.

## Abstract
We built a supervised regression model that estimates the **stator winding temperature** of a permanent-magnet synchronous motor from signals its controller already measures: ambient and coolant temperature, d/q voltages and currents, speed and torque. This is a "virtual sensor".
- **Data:** the public Paderborn University test-bench dataset (Kaggle, version 3; 1,330,816 rows at 2 Hz in 69 sessions, 184.84 h).
- **Features:** 45 inputs, i.e. 5 physics features (current², power) and 32 exponentially weighted moving averages (EWMA) that give the model a "thermal memory" of the last 1–45 minutes.
- **Models:** compared with session-wise 5-fold cross-validation. The engineered features cut the linear model's error from 16.09 °C to 5.18 °C.
- **Result:** on 6 held-out test sessions, used once, the pre-registered final model (an MLP) reached RMSE 6.00 °C (MAE 3.69 °C, R² 0.946), meeting both success targets. The other finalists, Ridge (4.97 °C) and LightGBM (5.11 °C), did better.
- **Limitations:** errors concentrate at session starts and at high temperatures, where the model tends to under-predict. A safety margin addresses this.
- **Innovation:** an ablation study, a memory curve, a safety-aware alarm, a data-efficiency study and a Streamlit replay demo.

## 1. Problem understanding and objective (rubric: 5 marks)
- **Why it matters:** insulation life roughly halves for every 10 °C rise. Insulation classes set maximum hot-spot temperatures (A 105, E 120, B 130, F 155, H 180 °C). Overheating destroys motors, while over-caution (derating) wastes performance [1, 2].
- **Why a model:** a sensor inside the winding is costly, needs wiring and can fail. The controller already measures currents, voltages and speed, and the dataset authors note such inputs "are commonly accessible in real-world traction drive systems" [3].
- **Objective:** estimate the current `stator_winding` temperature (°C) by supervised regression from 8 measured signals and their engineered features. `pm`, `stator_tooth` and `stator_yoke` are excluded, because a motor with those sensors wouldn't need the model (leakage).
- **Honesty about scope:** GE is the assignment's scenario; the data comes from a 50 kW research PMSM at Paderborn. We estimate the temperature *now*, not the future, and we do not predict failures. Details: `docs/problem.md`.

## 2. Data collection and pre-processing (rubric: 10 marks)
**2.1 Source and quality** (`data_check_summary.json`, `data/README.md`)
- Kaggle `wkirgsn/electric-motor-temperature`, version 3. `measures_v2.csv` is 300.1 MB, SHA-256 `78f3d150…67d3ad`.
- **Shape:** 1,330,816 × 13; 69 sessions (IDs 2–81); 184.84 h; sessions 0.302–6.107 h long.
- **Quality:** 0 missing values, 0 duplicate rows. All temperatures plausible (winding 18.59–141.36 °C).
- **No timestamp, so we tested time order:** each session is one unbroken block, and the median row-to-row winding change is 0.022 °C in file order vs 28.85 °C after shuffling. So file order = time order.
- **Storage:** a float32 parquet copy cut RAM from 138.4 to 74.5 MB; the largest value change was 0.000244 rpm.

**2.2 Split before exploring** (`split_profiles.json`)
- Two random sessions per length tertile (seed 42), accepted only if they make up 10–15 % of rows and include a hot and a cool session.
- **Test = sessions 6, 7, 21, 61, 66, 81** (141,024 rows, 10.60 %), frozen before any EDA. Training = 63 sessions, 1,189,792 rows.

**2.3 Visualisation / EDA on training sessions** (`eda_summary.json`, figures `eda_01`–`eda_08`)
- **Leakage proof:** r with the target is 0.970 (stator_tooth), 0.862 (yoke) and 0.796 (pm), while the best allowed input reaches |r| = 0.632 (i_d).
- **Thermal lag:** across 53 sessions, current² explains the winding best when the temperature is shifted a median 2.5 min later (r 0.645 → 0.746).
- **Coolant:** the winding is a median 26.47 °C above the coolant, but below it in 4.75 % of rows (the winding lags coolant changes).
- **Torque ≈ i_q** (r = 0.9965). Session medians range from 19.88 to 116.74 °C.

**2.4 Cleaning and features** (`features_summary.json`, `feature_list.json`)
- **Cleaning:** none needed (re-checked in code). Row order kept; 5 plausible ambient dips kept.
- **Physics features:** i_s = √(i_d²+i_q²), u_s, i_s², p_el = 1.5(u_d i_d + u_q i_q), p_mech = T·n·2π/60.
- **EWMA memory:** 8 signals × spans of 120/600/1800/5400 samples (1/5/15/45 min), per session and past-only. A causality test gave a maximum difference of 0.0. That makes **45 inputs**.
- **Effect:** the best memory feature (`i_s_ewma_600`, r = 0.705) beats raw i_s (0.583).
- **Scaling:** StandardScaler inside sklearn Pipelines (linear models, MLP). Trees are unscaled.

## 3. Model development and implementation (rubric: 12 marks)
- **Protocol** (`cv_results.csv`, `modelling_summary.json`): GroupKFold(5) by session on every 10th training row (118,980 rows; thinning measured to cost nothing: 5.146 vs 5.061 °C). Every model saw the same rows and folds. RMSE is the selection metric. No random early stopping.
- **Results (CV RMSE mean ± std, °C):**

| Model | CV RMSE | Training RMSE | Notes |
|---|---|---|---|
| B0 training mean | 29.09 ± 1.26 | 28.96 | dumbest baseline |
| B1 coolant + offset | 26.03 ± 1.64 | 25.94 | physics-naive baseline |
| M1 Linear, 8 raw | 16.09 ± 1.60 | 15.55 | |
| M2 Linear, 45 features | 5.18 ± 0.56 | 4.99 | features: −68 % error |
| M3 Ridge (α = 10) | 5.17 ± 0.58 | 4.99 | |
| M3 Lasso (α = 0.01) | 5.20 ± 0.62 | 5.05 | dropped 11 features |
| M4 Random Forest | 5.82 ± 0.84 | 2.33 | overfits sessions |
| M5 LightGBM | 5.06 ± 0.84 | 1.14 | overfits sessions |
| M6 MLP (64-32) | **4.92 ± 0.76** | 2.66 | |

- **Tuning:** ParameterSampler (seed 42) with 4 Random Forest and 8 LightGBM configurations; 6 Ridge and 3 Lasso α values (`tuning_*.csv`).
- **Finalists (rule fixed in advance):** MLP (best), LightGBM (best other family), Ridge (best linear). Five models were within 0.3 °C, less than the fold spread.
- **Success target (fixed before testing):** test RMSE ≤ 6.5 °C, and ≤ 13.02 °C (half of B1).

## 4. Performance evaluation and interpretation (rubric: 8 marks)
**Test set used once, at 2026-10-10 09:24:52** (`evaluation_summary.json`, `test_metrics.csv`, `test_metrics_per_profile.csv`, figures `eval_01`–`eval_12`).

| Model | Test RMSE | MAE | R² | p95 |e| | Mean signed | Session-mean MAE |
|---|---|---|---|---|---|---|
| M3 Ridge | **4.97** | 2.99 | 0.963 | 9.03 | +0.38 | 2.85 |
| M5 LightGBM | 5.11 | **2.86** | 0.961 | 9.88 | −0.87 | **2.38** |
| M6 MLP (final) | 6.00 | 3.69 | 0.946 | 14.60 | −1.95 | 2.99 |
| B1 coolant + offset | 24.48 | 20.15 | 0.106 | 50.92 | +2.40 | 19.54 |
| B0 mean | 25.94 | 22.22 | −0.004 | 45.96 | −1.63 | 23.08 |

- **Targets met** (6.00 ≤ 6.5 °C). 54.5 % of the MLP's estimates are within ±2 °C and 75.6 % within ±5 °C.
- **Generalisation gap:** MLP +1.09 °C, LightGBM +0.04, Ridge −0.21. CV could not separate the top models, and one hard session (6: RMSE 9.43 °C, high coolant under load) hurt the MLP most. We did **not** re-select after seeing the test. Lesson: pre-register a "simplest model within one CV std" rule, which would have chosen Ridge.
- **Failure modes:**
  - **Session starts:** the EWMA starts at the current value, so a cold motor under sudden load looks hot (+60.31 °C at minute 0 of session 21).
  - **Hot temperatures:** above 90 °C the MLP under-predicts by about 6 °C. In 52.0 % of hot rows (≥ 104.79 °C) it is more than 5 °C too low (LightGBM 27.0 %).
- **Physics check** (grouped permutation importance, RMSE increase in °C): coolant 19.67 > voltage 16.11 > speed 15.40 > current 11.32 > power 8.96 > torque 2.45 > ambient 0.52. This is consistent with coolant setting the floor, I²R heating, and speed-dependent iron losses.

## 5. Innovation and creativity (rubric: 5 marks)
All the experiments use the final MLP, the same 118,980 training rows and the same session folds. The test set is not re-used (`innovation_summary.json`, figures `innov_01`–`innov_04`).

- **I1. Ablation.** CV RMSE (°C) for each input set:

  | Variant | Features | CV RMSE (°C) | vs full |
  |---|---|---|---|
  | full | 45 | 4.92 | — |
  | no EWMA memory | 13 | 13.18 | **+8.26** |
  | no physics features | 24 | 6.56 | +1.64 |
  | no torque | 39 | 4.81 | −0.11 |
  | raw only | 8 | 13.41 | +8.49 |
  | with forbidden temperatures | 48 | 1.15 | −3.77 (the cheat) |

  The memory features are the most valuable idea. Torque is redundant (≈ i_q). Adding the neighbouring sensors makes the task trivial, which proves they must be excluded.
- **I2. Thermal-memory curve.** CV RMSE: 13.18 (no memory) → 9.17 (1 min) → 5.16 (+5 min) → 5.00 (+15 min) → 4.92 °C (+45 min). Five minutes of memory gives most of the gain, consistent with the 2.5-minute median lag found in EDA.
- **I3. Safety-aware alarm.** Alarm if estimate + k·σ ≥ 104.79 °C, with σ = 4.959 °C (out-of-fold, training sessions only). Hot rows caught: 57.2 % → 66.4 % → 70.0 % for k = 0 / 1 / 2. False alarms: 0.70 % → 2.30 % → 5.84 %. Precision: 90.4 % → 76.8 % → 57.9 % (`safety_alarm.csv`). The margin trades false alarms for caught overheating, and even k = 2 misses 30 % of hot rows, because the MLP under-reads when hot. The first 5 minutes of each test session (2.55 % of rows) have MAE 12.34 °C vs 3.47 °C afterwards (`session_start_errors.csv`): the EWMA warm-up artefact.
- **I4. Data efficiency.** On a fixed validation set (13 of the 63 training sessions), the validation RMSE was 9.56 °C with 12 sessions, 6.36 with 25, 5.18 with 38 and 4.66 with 50. Still falling, so more recorded sessions would help.
- **I5. Streamlit replay demo** (`app.py`). It replays a test session through the saved model, with a live estimate, the real sensor for comparison, the margin line and an alarm lamp. It falls back to the saved predictions if the model files are absent.

## 6. Limitations and future work
- **One test-bench motor:** new motors or vehicles need new data and validation.
- **No data above 141.36 °C.**
- **Session-start artefact:** future work could initialise the EWMA from a known idle state.
- **Under-prediction when hot.**
- **Recorded replay, not hardware.**
- **Future work:**
  - pre-registered simplicity rule;
  - EWMS (moving standard deviation) features;
  - a no-torque deployment model;
  - a comparison with a first-order physics thermal model;
  - uncertainty-aware estimates.

## 7. References
1. Wikipedia, "Insulation system" (IEC 60085 thermal classes; 10 °C rule of thumb).
2. E. Cowern, "The Hot Issue of Motor Temperature Ratings", EC&M, 2000.
3. W. Kirchgässner, O. Wallscheid, J. Böcker, "Data-Driven Permanent Magnet Temperature Estimation in Synchronous Motors with Supervised Machine Learning: A Benchmark", IEEE Trans. Energy Conversion, 2021 (arXiv:2001.06246).
4. Dataset: "Electric Motor Temperature", Kaggle `wkirgsn/electric-motor-temperature`, version 3.

## 8. Team contributions
| Member | Owned stage | Presents |
|---|---|---|
| A: Arnav | Phases 0–1, coordinator (repo, flow diagram, slides, cross-check) | Title, problem, dataset, flow diagram |
| B: ____ | Phase 2 EDA (run ahead by Arnav; reviewed by B) | EDA |
| C: ____ | Phase 3 features | Pre-processing & features |
| D: ____ | Phase 4 models | Models & CV results |
| E: ____ | Phase 5 evaluation, safety alarm, demo | Results, safety, demo |
