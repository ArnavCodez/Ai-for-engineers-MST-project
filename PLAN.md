# MST Project: Electric Motor Winding Temperature Prediction

**UCS321 AI for Engineers, MST mini project, statement #6**

## Phase checklist (tick when acceptance criteria are met)

- [x] Phase 0: Setup & data check (done 2026-10-07, Arnav)
- [x] Phase 1: Problem understanding (done 2026-10-07, Arnav)
- [x] Phase 2: Exploratory data analysis (EDA) (done 2026-10-07, run by Arnav for owner B; B to review)
- [ ] Phase 3: Pre-processing & feature engineering
- [ ] Phase 4: Model development
- [ ] Phase 5: Evaluation & interpretation (the test set is used here, once)
- [ ] Phase 6: Innovation extras
- [ ] Phase 7: Deliverables & viva prep

> Before every phase, read `CONTRIBUTING.md` (especially section 4: logging) and the last entries of `LOG.md`.

> **Plan v2 (2026-10-07).** We compared this plan with the team's "Motor Temperature Project Master Guide" (Word doc) and kept this plan as the base, because its core idea (EWMA thermal-memory features) is what the dataset's own authors use. We merged in the Guide's best ideas, each marked **[v2]** below:
> 1. Test sessions are frozen **before** EDA, and EDA uses training sessions only (Phase 2.0).
> 2. One shared contract file, `src/config.py` (target, inputs, forbidden columns, seed, paths), used by every notebook and the app.
> 3. Extra test metrics: 95th-percentile absolute error, mean signed error, and the unweighted mean of per-session MAE (Phase 5).
> 4. The Streamlit replay demo is a **core** deliverable, and its owner builds the app shell early, in parallel (Phase 6).
> 5. Provenance file `data/README.md` with the SHA-256 checksum; a fallback priority order; a defined "handoff package".
> The full comparison is in `LOG.md` (2026-10-07 16:40).

---

## The problem statement (verbatim)

> General Electric (GE) Power Systems aims to improve the operational reliability of its electric motors by predicting winding temperatures under diverse working conditions. Using a dataset containing parameters such as ambient temperature, motor speed, load torque, supply voltage, and current, students will develop a supervised machine learning regression model to estimate motor temperature.

**What we are building, in one line:** a **"virtual temperature sensor"**, a regression model that estimates the **stator winding temperature (°C)** of a real motor from signals that are cheap to measure: ambient and coolant temperature, voltages, currents, speed and torque.

### Rubric map (40 marks + 20 viva)

| Rubric item | Marks | Where we earn it |
|---|---|---|
| Problem understanding & objective clarity | 5 | Phase 1 |
| Data collection & pre-processing | 10 | Phases 0, 2, 3 |
| Model development & implementation | 12 | Phase 4 |
| Performance evaluation & interpretation of results | 8 | Phase 5 |
| Innovation / creativity in approach | 5 | Phase 6 |
| Presentation / viva | 20 | Phase 7 + all the logs |

**Required by the instructions:** a **flow diagram** in which the pre-processing and visualisation steps are clearly documented (Phase 7).

---

## Dataset

- **Name:** "Electric Motor Temperature" on Kaggle, by wkirgsn (Paderborn University, LEA department): https://www.kaggle.com/datasets/wkirgsn/electric-motor-temperature
- **File to use:** `measures_v2.csv`
- **What it is:** about **185 hours** of recordings from a **PMSM** (permanent magnet synchronous motor) on a test bench, sampled at **2 Hz** (one row every 0.5 s). That gives roughly **1.3 million rows** in **69 measurement sessions**, each identified by `profile_id`. Verify these numbers in Phase 0 and log the real values.

| Column | Meaning | Unit | Our use |
|---|---|---|---|
| `u_d`, `u_q` | Voltage, d- and q-components (rotating dq frame) | V | input |
| `i_d`, `i_q` | Current, d- and q-components | A | input |
| `motor_speed` | Rotor speed | rpm | input |
| `torque` | Torque | Nm | input (see nuance N4) |
| `coolant` | Coolant temperature | °C | input |
| `ambient` | Ambient temperature | °C | input |
| **`stator_winding`** | **Stator winding temperature** | °C | **TARGET** |
| `stator_tooth`, `stator_yoke`, `pm` | Other measured temperatures (stator tooth, stator yoke, permanent magnet) | °C | **NOT inputs** (leakage, see N1) |
| `profile_id` | Session ID | — | used only for grouping and splitting, **never as a feature** |

---

## Key nuances (read these before writing any code; log each one as a `[NUANCE]` when it shows up)

- **N1. Leakage via the other temperatures.** `stator_tooth`, `stator_yoke` and `pm` are temperatures measured right next to the winding. A real motor in a car or plant wouldn't have them, which is the whole point of a virtual sensor. With them as inputs the task becomes trivial (R² ≈ 1) and meaningless. **Drop them as inputs.** In Phase 6 we *show* what happens with them included, to justify dropping them.
- **N2. Rows are not independent.** Neighbouring rows are 0.5 s apart and almost identical. A random train/test split puts near-copies of the same moment in both sets, which gives fake, inflated accuracy. **Split by whole `profile_id`**, using a held-out test set of whole profiles and `GroupKFold` for cross-validation.
- **N3. Thermal memory.** Temperature depends on how hard the motor worked over the last minutes, not just on this instant (thermal inertia, like a pressure cooker that stays hot after you switch off the gas). So we add **EWMA (exponentially weighted moving average)** features. They must be computed:
  - **per profile**, so they never mix two sessions;
  - **causally**, using only past values, never future ones;
  - **before** any subsampling or shuffling.
- **N4. Torque.** In real vehicles torque is usually *estimated*, not measured. Check the dataset description on Kaggle for any note on this. Run an ablation with and without `torque` (Phase 6) and log it.
- **N5. Profiles are very different.** Some sessions are short, others are long random walks over the whole operating range. Choose test profiles that are representative, and report **per-profile** errors, not only the overall average.
- **N6. Size.** 1.3M rows is fine for linear models. Random Forest on all rows can be slow or run out of memory on a laptop. If so, subsample the *training* rows (e.g. keep every 4th row), but only **after** the EWMA features are computed. Always evaluate on full-resolution test data. Log the effect.
- **N7. Physics sanity check.** More current means more copper loss (I²R), which means a hotter winding. Coolant temperature sets the "floor". If a model's feature importance contradicts physics, investigate before trusting it.
- **N8. Errors are not equally bad.** **Under**-predicting temperature is worse than over-predicting, because the motor could overheat while the model says "fine". Report the maximum error and the under-prediction at high temperatures.
- **N9. No timestamp column.** We assume the file's row order *is* time order within each profile, so **never sort or shuffle before computing time features**. Log this assumption.

---

## Tech stack

`python 3.11`, `numpy`, `pandas`, `pyarrow` (parquet files), `matplotlib`, `seaborn`, `scikit-learn`, `lightgbm` (or `xgboost`), `joblib`, `jupyter`, `nbconvert`. Optional: `shap`, `streamlit`, `kaggle`.

## Folder layout (create in Phase 0)

```
MST_Motor_Temperature/
  PLAN.md  LOG.md  CONCEPTS.md  VIVA_QA.md
  requirements.txt  .gitignore
  data/README.md            [v2] provenance, checksum, download steps (the only tracked file in data/)
  data/raw/                 measures_v2.csv (never modified)
  data/processed/           parquet files, feature lists
  notebooks/                01_data_check, 02_eda, 03_preprocessing_features, 04_modelling, 05_evaluation, 06_innovation
  src/                      config.py [v2] (shared contract), download_data.py, features.py, plotting.py, metrics.py (small helpers)
  app.py                    [v2] Streamlit replay demo (Phase 6, core)
  outputs/figures/          all PNGs
  outputs/results/          CSV/JSON results, split_profiles.json, pip_freeze.txt
  outputs/models/           saved models (.joblib), git-ignored
  docs/                     problem.md, flow_diagram.md (+ .png), report/, slides/
```

---

## Phase 0: Setup & data check

**Tasks**
1. Create the folder layout above.
2. Create `.gitignore` covering `.venv/`, `data/`, `outputs/models/` and `.ipynb_checkpoints/`.
3. Write `requirements.txt`, create `.venv`, install the packages, and save `pip freeze` to `outputs/results/pip_freeze.txt`.
4. Download `measures_v2.csv` into `data/raw/`, using the Kaggle API or a manual browser download.
5. Build `notebooks/01_data_check.ipynb`:
   - load the CSV; print the shape, dtypes, `head()` and memory usage;
   - count unique `profile_id`s and rows per profile (min / median / max, in rows **and** in hours);
   - check missing values per column and duplicate rows;
   - run `describe()` and sanity-check the ranges (temperatures in °C, speed in rpm);
   - save `data/processed/measures_v2.parquet` with float columns cast to `float32`, and log the memory saved.

**Acceptance criteria**
- [x] The environment installs cleanly; Python and library versions are logged.
- [x] The data loads; the real shape, number of profiles and hours are logged (expected ≈ 1.3M × 13 and 69 profiles; if different, log why, e.g. a different dataset version).
- [x] Missing, duplicate and range checks are done, with results logged.
- [x] `LOG.md` has entries for setup and the data check.
- [x] `CONCEPTS.md` has: PMSM; dq frame / Park transform (simple version: "turning 3-phase AC into two steady DC-like values"); sampling rate; parquet vs CSV.

---

## Phase 1: Problem understanding (5 marks)

**Task:** write `docs/problem.md` (about 1–1.5 pages, simple English):
- **Why winding temperature matters:**
  - winding insulation ages much faster when hot;
  - every insulation class has a maximum temperature (e.g. Class F = 155 °C, Class H = 180 °C);
  - overheating leads to insulation breakdown and motor failure;
  - being too cautious (running the motor below its capability, called "derating") wastes performance.
- **Why a model instead of more sensors:**
  - sensors cost money and need wiring;
  - they can fail;
  - they can't be placed everywhere;
  - a **virtual sensor (soft sensor)** reuses signals the motor controller already has.
- **Objective:** regression. Input = the 8 measured signals (plus the features we engineer); output = `stator_winding` in °C.
- **Success criteria:**
  - clearly beat the baselines from Phase 4;
  - generalise to *unseen operating sessions* (hence the split by profile);
  - stay cheap enough to run on a motor controller (so a simpler model wins if its accuracy is close).
  - Set the numeric target **after** the Phase 4 baselines and log it as a `[DECISION]`.
- **Who uses it:** GE motor/drive engineers (protection, derating) and maintenance teams.
- **Constraints and assumptions:** test-bench data (not field data), one motor type, the file's row order taken as time order (N9).

**Acceptance criteria**
- [x] `docs/problem.md` is written.
- [x] A `LOG.md` entry exists.
- [x] At least 5 motivation and domain questions are added to `VIVA_QA.md`.

---

## Phase 2: EDA (part of the 10 pre-processing marks; visualisation is explicitly required)

**Notebook:** `notebooks/02_eda.ipynb`. For heavy plots, use `hexbin` or a random sample of rows. Save every figure to `outputs/figures/eda_XX_*.png`.

**2.0 [v2] Freeze the test sessions first** (moved here from Phase 3.2):
- Create `src/config.py` with `TARGET`, `INPUTS`, `FORBIDDEN` (leakage columns), `GROUP`, `SEED`, `SAMPLE_RATE_HZ` and the paths.
- Pick about 10–15% of rows as whole test sessions with `SEED = 42`. Stratify by session length so short and long sessions are both represented, then check the temperature coverage. Save the IDs to `outputs/results/split_profiles.json`.
- **All EDA below uses training sessions only.** The test sessions stay unseen until Phase 5, so nothing we learn from them can sneak into feature or model choices. Figure 1 may *mark* which sessions are test (that's only their length), but never plots their signals.

**Required figures**
1. Rows (or hours) per profile, as a sorted bar chart. Shows the session-length imbalance (N5).
2. One long profile over time (x-axis in minutes): the inputs and `stator_winding` in stacked subplots.
3. A histogram of every column, noting the ranges.
4. A correlation heatmap (Pearson) of all numeric columns, **including** the leakage temperatures, to show *why* they leak (N1).
5. Hexbin plots: `stator_winding` vs current magnitude √(i_d² + i_q²), and `stator_winding` vs `coolant`.
6. The operating region: `motor_speed` vs `torque`, coloured by `stator_winding`.
7. Boxplots of `stator_winding` per profile (or for 15–20 sample profiles).
8. **The thermal lag picture:** current² and winding temperature on the same time axis for one profile. The temperature visibly *lags* the current. This is the motivation for EWMA (N3). Optional: a cross-correlation plot showing the lag in minutes.

**Write observations:** 1–2 bullets per figure in the notebook and in `LOG.md` (`[EDA]` tag).

**Acceptance criteria**
- [x] At least 8 figures are saved, each described in `LOG.md`.
- [x] A short "Top 5 EDA insights" list is in `LOG.md` and in the notebook.
- [x] Concepts added: correlation (and why it is not causation), hexbin, distribution and outlier.
- [x] [v2] Test sessions frozen before EDA (`outputs/results/split_profiles.json`); `src/config.py` created.
- [x] Showcase: `docs/showcase/index.html` (interactive EDA explorer; published online; ask Arnav for the link).

---

## Phase 3: Pre-processing & feature engineering (10 marks)

**Notebook:** `notebooks/03_preprocessing_features.ipynb`. Helper functions go in `src/features.py`.

### 3.1 Cleaning
- Handle missing values if any exist: drop them, or interpolate **within the profile only**. Log the choice.
- Remove exact duplicate rows if any exist.
- Check physical plausibility ranges and log any odd values. Don't delete real extreme operating points.
- **Keep row order inside each profile.** Never shuffle at this stage (N9).

### 3.2 Split design (`[DECISION]`)
- **[v2] The test set is already frozen in Phase 2.0.** Load it from `outputs/results/split_profiles.json`. Never re-draw it. The bullets below describe how it was made.
- **Test set:** hold out whole profiles worth about 10–15% of the rows (typically 5–7 profiles).
  - Pick them with `SEED = 42`, then check they cover short and long sessions and low and high temperatures. If not, re-pick and log why.
  - Save the lists to `outputs/results/split_profiles.json`.
  - **Don't compute any test metrics until Phase 5.**
- **Training profiles:** use `GroupKFold(n_splits=5)` with `groups = profile_id` for all cross-validation and tuning.

### 3.3 Physics-informed features
| Feature | Formula | Why |
|---|---|---|
| `i_s` | √(i_d² + i_q²) | Current magnitude |
| `u_s` | √(u_d² + u_q²) | Voltage magnitude |
| `i_s_sq` | i_s² | Proportional to copper loss (I²R), the main heat source in the winding |
| `p_el` | 1.5 × (u_d·i_d + u_q·i_q) | Electrical power in the dq frame. The 1.5 comes from the amplitude-invariant Park transform; log this as a `[NUANCE]` |
| `p_mech` | torque × motor_speed × 2π/60 | Mechanical power in W (rpm converted to rad/s) |

### 3.4 EWMA "thermal memory" features (the key idea; see N3)
- Base signals: `i_s`, `i_s_sq`, `p_el`, `u_s`, `motor_speed`, `torque`, `coolant`, `ambient`.
- Spans: `[120, 600, 1800, 5400]` samples, which at 2 Hz is about 1, 5, 15 and 45 minutes.
- Compute them per profile:
  ```python
  df.groupby("profile_id")[col].transform(lambda s: s.ewm(span=sp).mean())
  ```
- Log:
  - the total feature count;
  - the span-to-minutes conversion;
  - the warm-up nuance: the first rows of each profile have little history.

### 3.5 Scaling
- Use `StandardScaler` **inside an sklearn `Pipeline`**, so it is fit on the training folds only.
- It is needed for linear models and MLPs, but **not** for tree models. Log *why* (trees split on thresholds, and scaling doesn't change the order of values).

### 3.6 Subsampling (only if needed for speed; see N6)
- For tree models, keep every k-th *training* row, applied **after** the features are computed.
- Log k and its effect on CV score and training time.

### 3.7 Save
- `data/processed/features.parquet`
- `data/processed/feature_list.json`

### Figures
- Raw signal vs its EWMAs for one profile.
- A bar chart of each feature's correlation with the target, showing the EWMA features correlate better than the raw ones.

**Leakage checklist** (copy it into `LOG.md` and tick each item)
- [ ] No `pm`, `stator_tooth` or `stator_yoke` in the features.
- [ ] `profile_id` is not a feature.
- [ ] EWMA is computed per profile and causally (past only).
- [ ] The scaler is fit only on training data (inside a Pipeline).
- [ ] Test profiles were untouched by any tuning.

**Acceptance criteria**
- [ ] The leakage checklist is fully ticked.
- [ ] The processed data and feature list are saved.
- [ ] Figures are saved and logged.
- [ ] Concepts added: data leakage, train/validation/test, GroupKFold, feature engineering, EWMA (with formula and span), standardisation.

---

## Phase 4: Model development (12 marks)

**Notebook:** `notebooks/04_modelling.ipynb`.

**Evaluation method:** use **only the training profiles**, with GroupKFold (5 folds). The main selection metric is **RMSE in °C (mean ± std across folds)**. Also record MAE and R².

**Train these models in order** (one `LOG.md` entry each):

| ID | Model | Purpose |
|---|---|---|
| B0 | Predict the training mean | "Dumbest" baseline |
| B1 | Winding temp = coolant temp + mean offset | Physics-naive baseline: is reading the coolant enough? |
| M1 | Linear Regression on the 8 raw inputs | Simple ML baseline |
| M2 | Linear Regression on raw + engineered + EWMA features | Shows how much the features add (expect a big jump) |
| M3 | Ridge (alpha tuned), and optionally Lasso | Regularisation; Lasso also shows which features it drops |
| M4 | Random Forest Regressor | Non-linear; tune `n_estimators`, `max_depth`, `min_samples_leaf` |
| M5 | LightGBM (or XGBoost) | Gradient boosting; tune `num_leaves`, `learning_rate`, `n_estimators` |
| M6 (optional) | MLPRegressor (sklearn) on scaled features | Small neural net for comparison |

**Rules**
- Tune with `RandomizedSearchCV(cv=GroupKFold(5))` or a small manual grid.
- Log for every model:
  - the search ranges;
  - the best parameters;
  - the training time.
- Save the results table to `outputs/results/cv_results.csv`, with these columns: model, RMSE mean, RMSE std, MAE, R², train time (s), number of features.
- **Choosing the final model (`[DECISION]`):**
  - start with the best RMSE;
  - but if a simpler or faster model is within about 0.3 °C, discuss the trade-off (a motor controller has limited compute).
  - Keep 2–3 finalists for Phase 5.
- **[v2] Early-stopping trap:** boosting libraries (LightGBM, or sklearn's `HistGradientBoostingRegressor`) can pick their own internal validation rows **at random**. That mixes rows from the same session and gives over-optimistic scores. Disable automatic early stopping, or give it a validation set made of whole sessions.
- **[v2] Compute fallback:** if 5-fold GroupKFold is too slow for Random Forest or LightGBM on a laptop, use one fixed validation split of whole training sessions (`GroupShuffleSplit`, about 15% of training sessions, `SEED = 42`) for those models, and log it.
- Retrain the finalists on **all** training profiles and save them to `outputs/models/*.joblib`. Save their input list, package versions and the split ID next to them (`outputs/models/model_metadata.json`).
- Set the numeric success target from Phase 1 now (e.g. "test RMSE below X °C") and log it.

**Acceptance criteria**
- [ ] The CV table has at least 6 models.
- [ ] Tuning ranges, best parameters and times are logged.
- [ ] A `[DECISION]` entry explains the finalists.
- [ ] Concepts added: linear regression, Ridge/Lasso (regularisation), decision tree, Random Forest (bagging), gradient boosting, cross-validation, hyperparameter tuning, overfitting vs underfitting, bias–variance in simple words.

---

## Phase 5: Evaluation & interpretation (8 marks): the test set is used here, once

**Notebook:** `notebooks/05_evaluation.ipynb`. Log the exact time the test set was first evaluated.

**Metrics on the test profiles**
- MSE (°C²), RMSE (°C), MAE (°C), R², max absolute error (°C).
- **[v2]** 95th-percentile absolute error (°C), and mean signed error = mean(predicted − actual) in °C. Negative means the model under-predicts on average.
- Compute them overall **and per test profile**.
- **[v2]** Report both the row-weighted overall MAE and the **unweighted mean of per-session MAE**. Sessions have very different lengths (0.302–6.107 h), so the two answer different questions.
- Save them to `outputs/results/test_metrics.csv` and `test_metrics_per_profile.csv`.

**Required figures**
1. **Predicted vs actual winding temperature over time**, one figure per test profile. This is the most important plot of the whole project.
2. A histogram of the residuals (errors).
3. A predicted vs actual scatter plot with the y = x line.
4. Absolute error vs actual temperature: does the model get worse when the motor is hot?
5. Feature importance, using permutation importance (and SHAP if installed). Compare it with physics (N7).
6. A bar chart of test RMSE for all finalists and the baselines.

**Interpretation** (write it in plain English in the notebook and in `LOG.md`)
- Which features matter most, and does that match the physics?
- Where does the model fail? (The start of profiles / warm-up, rapid load changes, extreme temperatures.)
- CV score vs test score: what is the generalisation gap, and why?
- **Under-prediction analysis (N8):**
  - the largest under-prediction;
  - the percentage of time the model under-predicts by more than 5 °C when the actual temperature is high (pick the threshold from the data, e.g. the top 10% of temperatures).

**Acceptance criteria**
- [ ] The test set is evaluated once, with the time logged.
- [ ] The results CSVs are saved.
- [ ] At least 6 figures are saved and logged.
- [ ] The interpretation is written.
- [ ] Concepts added: MSE, RMSE, MAE, R², residuals, permutation importance (and SHAP if used), generalisation gap.

---

## Phase 6: Innovation / creativity (5 marks)

Do **at least 3** of these (I1 and I3 are strongly recommended). Log each with numbers and figures.

- **I1. Ablation study table:** the final model in five variants:
  - full;
  - no EWMA features;
  - no engineered features;
  - no `torque`;
  - **with** the leakage temperatures (to show *why* they are forbidden).

  This proves, with numbers, that each idea helps. Save it to `outputs/results/ablation.csv`.
- **I2. Physics-informed "thermal memory" story:** present the engineered + EWMA features as our main innovation, with the before/after numbers.
- **I3. Safety-aware evaluation:**
  - add a safety margin (e.g. k × the residual standard deviation) to the prediction;
  - define an overheating alert: alert if prediction + margin > threshold (choose a threshold the test data actually reaches);
  - report how many real "hot" moments are caught vs how many are false alarms, for 2–3 values of k.
- **I4. Data-efficiency curve:** test RMSE when training on 25%, 50%, 75% and 100% of the training profiles.
- **I5. Demo app ([v2] now a CORE deliverable, not optional):** a small Streamlit app (`app.py`) that "replays" a test profile, showing actual vs predicted winding temperature updating, plus an alert lamp.
  - Its owner (E) builds the **app shell early**, during Phases 2–4, with a placeholder model, and swaps in the real saved pipeline after Phase 4.
  - Label it "Recorded-data replay". It never retrains at startup, and the measured temperature is only used for the comparison plot, never as an input.
  - Add `streamlit` to `requirements.txt` when this starts, and log it.

**Acceptance criteria**
- [ ] At least 3 innovation items are done, each with a results file, a figure and a `LOG.md` entry.
- [ ] Each is explainable in 2 lines in `VIVA_QA.md`.

---

## Phase 7: Deliverables & viva prep

1. **Flow diagram (required):** `docs/flow_diagram.md` in Mermaid, plus an exported PNG.
   - It must show: data source → data check → EDA (list the plots) → cleaning → split by profile → feature engineering (physics + EWMA) → scaling → models → CV tuning → final model → test evaluation → interpretation and innovation.
   - Export with `npx -y @mermaid-js/mermaid-cli -i docs/flow_diagram.md -o docs/flow_diagram.png` if Node.js is installed; otherwise draw it in draw.io and save the PNG.
2. **Final submission notebook (if the teacher wants one file):** `notebooks/MST_final.ipynb`, combining the key steps from notebooks 01–06 with markdown explanations. It must run top to bottom.
3. **Report (if asked):** sections that follow the rubric order. Use the format the teacher asks for.
4. **Slides (10–12):**
   1. Title + team
   2. Problem & motivation
   3. Dataset
   4. Flow diagram
   5. EDA highlights
   6. Pre-processing & features
   7. Models
   8. CV results table
   9. Test results + the predicted-vs-actual plot
   10. Innovation (ablation + safety)
   11. Limitations & future work
   12. Thank you

   Each teammate presents one part.
5. **Viva prep:**
   - `VIVA_QA.md` should have at least 40 Q&As.
   - Each teammate does a mock viva: pair up and quiz each other with 10 random questions from `VIVA_QA.md`, one at a time; the quizzer grades the answers against the A: lines.
6. **Final `LOG.md` entry:** a project summary plus the final numbers table, cross-checked against `outputs/results/`.

**Acceptance criteria**
- [ ] The flow diagram PNG exists.
- [ ] The notebooks run top to bottom.
- [ ] The slides (and report if asked) are done.
- [ ] Every number in the slides matches the results files.
- [ ] Every teammate has done a mock viva.

---

## Team split (fill in names; everyone still reads the whole LOG)

Split proposed 2026-10-07 (see `LOG.md`). The B–E names are still to be filled in. Each member **owns** a stage: they run the work session for it and must be able to defend it in detail. The **reviewer** is the next person in the chain. They read the owner's notebook and log entries, and ask them 3 viva questions before building on it.

| Member | Owns (runs the work sessions) | Extra role | Reviews | Presents (slides) |
|---|---|---|---|---|
| A: Arnav | Phase 0 (done), Phase 1 `docs/problem.md` | **Coordinator:** shared repo, flow diagram (Phase 7.1), assembling the slides, final number cross-check, `MST_final.ipynb` if asked | E's work | 1–4: title, problem, dataset, flow diagram |
| B: ____ | Phase 2 EDA (8 figures + top-5 insights) | **Viva master:** keeps `VIVA_QA.md` at 40+ Q&As, runs everyone's mock viva | A's work | 5: EDA highlights |
| C: ____ | Phase 3 split, physics + EWMA features, leakage checklist | Innovation I2 (the "thermal memory" story, before/after numbers) | B's work | 6: pre-processing & features |
| D: ____ | Phase 4 baselines + 6 models, CV table, finalists | Innovation I1 (ablation table); I4 (data-efficiency) only if time allows | C's work | 7–8: models, CV results |
| E: ____ | Phase 5 test evaluation (test set used once) | Innovation I3 (safety alarm) + I5 (Streamlit demo) | D's work | 9–10: test results, safety + demo |

- **Slide 11** (limitations & future work): each member adds one point from their own stage. **Slide 12:** thank you.
- **Order:** 1 and 2 can run in parallel (both only need Phase 0). Then 3 → 4 → 5 → 6 → 7 in sequence. While waiting for their turn, members read `LOG.md`/`CONCEPTS.md` so far, read up on their own phase's concepts, and set up their venv (`requirements.txt` + `src/download_data.py`).
- **Everyone, at the end:** a mock viva (Phase 7) and a full read of `LOG.md`, `CONCEPTS.md` and `VIVA_QA.md`. Viva questions can go to **anyone**.

## [v2] Handoffs and fallback
- **Handoff package:** when your phase is done, tell the next owner:
  - the file locations;
  - how to run them;
  - what inputs they expect and what they produce;
  - the known limits.
  Say "the split is in `outputs/results/split_profiles.json`", not "split done".
- **If we fall behind, keep this priority order:** correct data and split → working baseline and model → honest test evaluation → slides and viva prep → reliable demo → extras (MLP, I4, SHAP).
- **Fallback scope (Master Guide's "Day 3 fallback"):** baselines, Linear+features, Ridge and one boosting model; skip extensive tuning; session selector + slider instead of an animated replay.

## Deadlines (fill in)
- MST project submission / presentation: ____
- Once the date is known, map the phases to days. The Master Guide's 7-day template works if we have about a week: Day 1 split, Day 2 EDA + baselines, Day 3 models + app shell, Day 4 freeze, Day 5 test + demo, Day 6 report/slides, Day 7 rehearsal.

## References
- Dataset: https://www.kaggle.com/datasets/wkirgsn/electric-motor-temperature
- "Real-time temperature prediction of electric machines using machine learning with physically informed features" (Energy and AI, 2023): https://www.sciencedirect.com/science/article/pii/S2666546823000605
- Kirchgässner et al., "Estimating Electric Motor Temperatures With Deep Residual Machine Learning": https://www.researchgate.net/publication/347485416
- Before using a reference in the report, open and read it, and log what we took from it.
