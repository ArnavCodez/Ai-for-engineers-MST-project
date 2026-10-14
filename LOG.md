# LOG: MST Project (Motor Winding Temperature)

This is an **append-only** team journal. The format and rules are in `CONTRIBUTING.md` (the logging section).
Search tags with Ctrl+F: `[DECISION]` `[NUANCE]` `[BUG]` `[RESULT]` `[IDEA]` `[SETUP]` `[DATA]` `[EDA]`

---

## 2026-10-06 | Phase — | Project chosen and plan written  (run by: Arnav)
**Tags:** [DECISION]
**What we did:** Chose MST statement #6 (GE Power Systems, motor winding temperature regression) and wrote `PLAN.md`.
**Why:**
- It's in our ECE domain (motors, currents, I²R heating), so domain questions in the viva work in our favour.
- It uses a real public dataset, not a self-generated one.
- Very few groups are likely to pick it.
**How:** Compared all 10 MST statements on uniqueness, viva risk and dataset availability.
**Result:** Dataset is the Kaggle "Electric Motor Temperature" (Paderborn University PMSM test bench, `measures_v2.csv`).
**Nuances / gotchas:** The two big traps are written up as N1 and N2 in `PLAN.md`: leakage from the other temperature columns, and a random split on time-series rows.
**Alternatives considered:**
- #7 Siemens material clustering: also unique, but unsupervised, so it's harder to prove the clusters are "right".
- #4 protein solubility: too far from our domain.
- #1/#5/#9 (house price / loan / churn): overdone.
**Viva angle:** Q: "Why this topic?" A: It's a real engineering problem from our branch (motor thermal protection), on real test-bench data, and we can explain the physics behind the features.

---

## 2026-10-07 00:08 | Phase 0.1 | Folder layout, .gitignore and requirements.txt  (run by: Arnav)
**Tags:** [SETUP] [DECISION]
**What we did:** Created the folder layout from `PLAN.md`, a `.gitignore` and a first `requirements.txt`.
**Why:** Every teammate gets the same structure, and big or secret files never end up in git.
**How:**
- Folders: `data/raw/`, `data/processed/`, `notebooks/`, `src/`, `outputs/figures/`, `outputs/results/`, `outputs/models/`, `docs/report/`, `docs/slides/`.
- `.gitignore` ignores: `.venv/`, `data/` (raw *and* processed), `outputs/models/`, `.ipynb_checkpoints/`, `__pycache__/`, `kaggle.json`, `.env`.
- `requirements.txt`: the core libraries from the plan's tech stack (numpy, pandas, pyarrow, matplotlib, seaborn, scikit-learn, lightgbm, joblib, jupyter, nbconvert), plus `ipykernel` (lets Jupyter run code in our venv) and `kagglehub` (data download, allowed by the team rules in `CONTRIBUTING.md`). The optional `shap` and `streamlit` wait until the phase that needs them.
**Result:** —
**Nuances / gotchas:**
- The whole `data/` folder is ignored. A teammate who gets the project from git must run `src/download_data.py` and then notebook 01 to recreate the raw CSV and the parquet file.
- `outputs/results/` and `outputs/figures/` **are** committed. They are small, and they are the "source of truth" for every number we quote.
- `kaggle.json` and `.env` are ignored as a safety net, even though we don't use any key right now.
**Alternatives considered:** Committing the data. Rejected: the CSV is 300.1 MB and the parquet 72.2 MB, and GitHub warns at 50 MB per file and blocks files over 100 MB.
**Viva angle:** Q: Why isn't the dataset in your git repo? A: It's 300 MB, and anyone can re-download it with one script (`src/download_data.py`). Git is for code and small results, not big data.

---

## 2026-10-07 00:43 | Phase 0.2 | Python 3.11 venv and package install  (run by: Arnav)
**Tags:** [SETUP] [DECISION] [NUANCE]
**What we did:** Installed Python 3.11.14, created `.venv` with it, installed the packages, saved `pip freeze`, and pinned the exact versions in `requirements.txt`.
**Why:**
- The team rules say Python 3.11. This laptop only had 3.14 (the default), 3.13 and a 3.15 alpha.
- Very new Python versions often don't have ready-made packages ("wheels") for scientific libraries yet. TensorFlow for the EST project is the most likely problem.
- Pinning versions means every teammate gets exactly the same libraries, so results match.
**How:**
- `uv python install 3.11`: uv (a fast Python tool already on this laptop) downloaded Python 3.11.14.
- `"<uv's python 3.11>\python.exe" -m venv .venv`: a normal venv, so the commands in the team rules (`.venv\Scripts\activate`, `pip install -r requirements.txt`) work unchanged.
- `.venv\Scripts\python -m pip install -r requirements.txt`, then `pip freeze > outputs/results/pip_freeze.txt`.
- Rewrote `requirements.txt` with `==` versions.
**Result:**
- Python 3.11.14. `pip_freeze.txt` lists 119 packages (our 12 plus their dependencies).
- The install took **1,151 s (about 19 min)**.

| Library | Version |
|---|---|
| numpy | 2.4.6 |
| pandas | 3.0.6 |
| pyarrow | 25.0.1 |
| matplotlib | 3.11.2 |
| seaborn | 0.13.2 |
| scikit-learn | 1.9.1 |
| lightgbm | 4.7.0 |
| scipy (dependency) | 1.17.1 |
| joblib | 1.6.0 |
| jupyter / jupyterlab / notebook | 1.1.1 / 4.6.4 / 7.6.3 |
| nbconvert / ipykernel | 7.17.1 / 7.4.0 |
| kagglehub | 1.0.2 |

**Nuances / gotchas:**
- **uv was used only to *get* Python 3.11.** A teammate without uv can install Python 3.11 from python.org, then run `python -m venv .venv` and `pip install -r requirements.txt` as usual.
- We didn't use `uv venv`, because it makes a venv **without pip** by default, which would break the commands in the team rules.
- **19 minutes is slow.** The likely cause is antivirus scanning thousands of small files on the D: drive, but we did not confirm this. Expect a long first install.
- **pandas 3.0 is a major version.** "Copy-on-Write" is now always on. This means old-tutorial code like `df["col"][mask] = 0` (chained assignment) silently changes nothing. Always write `df.loc[mask, "col"] = 0`. Text columns also use a new string type by default. Our data is all numeric, so this doesn't affect us yet.
**Alternatives considered:**
- Use Python 3.14: breaks the team rule, and libraries may lack wheels.
- conda: heavier, and not in the plan.
- `uv venv` + `uv pip`: faster, but needs every teammate to install uv.
**Viva angle:** Q: Why use a virtual environment and pinned versions? A: The venv keeps this project's libraries separate from everything else on the laptop. The pinned `requirements.txt` makes every teammate install exactly the same versions, so the same code gives the same numbers.

---

## 2026-10-07 00:45 | Phase 0.3 | Dataset downloaded with kagglehub (no login)  (run by: Arnav)
**Tags:** [DATA] [SETUP] [DECISION]
**What we did:** Downloaded `measures_v2.csv` from Kaggle into `data/raw/` with a small script.
**Why:** The dataset is public, so no Kaggle API key is needed. A script makes the download repeatable for every teammate.
**How:**
- `src/download_data.py`, function `download_measures()`. Run it from the project folder: `.venv\Scripts\python src\download_data.py`.
- It calls `kagglehub.dataset_download("wkirgsn/electric-motor-temperature")`, which saves to kagglehub's cache folder. It then copies `measures_v2.csv` into `data/raw/`. If the file is already there, it does nothing.
**Result:**
- Kaggle dataset `wkirgsn/electric-motor-temperature`, **version 3**. https://www.kaggle.com/datasets/wkirgsn/electric-motor-temperature
- The archive is 117 MB and contains one file, `measures_v2.csv`, of **300.1 MB**.
- The download took 118 s.
**Nuances / gotchas:**
- kagglehub keeps a second 300 MB copy in `C:\Users\<you>\.cache\kagglehub\datasets\wkirgsn\electric-motor-temperature\versions\3\`. You can delete it after the copy if disk space is tight.
- The **dataset version** matters. If the owner uploads a new version, kagglehub may fetch it. We logged "version 3" so we can tell if numbers ever change.
- If Kaggle ever demands a login, download the zip in the browser from the link above and put `measures_v2.csv` in `data/raw/` by hand.
- We never created, printed or stored any Kaggle key.
**Alternatives considered:**
- A Kaggle API token: works, but means handling a secret key for no benefit.
- A manual browser download: works, but isn't scripted, so it's easy to grab the wrong file or version.
**Viva angle:** Q: Where exactly does your data come from, and how would someone get the same data? A: Kaggle dataset `wkirgsn/electric-motor-temperature`, version 3 (Paderborn University PMSM test bench). Running `src/download_data.py` fetches the same 300.1 MB file.

---

## 2026-10-07 00:52 | Phase 0.4 | Data check: size, sessions, missing values, duplicates, ranges  (run by: Arnav)
**Tags:** [DATA] [RESULT] [NUANCE]
**What we did:** Built and ran `notebooks/01_data_check.ipynb` top to bottom. It looks at the raw data without changing it.
**Why:** Before any modelling we must know the data is complete, unique and physically sensible. Phase 0 also asks us to verify the dataset's advertised numbers (about 1.3M rows, 69 profiles, about 185 h).
**How:**
- `pd.read_csv` for loading, `df.groupby("profile_id").size()` for session lengths, `df.isna().sum()` for missing values, `df.duplicated().sum()` for duplicate rows, and `df.describe()` for ranges.
- Range check: every temperature column against limits we chose, **−20 °C to 200 °C**. 200 °C is above the strongest common insulation class (Class H = 180 °C).
- Hours per session = rows ÷ 2 Hz ÷ 3600 s.
- All numbers are saved in `outputs/results/data_check_summary.json`, and every session's length in `outputs/results/rows_per_profile.csv`.
**Result:**

| Check | Result |
|---|---|
| Shape | **1,330,816 rows × 13 columns** (12 measurements + `profile_id`) |
| Sessions (`profile_id`) | **69**, IDs from 2 to 81 |
| Total time | **184.84 h** |
| Session length, min / median / max | 2,176 / 17,142 / 43,971 rows = **0.302 / 2.381 / 6.107 h** |
| Shortest sessions | 47 (0.302 h), 46 (0.303 h), 52 (0.518 h) |
| Longest sessions | 20 (6.107 h), 6 (5.609 h), 65 (5.569 h) |
| Missing values | **0** in every column |
| Duplicate rows | **0** (all 13 columns); also **0** when `profile_id` is ignored |
| Column types | 12 × `float64`, `profile_id` is `int64` |

| Temperature column | Min (°C) | Max (°C) | Inside −20…200 °C? |
|---|---|---|---|
| coolant | 10.62 | 101.60 | yes |
| ambient | 8.78 | 30.71 | yes |
| **stator_winding (target)** | **18.59** | **141.36** | yes |
| stator_tooth | 18.13 | 111.95 | yes |
| stator_yoke | 18.08 | 101.15 | yes |
| pm | 20.86 | 113.61 | yes |

- `motor_speed`: −275.55 to 6,000.02 rpm. **87,308 rows (6.56 %)** are negative.
- `torque`: −246.47 to 261.01 Nm. **446,946 rows (33.58 %)** are negative.
- `i_d`: −278.00 to 0.052 A. `i_q`: −293.43 to 301.71 A.
- `ambient`: mean 24.565 °C, std 1.930 °C.
**Nuances / gotchas:**
- **The dataset's advertised numbers are confirmed**: 1.33M rows, 69 profiles, 184.8 h (advertised: about 185 h).
- **The IDs have gaps.** There are 69 IDs between 2 and 81, so 11 numbers are unused. Never loop `for pid in range(1, 70)`; always use `df["profile_id"].unique()`.
- **Sessions are very unequal**: the longest (6.107 h) is about 20× the shortest (0.302 h). An "average over all rows" is dominated by long sessions. That is why the plan (N5) wants per-profile errors too.
- **Negative torque in 33.58 % of rows sounds like a lot**, but torque's 25th percentile is only −0.137 Nm. So many of these rows are tiny values around zero (motor almost idle, sensor noise), not heavy braking. Real braking (motor acting as a generator) is also in there, down to −246.47 Nm.
- **`i_d` is (almost) never positive** (max 0.052 A). This fits how PMSMs are controlled. A negative d-axis current weakens the magnet's field so the motor can reach high speed ("field weakening"). It is physics, not an error.
- **Ambient has a low outlier**: its min, 8.78 °C, is about 8 standard deviations below the mean (24.565 − 8.78 = 15.8 °C; 15.8 / 1.93 ≈ 8.2). That's within limits, so we keep it, but Phase 2 should look at which session it comes from.
- **The hottest winding reading is 141.36 °C**, below the Class F limit (155 °C). The test bench never pushed the motor to its insulation limit, so we can't test the model *above* 141 °C.
- `pm`, `stator_tooth` and `stator_yoke` are looked at here only to sanity-check them. They will **not** be inputs (leakage, N1).
**Alternatives considered:** Limits of 0–180 °C instead. Rejected: no reading is near either bound, so the choice changes nothing, and a wider range only flags truly impossible values.
**Viva angle:** Q: Did your data need cleaning? A: No rows were removed. Across 1,330,816 rows there are 0 missing values and 0 duplicate rows, and every temperature is in a physically plausible range (winding 18.59–141.36 °C).

---

## 2026-10-07 00:52 | Phase 0.5 | Checking the "file order = time order" assumption (N9)  (run by: Arnav)
**Tags:** [NUANCE] [DATA] [DECISION]
**What we did:** Tested whether the rows inside each session are really in time order, because the file has **no timestamp column**.
**Why:** The EWMA "thermal memory" features (Phase 3) average the *past*. If the rows weren't in time order, "past" would be meaningless and the features would be garbage.
**How:** Two checks in notebook 01, section 4:
1. **Blocks:** count where `profile_id` changes from one row to the next. If each session is one unbroken block, the number of blocks equals the number of sessions.
2. **Smoothness:** the median absolute change of `stator_winding` between neighbouring rows inside each session (`df.groupby("profile_id")["stator_winding"].diff().abs()`), compared with the same rows after a random shuffle (`sample(frac=1, random_state=42)`).
**Result:**
- **69 blocks for 69 sessions**, and 0 sessions split into pieces.
- The file is **not** sorted by ID. It starts with sessions 17, 5, 12, 32, 21, 2, 4, 7, 19, 3, …
- Median row-to-row change: **0.02208 °C in file order vs 28.85482 °C shuffled**, about 1,300× smaller.
- 99.9th percentile of the change: 0.55487 °C. The largest change: 1.39394 °C in 0.5 s.
- The first rows of session 17 (the first in the file) show winding 19.09 °C, coolant 18.81 °C and ambient 19.85 °C. So the session starts **cold, at room temperature**, as a real test run would.
**Nuances / gotchas:**
- **Smoothness can't tell forwards from backwards.** A session stored in reverse would also be smooth. The "starts cold at room temperature" observation is what suggests forwards. We checked it for one session only, and Phase 2's time plots will show it for more.
- **Never sort the DataFrame by `profile_id`.** It looks harmless, but an unstable sort can scramble the time order inside a session. If sorting is ever needed, use `kind="stable"`, which keeps the original order of rows with equal IDs. Better: just don't sort.
- **Shuffling destroys the time structure.** That's why the plan says EWMA features must be built *before* any shuffling or subsampling.
- The 1.39 °C jump in 0.5 s is large compared with the median. It could be a fast current step or sensor noise. Phase 2 should find where it happens.
**Alternatives considered:** Simply assuming the order is right, as many Kaggle notebooks do. Rejected: it's cheap to test, and the viva will probably ask.
**Decision:** We accept N9: file order = time order inside each session.
**Viva angle:** Q: There's no timestamp, so how do you know the rows are in time order? A: Each session is one unbroken block. Neighbouring rows differ by a median of only 0.022 °C, against 28.85 °C if shuffled, which only happens if they're consecutive moments. And sessions start at room temperature, as real runs do.

---

## 2026-10-07 00:52 | Phase 0.6 | float32 + parquet copy saved  (run by: Arnav)
**Tags:** [DECISION] [RESULT] [NUANCE]
**What we did:** Converted the 12 decimal columns from `float64` to `float32` and saved the data as `data/processed/measures_v2.parquet`.
**Why:** The later notebooks load the data many times. A smaller, faster file saves time and RAM, which matters for Random Forest on a laptop (N6).
**How:** `df_32[float_cols] = df_32[float_cols].astype("float32")`, then `df_32.to_parquet(..., index=False)`. We reloaded the file to check its shape and row order, and measured the biggest change any value suffered from the cast.
**Result:**
- **RAM: 138.4 MB → 74.5 MB (46.2 % saved).**
- **Disk: 300.1 MB CSV → 72.2 MB parquet** (about 4× smaller).
- Load time (final run): **CSV 7.66 s vs parquet 0.42 s**. On the first run it was 10.31 s vs 1.75 s.
- Biggest change from the cast: **0.000244 rpm in `motor_speed`**. The target `stator_winding` changed by at most **0.0000076 °C**, and the other columns by at most 0.000015.
- After reloading, the shape and the row order are identical.
**Nuances / gotchas:**
- **Why 46.2 % and not 50 %:** `profile_id` stayed `int64` (1,330,816 × 8 bytes = 10.6 MB). Only the 12 float columns halved: 127.8 MB → 63.9 MB.
- **Why exactly 0.000244:** float32 keeps about 7 significant digits. For numbers between 4,096 and 8,192 (high motor speeds), the gap between two neighbouring float32 values is 2⁻¹¹ ≈ 0.000488, and rounding moves a value by at most half a gap, ≈ 0.000244. That's 0.000004 % of 6,000 rpm.
- **Something we almost got wrong:** looking at `head()`, we first guessed the values were *already* float32 (e.g. `19.086669921875` is an exact float32 number), so the cast would change nothing. The measurement showed small changes, so the guess was wrong for some values. This is why we measure instead of assume.
- **Load times vary between runs**, probably because Windows keeps recently read files in its memory cache. Our two runs give 5.9× (10.31 / 1.75) and 18.2× (7.66 / 0.42), so quote "about 6–18× faster", or quote one run's numbers from `data_check_summary.json`.
- Parquet keeps column types and row order, so no `dtype=` arguments are needed when loading.
**Alternatives considered:**
- Keep float64: twice the RAM, with no accuracy gain (sensors aren't that precise).
- Feather or HDF5: also fast, but parquet is the standard, is compressed and is in our plan.
**Viva angle:** Q: Why convert to parquet and float32? A: The 300.1 MB CSV becomes a 72.2 MB parquet that loads in under 2 s instead of 8–10 s. float32 halves the float memory (138.4 → 74.5 MB in total), and the biggest error it adds is 0.000244 rpm, far below sensor accuracy.

---

## 2026-10-07 00:52 | Phase 0.7 | Harmless warnings and the "�C" display glitch  (run by: Arnav)
**Tags:** [BUG] [NUANCE]
**What we did:** Investigated two odd-looking things seen while running notebook 01.
**Why:** So no teammate wastes time on them, or thinks the notebook is broken.
**How:** We ran `jupyter nbconvert --to notebook --execute --inplace "notebooks/01_data_check.ipynb"`, then read the notebook file directly with Python to see what is really stored in it.
**Result:**
1. **Warnings from nbconvert on Windows:** "Proactor event loop does not implement add_reader…" and "Kernel is running over TCP without encryption…". These are **harmless**: the notebook ran fully, with 0 error outputs. They come from how Jupyter talks to its kernel on Windows.
2. **[BUG] "°C" showed as "�C"** when we printed notebook outputs in the terminal.
   - **Cause:** the Windows terminal used a different text encoding from the notebook (UTF-8). The notebook file itself is correct: it contains 14 "°" signs and 0 broken characters.
   - **Fix:** none needed in the notebook. If you print to a terminal and see "�", set `PYTHONIOENCODING=utf-8` first.
**Nuances / gotchas:** In Jupyter or VS Code the "°" shows correctly. Only the plain terminal shows "�".
**Alternatives considered:** Writing "degC" instead of "°C" everywhere. Rejected: the notebook is what we present, and it displays correctly.
**Viva angle:** —

---

## 2026-10-07 00:53 | Phase 0 summary  (run by: Arnav)
**Tags:** [SETUP] [DATA] [RESULT]
**What we did:** Finished Phase 0: environment, data download, data check and a fast parquet copy.

**1. Recap in simple words**
- We set up Python 3.11.14 in a project venv with pinned library versions, so every teammate gets the same setup.
- We downloaded the real dataset (Kaggle, version 3, 300.1 MB) with one script that anyone can re-run.
- The data is exactly as advertised: 1,330,816 rows, 69 sessions, 184.84 h, with 0 missing values and 0 duplicates.
- All temperatures are physically sensible. The winding reaches 18.59–141.36 °C.
- We showed the rows are in time order inside each session, and we saved a 72.2 MB float32 parquet copy for the next notebooks.

**2. Acceptance checklist**
- [x] The environment installs cleanly; Python and library versions are logged (Phase 0.2).
- [x] The data loads; real shape 1,330,816 × 13, 69 profiles and 184.84 h are logged (Phase 0.4).
- [x] Missing, duplicate and range checks are done and logged (Phase 0.4).
- [x] `LOG.md` has entries for setup and the data check (Phases 0.1–0.7).
- [x] `CONCEPTS.md` has: PMSM, dq frame / Park transform, sampling rate, parquet vs CSV (plus virtual environment, float32 vs float64, thermal inertia).

**3. What every teammate must be able to explain from this phase**
- What one row is (one moment, 0.5 s apart, at 2 Hz), what a `profile_id` is (one test session), and why sessions matter for splitting later.
- How we know the data is clean: 0 missing values, 0 duplicates, all temperatures in −20…200 °C.
- How we know the rows are in time order without a timestamp: one block per session, and a 0.022 °C vs 28.85 °C median step.
- Why negative torque and negative `i_d` are physics, not errors (braking / generating; field weakening).
- Why parquet + float32: 4× smaller on disk, much faster to load, half the float memory, with a negligible 0.000244 rpm error.

**4. Key numbers**

| Quantity | Value | Source |
|---|---|---|
| Rows × columns | 1,330,816 × 13 | `data_check_summary.json` |
| Sessions | 69 (IDs 2–81) | same |
| Total hours | 184.84 | same |
| Session length min / median / max | 0.302 / 2.381 / 6.107 h | same |
| Missing values / duplicate rows | 0 / 0 | same |
| Winding temperature range | 18.59–141.36 °C | same |
| Median row-to-row winding change (file vs shuffled) | 0.02208 vs 28.85482 °C | same |
| RAM float64 → float32 | 138.4 → 74.5 MB (−46.2 %) | same |
| CSV → parquet size | 300.1 → 72.2 MB | same |
| Package install time | 1,151 s | this log, Phase 0.2 |

**Viva angle:** the 12 new Phase 0 questions (plus 1 updated with our measured numbers) are in the "Data" section of `VIVA_QA.md`.

---

## 2026-10-07 00:53 | Handover  (run by: Arnav)
**Tags:** —
**Where we stopped:** Phase 0 of the MST project is complete and ticked in `PLAN.md`. Phase 1 has not started.
**What's next (exact next step):** Phase 1, writing `docs/problem.md`. It covers why winding temperature matters (insulation classes, ageing, derating), why a virtual sensor instead of more sensors, the objective, success criteria, users and constraints. Then add at least 5 motivation/domain Q&As to `VIVA_QA.md`. Follow the Phase 1 section of `PLAN.md`.
**Open issues / questions:**
- The team split and deadline tables in `PLAN.md` are still empty. Fill them in.
- `misc.txt` in the top folder holds one YouTube link with no note. Ask the team what it's for.
- This folder is not a git repo yet. Decide if we use a private GitHub repo (as the README suggests).
- For Phase 2: find which session has the 8.78 °C ambient outlier, and where the 1.39 °C one-step winding jump happens.
**Before you start, you must know:**
- **Setup on your own laptop:**
  1. Install Python 3.11, from python.org or with `uv python install 3.11`.
  2. Inside `MST_Motor_Temperature`, run `python -m venv .venv`, then `.venv\Scripts\activate`, then `pip install -r requirements.txt`.
  3. Run `python src\download_data.py`.
  4. Run notebook 01, which creates the parquet file.
- The first `pip install` took about 19 minutes on this laptop. Be patient.
- Later notebooks should load `data/processed/measures_v2.parquet`, not the CSV.
- Never sort or shuffle the data before the time features are built (Phase 0.5).

---

## 2026-10-07 15:50 | Phase — | MST work split for 5 teammates (proposed)  (run by: Arnav)
**Tags:** [DECISION]
**What we did:** Divided the MST work among the 5 team members and wrote it into the "Team split" table at the bottom of `PLAN.md`.
**Why:**
- Every phase needs one clear owner who runs the session and can defend it in the viva.
- The workload and marks should be roughly balanced.
**How:** Each member owns one stage of the pipeline, plus an extra role:
- **A, Arnav:** Phases 0–1, plus coordinator (repo, flow diagram, slide assembly, number cross-check).
- **B:** Phase 2 EDA, plus "viva master" (`VIVA_QA.md` at 40+, mock vivas).
- **C:** Phase 3 features, plus innovation I2.
- **D:** Phase 4 models, plus innovation I1 ablation (and I4 if time allows).
- **E:** Phase 5 evaluation, plus innovation I3 safety alarm and I5 demo.

The reviewer of each stage is the owner of the next stage (B reviews A, C reviews B, D reviews C, E reviews D, A reviews E).
**Result:** The table in `PLAN.md` is filled in for roles. Names B–E are pending.
**Nuances / gotchas:**
- **The phases are a chain** (3 needs 2's insights, 4 needs 3's features, 5 needs 4's models), so later owners wait. Only Phases 1 and 2 can run in parallel. Waiting members should read the log, study their phase's concepts in advance and set up their venv early (the first install took about 19 min on Arnav's laptop).
- **The plan's original template gave D both Phases 4 and 5** (12 + 8 = 20 marks, the two heaviest phases). We moved Phase 5 to E and spread Phases 6–7 across everyone, so no one carries most of the marks alone.
- Innovation needs **at least 3** items. I1 (D), I2 (C) and I3 (E) cover that. I5 (demo, E) is the bonus, and I4 is optional.
- **Parallel sessions on different laptops will clash in `LOG.md`** unless everyone works on one shared copy (a private GitHub repo, as the README suggests). Set this up before Phases 1 and 2 run in parallel.
**Alternatives considered:**
- The plan's original template (D = Phases 4 + 5, E = Phases 6 + 7): unbalanced, as explained above.
- Everyone doing every phase together: slow, and nobody clearly owns anything.
- Splitting by "coding vs writing": the coders would understand everything and the writers nothing, which is a disaster in a viva where any question can go to anyone.
**Viva angle:** Q: How did you divide the work, and what was your contribution? A: By pipeline stage. Each of us owned one stage, ran it and presents it, and the next stage's owner reviewed it before building on it. Everyone read the full log and did a mock viva, so anyone can answer for any stage.

---

## 2026-10-07 16:15 | Phase — | Team tracker page + problem statement explained simply  (run by: Arnav)
**Tags:** [SETUP] [DECISION] [NUANCE]
**What we did:**
- Published a live team tracker webpage.
- Explained the GE problem statement in plain words, and mapped its parameters to our dataset columns.
**Why:**
- Five people need one place to see who owns what, which phase is next, and the deadline.
- Arnav asked for the statement "explained like I'm clueless". Every teammate needs that same base understanding.
**How:**
- The tracker is an online page (published online; ask Arnav for the link). Ticks, names and the deadline live in its shared database (`tasks/`, `team/`, `meta/plan`).
- It was seeded with Phase 0 = done (from this log) and A = Arnav, setup done.
- Added concepts: virtual sensor, supervised learning, regression. Added 4 Q&As under "Problem & motivation".
**Result:** Mapping from the statement to our columns:

| Statement says | Our column(s) | Role |
|---|---|---|
| ambient temperature | `ambient` | input |
| motor speed | `motor_speed` | input |
| load torque | `torque` | input |
| supply voltage | `u_d`, `u_q` | input |
| current | `i_d`, `i_q` | input |
| (not in statement, but in our data) | `coolant` | input |
| "winding temperatures" / motor temperature | `stator_winding` | **target** |

**Nuances / gotchas:**
- **The statement says "motor temperature", but a motor has many temperatures.** We estimate the **winding**, because the statement names winding temperatures and because in our data it is the hottest measured part. Its max is 141.36 °C, against pm 113.61, tooth 111.95 and yoke 101.15 °C (`data_check_summary.json`).
- **Voltage and current come in dq form (two numbers each), not one value.** Phase 3 combines them into magnitudes (`u_s`, `i_s`).
- **Sharing the tracker:** teammates can only tick things if Arnav invites them **by email as Editors**. If the page is also shared by a public link, outside teammates become view-only.
**Alternatives considered:**
- A shared Google Sheet: no phase logic, and easy to break.
- Only the tables in `PLAN.md`: not live, and teammates must pull from git to see changes.
**Viva angle:** Q: Explain your problem statement in simple words. A: GE wants the winding temperature without a sensor in the winding. We learn it from test-bench data where a sensor was fitted, using signals the controller already has. That's a virtual sensor, built as supervised regression.

---

## 2026-10-07 16:30 | Phase — | MST work moved into the team GitHub repo  (run by: Arnav)
**Tags:** [SETUP] [DECISION] [NUANCE]
**What we did:** Moved the whole MST project into the cloned GitHub repo `ArnavCodez/Ai-for-engineers-MST-project`. Added the team rules file to the repo (the same rules, MST-only paths; now `CONTRIBUTING.md`) and `data/README.md` (provenance).
**Why:**
- Five people need **one** shared copy, so `LOG.md` stays one continuous journal.
- Every teammate must follow the same logging rules, so the rules file has to be inside the repo.
**How:**
- Moved `PLAN/LOG/CONCEPTS/VIVA_QA.md`, `requirements.txt`, `.gitignore`, `data/`, `docs/`, `notebooks/`, `outputs/` and `src/` into the repo folder.
- The headers' links to the rules file now point to the copy inside the repo (no more `../`).
- `.gitignore`: `data/` became `data/*` + `!data/README.md`, so only the provenance file is tracked.
- `sha256sum data/raw/measures_v2.csv` → `78f3d150f0f2ad9c5dc7ff24dd12c00d386ad530f48c1589ad24fcd88867d3ad` (in `data/README.md`).
**Result:** `git status` lists only shareable files: the markdown files, notebook 01, `src/download_data.py`, `requirements.txt` and the 3 results files. `data/raw` and `data/processed` show as ignored.
**Nuances / gotchas:**
- **Arnav's `.venv` stayed one folder above the repo** (`MST_Motor_Temperature/.venv`). A Windows venv remembers its absolute path, so moving it would break `activate` and `jupyter.exe`, and rebuilding it would cost about 19 min. It also guarantees the venv can never be uploaded. Arnav runs `..\.venv\Scripts\python`; teammates create `.venv` inside their clone (git-ignored).
- **Notebook 01 was not re-run after the move.** Re-running would overwrite the logged load times (they vary per run). Its paths are relative (`Path.cwd().parent`), so it works from the new location.
- The top-level rules file on Arnav's laptop (it covers both MST and EST) now points to the repo path.
**Alternatives considered:**
- Copying files into the repo and keeping two copies: they would drift apart.
- Rebuilding the venv inside the repo: about 19 min for no benefit.
**Viva angle:** Q: How did five people work on one project without overwriting each other? A: One private GitHub repo. Everyone pulls before a session and pushes right after. Big data and the venv are git-ignored, and every step goes into one shared LOG.md.

---

## 2026-10-07 16:33 | Phase 1.1 | docs/problem.md written, with checked sources  (run by: Arnav)
**Tags:** [DECISION] [NUANCE]
**What we did:** Wrote `docs/problem.md`, the problem definition: why winding temperature matters, why a virtual sensor, objective, success criteria, users, constraints.
**Why:** Problem understanding is worth 5 marks, and every later choice (target, inputs, forbidden columns, metrics) comes from it.
**How:** Before using each source we opened and read it (team rule):
1. **Wikipedia, "Insulation system".** We took the IEC 60085 thermal classes (A 105, E 120, B 130, F 155, H 180 °C); hot spot = rated ambient (often 40 °C) + rise + 10 °C allowance; the rule of thumb "a halving of life for every 10 °C temperature increase".
2. **E. Cowern, "The Hot Issue of Motor Temperature Ratings", EC&M, 2000.** We took "insulation life doubles for each 10° of unused insulation temperature capability", and the class temperature being tied to about 20,000 h average life.
3. **Kirchgässner, Wallscheid & Böcker, IEEE Trans. Energy Conversion 2021 (arXiv:2001.06246)**, read from the PDF. We took:
   - "a three-phase PMSM of 50 kW mounted on a test bench … fs = 2 Hz";
   - their input signals "are commonly accessible in real-world traction drive systems … without further sensor upgrades";
   - their input list (ambient, coolant, u_d, u_q, i_d, i_q, motor speed) has **no torque**;
   - they use EWMA features and call them inevitable because the ML models assume independent samples.
**Result:** `docs/problem.md`, about 1.5 pages, 8 sections plus sources.
- **Target** = `stator_winding` (°C).
- **Inputs** = 8 measured signals, mapped to the statement's words.
- **Forbidden** = `pm`, `stator_tooth`, `stator_yoke`.
- **Success criteria:** beat the baselines (the numeric target is set *after* Phase 4 baselines), generalise to unseen sessions, safety (under-prediction), cheap to run.
**Nuances / gotchas:**
- **The dataset version matters.** The paper describes 139 h of data; our Kaggle version 3 has 184.84 h. Never quote the paper's numbers as ours.
- **Torque** is named in the statement but isn't in the authors' input list (torque is usually estimated in vehicles). We keep it, and test without it in the Phase 6 ablation. This backs up plan nuance N4 with a source.
- **The paper strongly supports our Phase 3 plan.** It uses EWMA features (spans in samples, α = 2/(span+1)), and its derived inputs include voltage and current magnitudes.
- **We dropped a "Montsinger / Arrhenius" attribution** for the 10 °C rule. It came from a search snippet we didn't open, so we only quote what the two opened sources say.
- **We don't know the test motor's insulation class**, so `docs/problem.md` never claims a limit for it. 141.36 °C is simply "below Class F".
**Alternatives considered:** Fixing a numeric target now (e.g. "RMSE < 2 °C"). Rejected: without baselines that would be a made-up number.
**Viva angle:** Q: Why does winding temperature matter? A: Insulation life roughly halves for every 10 °C hotter. Each insulation class has a maximum (Class F 155 °C, H 180 °C), so overheating shortens motor life, and over-caution (derating) wastes performance.

---

## 2026-10-07 16:40 | Phase — | Plan comparison: our PLAN.md vs the "Master Guide" → merged plan v2  (run by: Arnav)
**Tags:** [DECISION]
**What we did:** Compared our `PLAN.md` with the team's "Motor Temperature Project Master Guide" (a Word doc, 7-day plan) and decided which one to follow.
**Why:** Two plans would split the team. We need one, and it should be the stronger one.
**How:** Read all 14 sections of the Guide, then compared it point by point with `PLAN.md`.
**Result:**

| Point | Our PLAN.md | Master Guide | Winner |
|---|---|---|---|
| Thermal history (EWMA "memory" features) | Core idea | Deferred; "instantaneous inputs" only | **Ours.** The dataset authors call these features inevitable (Phase 1.1) |
| Physics features and coolant + offset baseline | Yes | Only optional magnitudes | Ours |
| Logging / concepts / viva system | Full | Templates | Ours |
| EDA only on training sessions (test frozen first) | No (EDA on all data) | Yes | **Guide** → adopted |
| Shared `src/config.py` contract | No | Yes | Guide → adopted |
| Metrics: p95 abs error, signed error, mean per-session MAE | No | Yes | Guide → adopted |
| Demo app as a core, early, parallel deliverable | Optional | Yes | Guide → adopted |
| Honesty: GE = scenario; "estimate now, not forecast" | Partly | Explicit | Guide → added to `docs/problem.md` |
| Boosting early-stopping trap (random internal validation) | Missing | Yes | Guide → added to Phase 4 |
| 7-day schedule, handoffs, fallback order | Missing | Yes | Guide → added to `PLAN.md` |
| Validation design | GroupKFold(5) CV | One fixed 70/15/15 session split | Ours (more stable with about 60 training sessions), with the Guide's fixed split as the compute fallback |

**Decision:** keep `PLAN.md` as the base and merge in the adopted points. Each one is marked **[v2]** in `PLAN.md`. The Word guide is now reference material, and `PLAN.md` is the single plan to follow.
**Nuances / gotchas:**
- **Adopting "EDA on training sessions only" means freezing the test split now**, in Phase 2.0, instead of in Phase 3. This is stricter: nothing seen in EDA can come from test sessions.
- The Guide's team roles (M1–M5) are close to ours (A–E). We keep ours (`PLAN.md` team table), but borrow the idea that the demo owner starts the app shell early, so E isn't idle while waiting for models.
- The Guide also notes that leakage columns aren't "invalid data in general"; they are excluded because of our sensor assumption. We adopted that wording in `docs/problem.md` and `VIVA_QA.md`.
**Alternatives considered:**
- Switch to the Guide fully: we'd lose the thermal-memory idea (likely a much weaker model) and our logging system, and redo Phase 0's work.
- Ignore the Guide: we'd miss real rigour improvements.
**Viva angle:** Q: How did you plan the project? A: We wrote a phase plan, compared it with a second team plan, and merged the best of both. We kept physics-based thermal-memory features (backed by the dataset authors' paper), and adopted training-only EDA, a shared config file and extra error metrics.

---

## 2026-10-07 16:42 | Phase 1 summary  (run by: Arnav)
**Tags:** [RESULT]
**What we did:** Finished Phase 1: problem understanding.

**1. Recap in simple words**
- The winding is the copper coil inside the motor. Heat ages its insulation, and life roughly halves per 10 °C hotter.
- Measuring the winding temperature directly needs an expensive, fragile sensor, so we build a **virtual sensor**: a model that estimates it from signals the controller already has.
- It is **supervised regression**: every training row has the true temperature, and the answer is a number in °C.
- **Target** `stator_winding`; **inputs** ambient, coolant, u_d, u_q, i_d, i_q, motor_speed, torque; **forbidden** pm, stator_tooth, stator_yoke.
- GE is the scenario. The data is a public Paderborn research motor (50 kW PMSM). We estimate the temperature *now*, not the future.

**2. Acceptance checklist**
- [x] `docs/problem.md` is written (sources read and logged in Phase 1.1).
- [x] A `LOG.md` entry exists (Phase 1.1 + this summary).
- [x] At least 5 motivation and domain Q&As in `VIVA_QA.md` (10 added under "Problem & motivation").

**3. What every teammate must be able to explain from this phase**
- Why winding temperature matters: insulation classes and the 10 °C rule.
- What a virtual sensor is, and why it beats adding a sensor.
- Which columns are inputs, the target and forbidden, and *why* the forbidden ones are forbidden.
- Why there is no accuracy target yet (set after baselines in Phase 4).
- The honest limits: one test-bench motor, data up to 141.36 °C, GE is only the scenario.

**4. Key numbers**

| Quantity | Value | Source |
|---|---|---|
| Insulation classes A/E/B/F/H | 105/120/130/155/180 °C | Wikipedia "Insulation system" |
| Test motor | three-phase PMSM, 50 kW | Kirchgässner et al. 2021 |
| Our data | 1,330,816 rows, 69 sessions, 184.84 h | `data_check_summary.json` |
| Hottest winding reading | 141.36 °C | same |
| Raw file SHA-256 | 78f3d150…67d3ad | `data/README.md` |

**Viva angle:** see "Problem & motivation" in `VIVA_QA.md`.

---

## 2026-10-07 16:41 | Phase 2.0 | Shared config + test sessions frozen BEFORE EDA (plan v2)  (run by: Arnav, running Phase 2 ahead for owner B)
**Tags:** [DECISION] [DATA] [NUANCE]
**What we did:** Created `src/config.py` (the shared contract) and `src/data.py` (loaders). Then picked and froze the 6 test sessions in `notebooks/02_eda.ipynb` section 3, saved to `outputs/results/split_profiles.json`.
**Why:**
- If we explored the test sessions, what we saw could steer our feature and model choices, and the final test would stop being a fair exam.
- One shared `config.py` stops teammates using different column lists.
**How:**
- `src/config.py` holds `TARGET="stator_winding"`, `INPUTS` (8 signals), `FORBIDDEN=["pm","stator_tooth","stator_yoke"]`, `GROUP="profile_id"`, `SEED=42`, `SAMPLE_RATE_HZ=2`, and the paths.
- **The rule was written before drawing:**
  1. Split the 69 sessions into 3 equal length groups (`pd.qcut` on rank: 23 short, 23 medium, 23 long).
  2. `np.random.default_rng(42)` picks 2 sessions per group.
  3. Accept only if the test rows are 10–15 % **and** at least one test session is "hot" (its max winding > 128.05 °C, the 75th percentile of session maxima) **and** one is "cool" (its max < 114.81 °C, the median).
**Result:**
- **Test sessions: 6, 7, 21, 61, 66, 81.** Accepted on the **first** draw.
- Test = 141,024 rows = **10.60 %**. Training = **63 sessions, 1,189,792 rows**.
- `outputs/results/split_profiles.json` (committed).
**Nuances / gotchas:**
- **Never re-draw the split.** Phases 3–5 must load `split_profiles.json`. A new draw would quietly change every number.
- **The "hot/cool" check looks only at each test session's *maximum* temperature**, a one-number summary, so the test set is representative. That's stratification, not tuning: no model saw anything, and no signal from test sessions was plotted.
- **The "short" draw picked the longest of the short sessions** (7 and 61 are about 2.0 h each; the short group spans 0.302–2.054 h). So the test set has **no very short session (under 1 h)**. The rule allowed this, and we didn't re-draw to "fix" it, because that would mean choosing the test set by hand. Phase 5 should mention that very short sessions are only in training.
- Figure 1 marks which sessions are test, using **only their length**.
**Alternatives considered:**
- Freezing the test in Phase 3 (the original plan): EDA would then have seen the test sessions.
- A plain random choice of 6 sessions: could end up with only short sessions, or no hot one.
- `GroupShuffleSplit` (the Master Guide's way): fine too, but it doesn't guarantee a mix of lengths.
**Viva angle:** Q: How did you choose your test set, and why before EDA? A: Six whole sessions, two from each length group, drawn with seed 42 and checked for 10–15 % of rows plus one hot and one cool session. We froze them before exploring, so nothing we saw could leak into our choices.

---

## 2026-10-07 16:44 | Phase 2.1 | EDA figures 1–4: sessions, one session over time, distributions, correlations  (run by: Arnav)
**Tags:** [EDA] [RESULT] [NUANCE]
**What we did:** Made the first 4 required EDA figures, on training sessions only.
**Why:** To understand the data's structure and the target before choosing features and models. Visualisation is explicitly required by the instructions.
**How:** `notebooks/02_eda.ipynb` sections 5–8, using matplotlib/seaborn and `src/plotting.py` (`save_figure`, PNG dpi = 150). Pearson correlation via `df_train[columns].corr()`.
**Result:**
- `outputs/figures/eda_01_session_lengths.png`: sorted session lengths (0.302–6.107 h); test sessions marked. Shows the test set includes long and medium sessions.
- `outputs/figures/eda_02_session20_over_time.png`: training session 20 (the longest, 6.1 h), all signals on one minute axis.
  - Speed and torque are held steady for minutes at a time, and after every step the winding moves along a smooth curve, not a jump.
  - When the coolant setting is raised partway through, the winding's "floor" rises too.
  - Winding 19.18–125.38 °C, coolant 15.59–66.91 °C.
- `outputs/figures/eda_03_histograms.png`: all 12 measured columns.
  - Target (training) 18.59–141.36 °C; median 64.63; 10th percentile 25.89; 90th percentile 104.79 °C.
  - Coolant mostly sits at one low setting.
  - Speed has many fixed levels, and torque and `i_q` spike at 0 (idle).
  - `i_d` max 0.1 A.
- `outputs/figures/eda_04_correlation_heatmap.png` (+ `eda_correlation_matrix.csv`, `eda_target_correlations.csv`). r with the target:
  - stator_tooth **0.970**, stator_yoke **0.862**, pm **0.796** (all forbidden);
  - best allowed: i_d **−0.632**, coolant **0.505**, motor_speed **0.424**, ambient 0.339, u_d −0.229, torque 0.105, i_q 0.076, u_q 0.031;
  - derived: i_s 0.583, i_s² 0.542.
**Nuances / gotchas:**
- **The leakage is now proven with numbers.** The forbidden temperatures correlate 0.80–0.97 with the target, far above any allowed input.
- **`torque` vs `i_q`: r = 0.9965.** Torque is almost a scaled copy of `i_q`. That fits torque being *derived from current* rather than measured independently, and it backs up plan nuance N4 and the Phase 1.1 source. Expect the "no torque" ablation (Phase 6) to cost little.
- **A negative r for i_d is not "cooling".** `i_d` goes more negative at high speed (field weakening, r with speed = −0.68), and high speed goes with higher temperatures. Correlation is not causation.
- **The low r for torque and i_q (0.105, 0.076) doesn't mean current is unimportant.** Their sign flips between motoring and braking, which cancels out in a straight-line correlation. Magnitudes (`i_s`, 0.583) fix that. This is why Phase 3 uses magnitudes.
- All of this is on **training rows only**. Test sessions were never loaded into these plots.
**Alternatives considered:** Spearman (rank) correlation, which catches non-linear but monotonic links. We kept Pearson as the plan says; it's enough to show the leakage and the weak instantaneous inputs.
**Viva angle:** Q: What did the correlation heatmap tell you? A: The forbidden temperatures correlate 0.97 / 0.86 / 0.80 with the winding, which proves they'd leak. The best allowed input only reaches |r| 0.63, so no single signal is enough. And torque ≈ i_q (r 0.9965).

---

## 2026-10-07 16:46 | Phase 2.2 | EDA figures 5–8: hexbins, operating region, per-session boxes, thermal lag  (run by: Arnav)
**Tags:** [EDA] [RESULT] [NUANCE] [BUG]
**What we did:** Made the remaining 4 required figures, including the key "thermal lag" analysis.
**Why:** To test the plan's central idea (N3): that the winding has thermal memory, so EWMA features of the past should help.
**How:** `notebooks/02_eda.ipynb` sections 9–12.
- Hexbin: `gridsize=60, bins="log"`.
- Operating region: 100,000 random training rows, `random_state=42`.
- Boxplots: `showfliers=False`.
- **Lagged correlation:** for each training session ≥ 90 min (53 sessions), corr(`i_s²(t)`, winding(t + lag)) for lags 0–60 min in 0.5-min steps. Saved per session to `eda_thermal_lag_per_session.csv`.
**Result:**
- `outputs/figures/eda_05_hexbin_current_and_coolant.png`:
  - At almost every current value the winding spans nearly its whole range, so the present current alone can't tell the temperature.
  - Winding minus coolant: median **26.47 °C**, min **−29.66**, max 121.39 °C. In **4.75 %** of rows the winding is cooler than the coolant.
- `outputs/figures/eda_06_operating_region.png`:
  - The data covers the full torque–speed envelope (high torque at low speed, a falling limit at high speed).
  - Hot and cool points are mixed everywhere.
  - Median winding by speed band: **49.05 °C** (< 1000 rpm), **62.46 °C** (1000–3000), **82.92 °C** (> 3000).
- `outputs/figures/eda_07_boxplots_per_session.png`: 63 training sessions. Medians **19.88–116.74 °C**, maxima **39.10–141.36 °C**.
- `outputs/figures/eda_08_thermal_lag.png`:
  - (a) Session 20, minute 74.7: the current steps from **34.1 A to 305.9 A** within 10 s. The temperature climbs for the whole time the current is on, and takes many minutes to cool after it drops.
  - (b) Across 53 sessions: **median best lag 2.5 min** (25th–75th percentile 1.0–3.0); median r **0.645 at lag 0 → 0.746 at the best lag**; **47 of 53** sessions peak under 5 min. The median curve itself peaks at **1.5 min** (r 0.746).
**Nuances / gotchas:**
- **"Median of the peaks" (2.5 min) is not the same as "peak of the median curve" (1.5 min).** Both are correct; they summarise differently. Quote whichever you name, with its name.
- **The lag is not the thermal time constant.** Lagged correlation only shows that the temperature reacts to *recent past* current, within minutes. In Fig 8(a) the heating and cooling run over many minutes, which is why Phase 3 uses EWMA spans of 1, 5, 15 and 45 min.
- **6 of 53 sessions (42, 45, 62, 63, 71, 75) peak at 33–55 min, with weaker correlations** (best r 0.30–0.67). Their curves have no clear early peak, so a single lag isn't meaningful for them. The median is robust to them.
- **The winding below the coolant (4.75 % of rows)** happens when the coolant is heated faster than the winding can follow (visible in Fig 2). So the coolant's *history* matters too, which supports EWMA on coolant as planned.
- **Boxplots hide outlier dots** (`showfliers=False`). With about 19,000 rows per session they would cover the plot. The whiskers still show the 1.5 × IQR range.
- **Fig 6 uses a 100,000-row random sample** only to keep the picture readable. No analysis uses the sample.
- **[BUG] Fig 8(a) first had the step about 2 min to the left of zero.**
  - Cause: the step was found on a 2-minute *trailing* rolling mean, which reacts late.
  - Fix: find the biggest raw jump of `i_s²` within 10 s (`diff(20)`).
  - Two smaller layout fixes: the Fig 4 title overlapped the colour bar (shortened), and the Fig 5 dashed line overshot the coolant range.
**Alternatives considered:**
- Ordinary scatter plots for Fig 5: 1.2M points become a blob, so we used hexbin.
- Fitting a first-order thermal model to get real time constants: interesting, but beyond EDA. Logged as an `[IDEA]` for future work.
**Viva angle:** Q: How do you know the motor has thermal memory? A: In Fig 8(a) the temperature keeps rising for minutes after a current step and cools slowly after it. Across 53 sessions the current–temperature correlation is best when the temperature is shifted a median 2.5 min later (r 0.645 → 0.746). So past current matters, and that's why we add EWMA features.

---

## 2026-10-07 16:47 | Phase 2.3 | Data-quality follow-ups from the Phase 0 handover  (run by: Arnav)
**Tags:** [DATA] [DECISION]
**What we did:** Located the two oddities flagged in Phase 0.
**Why:** The Phase 0 handover asked for it. Odd values must be understood before deciding whether to clean them.
**How:** `notebooks/02_eda.ipynb` section 13. These are raw-signal audits on the full file, as in notebook 01.
**Result:**
- The ambient readings below 15 °C are **4 rows in session 44** (lowest 8.78 °C) and **1 row in session 68**.
- The biggest one-step winding change, **1.394 °C**, is in **session 65, minute 82.1**.
- Both are training sessions.
**Nuances / gotchas:** 5 rows out of 1,189,792 training rows can't move a model, and they could be a real brief draught or a sensor blip. Deleting real-looking data needs a reason, and we have none.
**Alternatives considered:**
- Delete the 5 ambient rows: it would break the 0.5 s time spacing inside those sessions, which matters for EWMA.
- Interpolate them: no benefit.
**Decision:** keep both as they are (no cleaning). Logged so Phase 3 doesn't repeat the investigation.
**Viva angle:** Q: Did you remove outliers? A: No. We found only 5 ambient readings below 15 °C (sessions 44 and 68) and one 1.39 °C jump (session 65). They're plausible, tiny in number, and removing rows would break the time spacing the memory features need.

---

## 2026-10-07 16:50 | Phase 2.4 | Interactive showcase page for Phases 1–2  (run by: Arnav)
**Tags:** [SETUP] [RESULT]
**What we did:** Built an interactive showcase, "Motor Winding Explorer", for the presentation.
- Phase 1 idea: the virtual-sensor diagram and the insulation-class scale.
- A session explorer: click any of the 63 training sessions and see temperatures, current, speed and torque, with a synchronised hover readout.
- The thermal-lag curve and histogram, correlation bars plus heatmap, the speed–torque map coloured by average temperature, and the top-5 insights.
**Why:** The viva is 20 marks, and a live, clickable view of the data explains the findings much better than static slides. It also lets every teammate study the data without running Python.
**How:**
- `notebooks/02_eda.ipynb` section 15 exports `docs/showcase/eda_data.js` (0.74 MB): 1-minute averages of the **training sessions only**, plus the correlation matrix, the lag results, a 32 × 30 speed–torque grid of mean winding temperature, and `eda_summary.json`.
- `docs/showcase/index.html` (about 44 KB) draws everything with plain SVG, no libraries. Open it in any browser straight from the repo (needs internet only for fonts).
- Every number on the page is read from the exported summary, not typed by hand.
- Published copy (data inlined): published online; ask Arnav for the link.
**Result:** The page renders with no console errors, in light and dark mode and at narrow widths (checked in a local browser via `python -m http.server`).
**Nuances / gotchas:**
- **Test sessions are hatched and not clickable**, and their signals aren't in the export. The showcase keeps the same "test stays locked" rule as the notebook.
- **Opening `index.html` in an editor's preview pane as a "static snapshot" shows a blank page**, because the snapshot can't load the separate `eda_data.js`. That's a preview quirk. Opening the file normally in Chrome or Edge, or serving the folder, works.
- **Curves are 1-minute averages**, so very fast spikes are smoothed. The PNG figures use full 2 Hz data.
**Alternatives considered:**
- Plotly or Chart.js: extra libraries and bigger pages.
- Streamlit now: that's the Phase 6 demo, and it needs a model; this page is EDA-only.
**Viva angle:** Q: How will you show your EDA in the presentation? A: With the 8 required PNG figures, plus a live explorer page where we click through training sessions and show the thermal lag interactively. Every number on it comes from our results files.

---

## 2026-10-07 16:52 | Phase 2 summary  (run by: Arnav)
**Tags:** [EDA] [RESULT]
**What we did:** Finished Phase 2 (EDA), the v2 version: test sessions frozen first, and EDA on training sessions only.

**1. Recap in simple words**
- We locked away 6 whole test sessions (6, 7, 21, 61, 66, 81; 10.60 % of rows) before looking at anything, so the final exam stays fair.
- On the 63 training sessions we made the 8 required figures and saved every number to `outputs/results/`.
- The forbidden temperatures correlate 0.80–0.97 with the winding, which is proof of leakage. The best allowed signal reaches only |r| = 0.632.
- The winding has **thermal memory**: it follows the heating current a median 2.5 min late, and heats and cools over many minutes. This is the case for EWMA features.
- Sessions are very different (medians 19.88–116.74 °C), torque ≈ i_q (r 0.9965), and we keep the few odd readings because they are plausible.

**2. Acceptance checklist**
- [x] At least 8 figures are saved, each described in `LOG.md` (Phases 2.1, 2.2; `eda_01` … `eda_08`).
- [x] A "Top 5 EDA insights" list is in `LOG.md` (below) and in the notebook (section 16).
- [x] Concepts added: correlation (and why it is not causation), hexbin, distribution and outlier (plus data leakage, test-set freezing, lagged correlation).
- [x] [v2] Test sessions frozen before EDA; `src/config.py` created.

**Top-5 EDA insights**
1. The forbidden temperatures would leak: r = 0.970 / 0.862 / 0.796, against |r| = 0.632 for the best allowed input.
2. No single allowed signal explains the winding: at the same current it can be cold or hot. We need many inputs and non-linear models.
3. Thermal memory: the median best lag is 2.5 min, and r rises 0.645 → 0.746. So we add EWMA features in Phase 3.
4. Coolant sets the floor with its own lag: the winding is a median 26.47 °C above the coolant, but below it in 4.75 % of rows.
5. Sessions differ a lot (lengths 0.302–6.107 h, medians 19.88–116.74 °C). So we split by session and report per-session errors. Also, torque ≈ i_q (r 0.9965).

**3. What every teammate must be able to explain from this phase**
- Why the test sessions were frozen **before** EDA, and how they were chosen (the rule, seed 42, first draw).
- What Pearson r measures, why the forbidden columns' high r proves leakage, and why correlation ≠ causation (the i_d example).
- How the lag analysis works, and what 2.5 min / 0.645 → 0.746 means.
- Why hexbin instead of scatter, why boxplot fliers are hidden, and why Fig 6 uses a sample.
- Why we didn't remove the 5 odd ambient rows.

**4. Key numbers**

| Quantity | Value | Source |
|---|---|---|
| Test sessions / share of rows | 6, 7, 21, 61, 66, 81 / 10.60 % | `split_profiles.json` |
| Training sessions / rows | 63 / 1,189,792 | same |
| r with target: tooth, yoke, pm | 0.970, 0.862, 0.796 | `eda_target_correlations.csv` |
| Best allowed r: i_d, coolant, speed | −0.632, 0.505, 0.424 | same |
| torque vs i_q | r = 0.9965 | `eda_correlation_matrix.csv` |
| Lag: median best, IQR, r lag0 → best | 2.5 min, 1.0–3.0, 0.645 → 0.746 | `eda_summary.json` |
| Winding − coolant: median, % below 0 | 26.47 °C, 4.75 % | same |
| Session medians / maxima | 19.88–116.74 / 39.10–141.36 °C | `eda_session_summary.csv` |

**Viva angle:** see the "EDA" section of `VIVA_QA.md`.

---

## 2026-10-07 16:53 | Phase — | [IDEA] Future-work points spotted during EDA  (run by: Arnav)
**Tags:** [IDEA]
**What we did:** Noted ideas for the "future work" slide.
**Why:** So they aren't lost.
**How:** —
**Result:**
- Fit a simple first-order thermal model (one time constant per session) and compare it with the ML model.
- Use EWMA of the coolant, not only of current, because the winding lags coolant changes (4.75 % of rows below the coolant).
- Check a "no torque" model early (torque ≈ i_q, r 0.9965). It might be just as good and more realistic for vehicles.
**Nuances / gotchas:** —
**Alternatives considered:** —
**Viva angle:** Q: What would you do with more time? A: Compare against a physics-based first-order thermal model, and drop torque, since it's nearly a copy of i_q.

---

## 2026-10-07 16:55 | Handover  (run by: Arnav)
**Tags:** —
**Where we stopped:** Phases 0, 1 and 2 are done and ticked in `PLAN.md`. Plan v2 (merged with the Master Guide) is in force. The repo has **not been committed or pushed yet**.
**What's next (exact next step):**
1. Arnav: review `git status`, then commit and push (commands in `README.md`).
2. Phase 3 (owner C), following the Phase 3 section of `PLAN.md`. It must **load** `outputs/results/split_profiles.json` (never re-draw it) and the shared lists from `src/config.py`.
**Open issues / questions:**
- Phase 2 was run by Arnav ahead of time, so owner **B** should review notebook 02 and these log entries, and must still be able to present the EDA slide. The team may want to give B another task, for example starting the flow diagram or helping E with the app shell.
- Team names (B–E) and the MST deadline are still missing from `PLAN.md`.
- `misc.txt` (a YouTube link) is still unexplained.
- Teammates need to be added as collaborators on the GitHub repo, and invited as Editors on the tracker page.
**Before you start, you must know:**
- **Training sessions only**, until Phase 5. Never plot or tune on sessions 6, 7, 21, 61, 66, 81.
- `src/config.py` is the single source for `TARGET`, `INPUTS` and `FORBIDDEN`. Import it; don't retype the column lists.
- **EWMA must be computed per session, in file order, before any subsampling** (N3 and N9). Our EDA suggests spans of 1, 5, 15 and 45 min are sensible, and that the coolant needs EWMA too.
- Arnav's venv is `..\.venv`. Teammates create `.venv` inside their clone.

---

## 2026-10-10 08:40 | Phase — | Session start: Arnav asked to run all remaining phases (3–7)  (run by: Arnav)
**Tags:** [DECISION] [SETUP]
**What we did:**
- Phases 3–7 were run end to end in one go (everyone's parts), with full logging.
- Checked the repo: `main` is in sync with `origin/main` (one commit, "v1"), nothing new from teammates.
- Installed `streamlit` for the Phase 6 demo.
**Why:** The team wants the whole MST pipeline done and documented. Each owner (C, D, E, …) must still study their phase's notebook and log entries, and present it.
**How:**
- `git fetch` + `git status`.
- `pip install streamlit` → **streamlit 1.65.0**, 168 s.
- Laptop: 16 CPU cores and 15.7 GB RAM, about 3.2 GB free at the start, so model training was kept memory-light.
**Result:** Entries from here on say "(run by: Arnav, for owner X)". The owner of each phase should review it before presenting it.
**Nuances / gotchas:**
- The plan's rule is "one phase per session". Here Arnav explicitly asked for all phases. Each phase still gets its own summary entry and acceptance checklist.
- Streamlit is added to `requirements.txt` pinned at 1.65.0, as the plan says ("add streamlit when this starts, and log it").
**Alternatives considered:** Stopping after each phase for review. Not what was asked; owners review afterwards instead.
**Viva angle:** Q: Who did what? A: Phases were owned per member (`PLAN.md` team table). Every step is logged with numbers, and each owner reviewed and presents their part.

---

## 2026-10-10 08:55 | Phase 3.1 | Cleaning re-checked, physics + EWMA features built, causality proven  (run by: Arnav, for owner C)
**Tags:** [DATA] [DECISION] [NUANCE] [RESULT]
**What we did:**
- Wrote `src/features.py` (shared by training, evaluation and the app) and `notebooks/03_preprocessing_features.ipynb`.
- Re-checked that no cleaning is needed, then added 5 physics features and 32 EWMA "thermal memory" features: **45 model inputs** in total.
**Why:**
- Phase 2 showed that no single raw signal explains the winding (best |r| 0.632), and that the winding follows the current with a delay of minutes.
- Physics features turn signals into quantities linked to heat. EWMAs give the model memory of the recent past.
**How:**
- **Cleaning:** 0 missing values, 0 duplicates, 69 unbroken session blocks (asserted in code). Row order kept.
- **Physics:** `i_s = √(i_d²+i_q²)`, `u_s = √(u_d²+u_q²)`, `i_s_sq = i_s²`, `p_el = 1.5·(u_d·i_d + u_q·i_q)`, `p_mech = torque·speed·2π/60`.
- **EWMA:** `df.groupby("profile_id")[col].transform(lambda s: s.ewm(span=sp, adjust=True).mean())`.
  - Spans **120 / 600 / 1800 / 5400 samples = 1 / 5 / 15 / 45 min**.
  - Applied to 8 base signals: `i_s, i_s_sq, p_el, u_s, motor_speed, torque, coolant, ambient`.
- **Feature sets** (for the Phase 6 ablation): raw 8, full 45, no_ewma 13, no_engineered 24, no_torque 39, with_leakage 48.
**Result:**
- Physics features took 0.4 s and EWMA features under 4 s (3.5–3.8 s across runs).
- `data/processed/features.parquet`: 298.3 MB, git-ignored.
- `outputs/results/feature_list.json`, `features_summary.json` and `feature_target_correlations.csv` are committed.
- Training ranges: `i_s` 0–361.52 A; `p_el` −44,473 to 52,472 W; `p_mech` −55,121 to 49,618 W.
**Nuances / gotchas:**
- **Causality is proven, not assumed.** We computed the EWMAs of session 20 on its first 10,000 rows only, and compared them with the full-session run. The largest difference was **0.0**, so no future data leaks in.
- **Computing EWMA on test rows is not leakage.** Each test row only uses its own session's past signals, which is what a real controller would have. Nothing is learned from other rows.
- **Warm-up:** 27.9 % of training rows lie in the first 45 min of their session (9.5 % within 15 min, 3.2 % within 5 min). There, the long EWMAs are still "settling". With `adjust=True`, the first EWMA value equals the raw value. Expect bigger errors near session starts.
- **Why 1.5 in `p_el`:** the dataset's dq values use the amplitude-invariant Park transform, where three-phase power = 1.5·(u_d·i_d + u_q·i_q). Without the 1.5 the "power" would be off by a constant. That doesn't hurt trees, but it would be physically wrong.
- **`p_el` vs `p_mech`:** their training means are 7,722 W vs 6,601 W. The difference is roughly the motor's losses (heat!), a nice physics sanity check. We don't use it as a feature, to keep things simple.
- `features.parquet` also stores the 3 forbidden temperatures, **only** for the Phase 6 "with leakage" ablation. They are not in the 45-feature list.
**Alternatives considered:**
- Rolling (flat-window) means: abrupt edges, and they need a full window, so they're worse at session starts.
- EWMS (exponentially weighted standard deviation, used by the dataset authors): more features for less gain; logged as an `[IDEA]`.
- An LSTM sequence model: much more complex, and not needed when EWMAs already carry the memory.
**Viva angle:** Q: What is EWMA and why did you use it? A: An average of the past where recent values count more. The winding temperature depends on the last few minutes of current (thermal inertia). The 5-minute EWMA of current has r = 0.705 with the winding temperature, against 0.583 for the raw current.

---

## 2026-10-10 08:57 | Phase 3.2 | Feature figures and the leakage checklist  (run by: Arnav, for owner C)
**Tags:** [EDA] [RESULT] [DECISION]
**What we did:** Plotted a raw signal against its EWMAs, and the correlation of all 45 features with the target (training rows). Then ran the leakage checklist in code.
**Why:** To show visually that the memory features track the temperature better than raw signals, and to prove that no leakage got in.
**How:** `notebooks/03_preprocessing_features.ipynb`, sections 8, 9 and 11.
**Result:**
- `outputs/figures/feat_01_ewma_example.png`: session 20. Raw `i_s²` jumps instantly, and longer EWMAs are smoother and lag more. The 5-min EWMA follows the shape of the winding curve far more closely than the raw signal.
- `outputs/figures/feat_02_feature_target_correlation.png`: all 45 features sorted by |r|.
  - **The top 5 are all EWMAs of current:** `i_s_ewma_600` 0.705, `i_s_sq_ewma_600` 0.685, `i_s_ewma_1800` 0.673, `i_s_ewma_120` 0.655, `i_s_sq_ewma_1800` 0.651.
  - Best |r| per group: EWMA 0.705, raw 0.632, physics 0.583.
- **Leakage checklist:**
  - [x] No `pm`, `stator_tooth` or `stator_yoke` in the features.
  - [x] `profile_id` is not a feature.
  - [x] The target is not a feature.
  - [x] EWMA computed per profile and causally (max difference 0.0).
  - [x] Test profiles untouched by any tuning (features only *computed* for them).
  - [ ] → [x] in Phase 4: the scaler is fitted only on training folds (it sits inside a `Pipeline`).
**Nuances / gotchas:**
- **The 5-min span correlates best, not the 45-min one** (0.705 vs 0.558 for `i_s_ewma_5400`). That fits the Phase 2 lag of a few minutes. The long spans still matter to models, as a slow "baseline heat" signal.
- **Correlation only measures straight-line links.** Trees can use features with low r (e.g. `torque_ewma`) in non-linear ways, so we keep all 45 and let regularisation and the models decide.
**Alternatives considered:** Feature selection by correlation threshold. Rejected: it would throw away features that only help non-linearly. Lasso shows which features a linear model can drop (Phase 4).
**Viva angle:** Q: How do you know the EWMA features help? A: Their correlation with the winding temperature is higher (best 0.705 vs 0.583 raw), and the Phase 4 models and the Phase 6 ablation measure the RMSE gain directly.

---

## 2026-10-10 09:00 | Phase 3 summary  (run by: Arnav, for owner C)
**Tags:** [RESULT]
**What we did:** Finished Phase 3: pre-processing and feature engineering.

**1. Recap in simple words**
- No cleaning was needed. We re-proved it in code, and kept the row order.
- The split was loaded from `split_profiles.json`, never re-drawn.
- We added 5 physics features (current/voltage magnitude, current², electrical and mechanical power).
- We added 32 EWMA "memory" features (8 signals × 1, 5, 15, 45 min), per session and past-only. We proved they use no future data.
- The memory features correlate best with the winding temperature (0.705 vs 0.583 raw). 45 inputs are saved for Phase 4.

**2. Acceptance checklist**
- [x] The leakage checklist is fully ticked (the scaler item is enforced by the Pipeline in Phase 4, logged there).
- [x] The processed data and feature list are saved (`data/processed/features.parquet`, `outputs/results/feature_list.json`).
- [x] Figures are saved and logged (`feat_01`, `feat_02`).
- [x] Concepts added: data leakage (Phase 2), train/validation/test, GroupKFold, feature engineering, EWMA (with formula and span), standardisation.

**3. What every teammate must be able to explain from this phase**
- Each physics feature's formula and why it relates to heat (I²R; why the 1.5 in p_el).
- What an EWMA is: the formula μ_t = (1−α)μ_{t−1} + αx_t, α = 2/(span+1), and the span-to-minutes conversion (÷120).
- Why EWMA must be per session, past-only and computed before thinning, and how we proved causality.
- Why computing features on test rows is not leakage.
- The warm-up problem at session starts.

**4. Key numbers**

| Quantity | Value | Source |
|---|---|---|
| Model inputs | 45 (8 raw + 5 physics + 32 EWMA) | `feature_list.json` |
| EWMA spans | 120/600/1800/5400 samples = 1/5/15/45 min | same |
| Causality check | max difference 0.0 | `features_summary.json` |
| Best r: raw i_s → i_s EWMA 5 min | 0.583 → 0.705 | same |
| Training rows in the 45-min warm-up | 27.9 % | same |
| features.parquet | 298.3 MB (git-ignored) | same |

**Viva angle:** see "Pre-processing & features" in `VIVA_QA.md`.

---

## 2026-10-10 09:01 | Phase 4.1 | Cross-validation protocol, timing tests, baselines and linear models  (run by: Arnav, for owner D)
**Tags:** [DECISION] [RESULT] [NUANCE]
**What we did:**
- Wrote `src/modelling.py`: the `CoolantPlusOffset` baseline, `regression_metrics()`, `group_cv()` (GroupKFold(5) by session, which also records training RMSE) and `summarise_cv()`.
- Built `notebooks/04_modelling.ipynb` and ran B0, B1, M1, M2, Ridge and Lasso.
**Why:** We needed one fair protocol for every model: same rows, same folds, unseen sessions in every validation fold.
**How:**
- **Timing test first:** one fit on every 10th training row (95,184 rows) took Linear 0.7 s, Ridge 0.3 s, Lasso 21.2 s, Random Forest (100 trees, depth 16) 99.0 s and LightGBM (600 trees) 19.1 s.
- **Decision:** all CV uses **every 10th training row** (`K_CV = 10`): 118,980 rows from 63 sessions.
- Ridge α ∈ {0.01, 0.1, 1, 10, 100, 1000}; Lasso α ∈ {0.01, 0.1, 1.0}. Scaling sits inside `Pipeline([StandardScaler, model])`.
**Result (CV RMSE mean ± std over 5 folds, °C):**
- **B0 mean** 29.088 ± 1.258 (R² −0.031).
- **B1 coolant + offset** 26.033 ± 1.636 (R² 0.159).
- **M1 Linear, 8 raw inputs** 16.093 ± 1.600 (R² 0.681).
- **M2 Linear, 45 features** 5.178 ± 0.565 (R² 0.966).
- **Ridge** best at α = 10: 5.172 ± 0.576.
- **Lasso** best at α = 0.01: 5.202 ± 0.615. It dropped 11 features: ambient, u_d, p_el, i_s_ewma_120, i_s_ewma_600, i_s_ewma_5400, p_el_ewma_120, u_s_ewma_1800, motor_speed_ewma_120, torque_ewma_120, ambient_ewma_120. At α = 1.0 it dropped 34 features and got worse (6.575, underfitting).
- Figure `outputs/figures/model_02_regularisation.png`: Ridge is flat for α ≤ 100 and worse at 1000; Lasso gets worse as α grows.
**Nuances / gotchas:**
- **Feature engineering is worth 10.9 °C.** The same linear model goes 16.093 → 5.178 °C (−68 %) just from the physics + EWMA features. This is the main "thermal memory" evidence, together with the Phase 6 ablation.
- **The coolant thermometer alone barely helps:** B1 is 26.03 vs 29.09 °C for B0.
- **Lasso dropping some EWMAs doesn't mean they're useless.** They are highly correlated with their neighbours (e.g. `i_s_ewma_600` vs `i_s_sq_ewma_600`), and Lasso keeps one per group.
- **The scaler is inside the Pipeline.** This ticks the last leakage-checklist item from Phase 3.
**Alternatives considered:**
- Full-resolution CV: about 10× slower for Random Forest, with no expected gain, since neighbouring rows are near-copies (measured in Phase 4.3).
- `LassoCV`/`RidgeCV`: they use row-random folds by default, which leak. We used our own group folds instead.
**Viva angle:** Q: How much did feature engineering help? A: The same Linear Regression went from 16.09 °C RMSE (8 raw signals) to 5.18 °C (45 physics + EWMA features), on unseen sessions in 5-fold group CV.

---

## 2026-10-10 09:20 | Phase 4.2 | Random Forest, LightGBM and MLP tuned; CV table  (run by: Arnav, for owner D)
**Tags:** [RESULT] [NUANCE] [DECISION]
**What we did:** Tuned Random Forest (4 configurations) and LightGBM (8), trained one MLP, and saved the comparison table.
**Why:** To test whether non-linear models beat the linear ones on unseen sessions.
**How:**
- **Configurations:** `ParameterSampler(..., random_state=42)`.
  - RF: `n_estimators=100, max_samples=0.5`, with depth {12, 20, None}, `min_samples_leaf` {5, 20, 50}, `max_features` {0.33, 0.5}.
  - LightGBM: `num_leaves` {15, 31, 63, 127}, `learning_rate` {0.03, 0.05, 0.1}, `n_estimators` {300, 600, 1000}, `min_child_samples` {20, 100, 300}, `colsample_bytree` {0.7, 1.0}, `subsample` {0.8, 1.0}, **no early stopping**.
  - MLP: `(64, 32)`, `alpha=1e-4`, `batch_size=512`, `max_iter=40`, `early_stopping=False`, scaled inputs.
- Saved `outputs/results/cv_results.csv`, `tuning_rf.csv`, `tuning_lgbm.csv` and the figure `model_01_cv_comparison.png`.
**Result:**

| Model | CV RMSE (°C) | MAE | R² | Training RMSE | Fit s/fold |
|---|---|---|---|---|---|
| M6 MLP (64-32) | **4.919 ± 0.763** | 3.116 | 0.970 | 2.663 | 17.1 |
| M5 LightGBM (15 leaves, 1000 trees, lr 0.1, min_child 300, subsample 0.8) | 5.061 ± 0.836 | 3.317 | 0.968 | 1.144 | 5.8 |
| M3 Ridge (α = 10) | 5.172 ± 0.576 | 3.052 | 0.966 | 4.992 | 0.3 |
| M2 Linear (45) | 5.178 ± 0.565 | 3.067 | 0.966 | 4.987 | 0.5 |
| M3 Lasso (α = 0.01) | 5.202 ± 0.615 | 3.019 | 0.966 | 5.046 | 23.2 |
| M4 Random Forest (depth 12, leaf 20, max_features 0.33) | 5.822 ± 0.844 | 3.787 | 0.958 | 2.327 | 10.3 |

- MLP per fold: RMSE 5.215 / 5.967 / 4.449 / 5.231 / 3.734 °C; max |error| 76.3 / 45.1 / 47.7 / 44.1 / 63.9 °C.
- `model_01_cv_comparison.png`: bars = validation RMSE ± std, dots = training RMSE.
**Nuances / gotchas:**
- **The trees overfit sessions.** LightGBM's training RMSE is 1.14 vs 5.06 °C validation; Random Forest's is 2.33 vs 5.82 °C. The linear models have almost no gap (4.99 vs 5.17). Trees also can't extrapolate beyond their leaves.
- **The top five models are within 0.3 °C** (4.92–5.20), smaller than their fold std (0.57–0.84). CV can't really separate them. This matters in Phase 5.
- **The worst single errors are huge (44–76 °C per fold)** while 95 % of out-of-fold errors are below 9.41 °C. Hypothesis, checked in Phase 5: session starts. 16 of 63 training sessions start above 30 °C (session 46 starts at 99.3 °C).
- **Figure 1 cosmetics:** the value labels overlap the error bars and the legend overlaps the B0 bar. Not fixed, because that needs a 23-min re-run; the Phase 5 figure `eval_12` shows the same models more clearly.
**Alternatives considered:**
- A bigger tuning budget: a 23-min notebook run is already near the laptop's practical limit, and differences are below fold noise anyway.
- `HistGradientBoostingRegressor` (the Master Guide's choice): it's sklearn's version of the same algorithm as LightGBM, which was already installed.
**Viva angle:** Q: Which model was best in cross-validation, and was it clearly best? A: The MLP, at 4.92 ± 0.76 °C, but five models were within 0.3 °C, less than the fold spread, so CV couldn't really separate them.

---

## 2026-10-10 09:22 | Phase 4.3 | Subsampling check, finalists, out-of-fold errors, saved models, success target  (run by: Arnav, for owner D)
**Tags:** [DECISION] [RESULT] [NUANCE]
**What we did:** Checked what the 10× row thinning costs, applied the pre-written finalist rule, computed out-of-fold (OOF) errors, retrained and saved the finalists, and set the numeric success target **before** opening the test set.
**Why:** Plan Phase 4 rules. The target must be fixed before we see any test number.
**How:**
- **Finalist rule** (written before seeing the table): best model; best of another family; best linear.
- Final fits:
  - MLP: every 10th training row (118,980 rows);
  - LightGBM: every 10th row, chosen by the thinning check;
  - Ridge: all 1,189,792 training rows.
- Saved `outputs/models/*.joblib` (git-ignored) and `model_metadata.json` (inputs, settings, versions, split).
- **Target rule:** test RMSE ≤ CV RMSE + 2 × CV std, rounded up to 0.1 °C; and ≤ half of B1's CV RMSE.
**Result:**
- **Thinning:** LightGBM CV 5.061 °C with every 10th row vs 5.146 °C with every 5th (+0.085 °C, within noise), at 5.8 vs 12.5 s per fold. So thinning costs nothing measurable.
- **Finalists: M6 MLP, M5 LightGBM, M3 Ridge.** Within 0.3 °C of the best: MLP, LightGBM, Ridge, Linear, Lasso.
- **OOF errors of the MLP:** mean −0.466 °C, **std σ = 4.959 °C**, 95th-percentile |error| 9.413 °C, range −47.67 to +76.31 °C. σ is used as the Phase 6 safety margin.
- **Fit times and sizes:** MLP 77.6 s, 0.1 MB; LightGBM 22.4 s, 1.5 MB; Ridge 2.9 s, 3 KB.
- **Success targets:** test RMSE of the MLP **≤ 6.5 °C** (4.919 + 2 × 0.763 = 6.445, rounded up) and **≤ 13.02 °C** (half of B1's 26.03).
**Nuances / gotchas:**
- **The simple-vs-best trade-off (plan rule: discuss if a simpler model is within 0.3 °C).**
  - Ridge is only 0.25 °C behind the MLP, has the *smallest* fold spread (± 0.58 vs ± 0.76), is 45 weights in a 3 KB file, and runs in microseconds on any controller.
  - The MLP's mean is the best, but it's more variable.
  - We kept the pre-written rule (MLP = final model) and carried Ridge as the deployable alternative.
- **Why not fit the final MLP and LightGBM on all rows?** CV showed no gain from more rows (5th vs 10th), and the hyperparameters were tuned at this density.
**Alternatives considered:**
- A "one-standard-error rule" (pick the simplest model within one CV std of the best). It would have chosen Ridge. We had not pre-registered it, so we didn't switch. Logged as a lesson for Phase 5.
**Viva angle:** Q: How did you choose the final model, and what target did you set? A: With a rule fixed in advance: lowest CV RMSE (the MLP, 4.92 °C), plus LightGBM and Ridge as finalists. Before testing we set the target: test RMSE ≤ 6.5 °C and ≤ half the coolant baseline (13.02 °C).

---

## 2026-10-10 09:23 | Phase 4 summary  (run by: Arnav, for owner D)
**Tags:** [RESULT]
**What we did:** Finished Phase 4: model development.

**1. Recap in simple words**
- Every model was judged with the same session-wise 5-fold CV on every 10th training row (118,980 rows, 63 sessions).
- Baselines: always-the-mean 29.09 °C, coolant + offset 26.03 °C.
- Our 45 features cut the linear model's error from 16.09 to 5.18 °C. That's the biggest single improvement.
- Tuned models: MLP 4.92, LightGBM 5.06, Ridge 5.17, Lasso 5.20, Random Forest 5.82 °C. The trees overfit the training sessions.
- Finalists MLP, LightGBM and Ridge were retrained and saved. Target set before testing: ≤ 6.5 °C.

**2. Acceptance checklist**
- [x] The CV table has at least 6 models (9: B0, B1, M1, M2, Ridge, Lasso, RF, LightGBM, MLP).
- [x] Tuning ranges, best parameters and times are logged (Phases 4.1, 4.2; `tuning_*.csv`).
- [x] A `[DECISION]` entry explains the finalists (Phase 4.3).
- [x] Concepts added: linear regression, Ridge/Lasso (regularisation), decision tree, Random Forest (bagging), gradient boosting, cross-validation, hyperparameter tuning, overfitting vs underfitting, bias–variance (plus baselines, MLP, out-of-fold predictions).

**3. What every teammate must be able to explain from this phase**
- GroupKFold by session, and why the same rows and folds are used for every model.
- Why every 10th row is enough (measured: +0.085 °C with every 5th).
- What each model does in one sentence, and why trees overfit here (training vs validation RMSE).
- The finalist rule, and the Ridge-vs-MLP trade-off.
- How the success target (≤ 6.5 °C) was set *before* the test.

**4. Key numbers**

| Quantity | Value | Source |
|---|---|---|
| CV rows / sessions / folds | 118,980 / 63 / 5 | `modelling_summary.json` |
| B0 / B1 CV RMSE | 29.088 / 26.033 °C | `cv_results.csv` |
| M1 → M2 (features) | 16.093 → 5.178 °C | same |
| MLP / LightGBM / Ridge CV RMSE | 4.919 / 5.061 / 5.172 °C | same |
| MLP OOF residual σ | 4.959 °C | `modelling_summary.json` |
| Success target | test RMSE ≤ 6.5 °C | same |

**Viva angle:** see the "Models" section of `VIVA_QA.md`.

---

## 2026-10-10 09:24 | Phase 5.1 | TEST SET OPENED (once) and overall + per-session results  (run by: Arnav, for owner E)
**Tags:** [RESULT] [NUANCE]
**What we did:** Ran `notebooks/05_evaluation.ipynb` **once**. **The test set was first opened at 2026-10-10 09:24:52** (printed in the notebook). The finalists and baselines predicted all 141,024 rows of the 6 test sessions at full 2 Hz.
**Why:** The final, honest exam on unseen sessions (plan rule 4: used once).
**How:** Loaded the saved finalists from `outputs/models/`. Refitted B0 and B1 on all training rows. `regression_metrics()` on all rows and per session. Saved `test_metrics.csv`, `test_metrics_per_profile.csv`, `test_predictions.csv` and `evaluation_summary.json`. Only markdown was added to the notebook afterwards; it was **not re-executed**.
**Result (overall):**

| Model | Test RMSE | MAE | R² | max abs | p95 abs | mean signed | session-mean MAE |
|---|---|---|---|---|---|---|---|
| M3 Ridge | **4.966** | 2.993 | 0.963 | 73.573 | 9.030 | +0.380 | 2.847 |
| M5 LightGBM | 5.105 | 2.860 | 0.961 | 74.873 | 9.877 | −0.873 | 2.380 |
| M6 MLP (final) | 6.005 | 3.693 | 0.946 | 60.312 | 14.597 | −1.946 | 2.991 |
| B1 | 24.484 | 20.147 | 0.106 | 72.000 | 50.917 | +2.404 | 19.543 |
| B0 | 25.941 | 22.225 | −0.004 | 63.495 | 45.961 | −1.626 | 23.078 |

- **MLP per session (RMSE / MAE / max / signed, °C):**
  - session 6: 9.430 / 7.635 / 21.873 / −6.599
  - session 7: 1.226 / 0.800 / 6.175 / +0.297
  - session 21: 5.988 / 3.318 / 60.312 / −1.252
  - session 61: 3.620 / 2.371 / 22.669 / −0.538
  - session 66: 3.708 / 2.194 / 34.226 / +0.122
  - session 81: 2.998 / 1.630 / 17.923 / +0.723
- **Success targets: both MET.** The MLP's 6.005 °C ≤ 6.5 °C, and ≤ 13.02 °C.
- **Figures:**
  - `eval_01_test_session_6.png` … `eval_06_test_session_81.png`: predicted vs actual over time, one per session.
  - `eval_07_residual_histogram.png`: errors centred slightly below 0 (mean −1.95 °C).
  - `eval_08_predicted_vs_actual.png`: points hug y = x, but fall below it at high temperatures.
  - `eval_12_cv_vs_test.png`: CV vs test for all models.
- **Accuracy in plain words (MLP):** 54.5 % of predictions within ±2 °C, 75.6 % within ±5 °C.
**Nuances / gotchas:**
- **The CV winner (MLP) came last among the finalists on the test set**: gap +1.086 °C, against LightGBM +0.044 and Ridge −0.205.
  - CV couldn't separate the top models: they were 0.28 °C apart against a fold std of 0.58–0.84 °C.
  - 6 test sessions is a small sample, and one hard session (6) dominates the MLP's score.
- **We did NOT switch the final model after seeing this.** Choosing on test results would turn the test set into a validation set. We report all finalists honestly instead.
- The **session-mean MAE** favours LightGBM (2.380) while the row-weighted RMSE favours Ridge (4.966). This is exactly why plan v2 asked for both: long sessions dominate row-weighted scores.
- The baselines score *better* on the test set than in CV (B0 25.94 vs 29.09). The test sessions' temperature spread is a bit narrower, which shows the test set isn't harder overall, just different.
- **Legend overlap** in `eval_12_cv_vs_test.png` (over the B0 bar) was not fixed, because that would mean re-running the test evaluation.
**Alternatives considered:** Re-running with a "better" final model. Rejected (see above). Logged as a lesson: pre-register a one-standard-error simplicity rule next time.
**Viva angle:** Q: Your best CV model did worst on the test set. Why, and did you switch? A: The top models were within 0.3 °C in CV, smaller than the fold noise, and one hard test session (6) hurt the MLP most. We didn't switch, because choosing after seeing test results is test-set leakage. Ridge (4.97 °C) and LightGBM (5.11 °C) were also finalists and are reported.

---

## 2026-10-10 09:26 | Phase 5.2 | Where the model fails: hot temperatures, one hard session, session starts  (run by: Arnav, for owner E)
**Tags:** [RESULT] [NUANCE] [IDEA]
**What we did:** Analysed the errors: by temperature band, over time since session start, and for under-prediction in the hot zone.
**Why:** Plan Phase 5 interpretation and N8: under-prediction is the dangerous direction.
**How:** `notebooks/05_evaluation.ipynb` sections 8, 9 and 12. "Hot" = actual ≥ **104.79 °C**, the training 90th percentile (from training data, never from test data).
**Result:**
- `eval_09_error_by_temperature.png` (MLP):
  - MAE ≤ 5.3 °C up to 90 °C;
  - **7.53 / 7.82 °C at 90–100 / 100–110 °C**, with mean signed error −6.22 / −6.64 °C, i.e. systematic under-prediction when hot.
- **Hot rows:** 14,496 (10.3 % of test rows).
  - MLP under-predicts by more than 5 °C in **52.0 %** of them (LightGBM 27.0 %).
  - Mean signed error on hot rows: MLP −6.48, LightGBM −2.62 °C.
  - Largest under-prediction: MLP −22.03 °C (session 66, minute 21.3, actual 86.99 °C); LightGBM −33.26 °C (session 6, minute 263.4).
- `eval_01_test_session_6.png`: while the coolant was raised to about 50–65 °C under load, the MLP stayed 10–18 °C too low for over an hour. Session RMSE 9.43 °C.
- `eval_10_error_vs_session_time.png`: mean |error| is highest in the **first 5-minute window** (Phase 6 gives the exact number from the saved predictions). It drops below 2 °C by about 45 minutes, and later bumps come from the few long sessions.
- `eval_03_test_session_21.png`: **the biggest error, +60.31 °C at minute 0.** A cold motor (about 20 °C) starts under heavy load, and both models predict 80–95 °C.
**Nuances / gotchas:**
- **The session-start error is an artefact of how the EWMA starts.** With `ewm(adjust=True)`, the first value equals the current reading, so a session that starts under heavy load "looks" like it has been at that load for a long time, and the model predicts a hot winding. The reverse happens for sessions that start already hot (16 of 63 training sessions start above 30 °C). A real controller would keep its EWMAs running from power-on, so this is mostly caused by cutting the recordings into sessions.
- **The Phase 4 hypothesis is only partly confirmed.** The very first minutes are bad, but averaged over the first 45 minutes the MAE (3.665 °C) equals that after (3.701 °C).
- **Under-prediction when hot is the most important limitation for safety.** The Phase 6 alarm adds a margin to handle it.
**Alternatives considered:** Excluding the first minutes from the score. Rejected: that hides a real limitation. We report it instead.
**Viva angle:** Q: Where does your model fail? A: (1) In the first minutes of a session, because the memory features start "full", so a cold motor under sudden load looks hot (up to +60 °C). (2) When hot (> 90 °C), where it under-predicts by about 6 °C on average. (3) Session 6, with high coolant under load.

---

## 2026-10-10 09:27 | Phase 5.3 | Permutation importance and the physics check (N7)  (run by: Arnav, for owner E)
**Tags:** [RESULT] [NUANCE]
**What we did:** Computed permutation importance of the final MLP, for single features and for physically grouped feature families.
**Why:** To check that the model relies on physically sensible inputs (plan N7).
**How:** `sklearn.inspection.permutation_importance(scoring="neg_root_mean_squared_error", n_repeats=3, random_state=42)` on every 10th test row (14,103 rows; baseline RMSE on this sample 6.02 °C). Then a manual grouped version: whole families are shuffled jointly. This is interpretation only, after the single evaluation.
**Result** (`eval_11_permutation_importance.png`, `permutation_importance.csv`, `permutation_importance_grouped.csv`). RMSE increase when a family is shuffled:
- **coolant 19.67 °C**
- voltage 16.11
- speed 15.40
- current 11.32
- power 8.96
- torque 2.45
- ambient 0.52

The top single features are `coolant_ewma_600`, `i_s_sq`, `motor_speed_ewma_600`, `u_d` and `i_s_sq_ewma_600`.
**Nuances / gotchas:**
- **The ranking matches physics:**
  - coolant sets the floor the winding cools towards;
  - current² (I²R) is the heat source;
  - speed and voltage describe the operating point (iron losses grow with frequency, and voltage ∝ speed);
  - torque adds little because it's almost a copy of i_q (r = 0.9965);
  - ambient matters least because it varies little (8.78–30.71 °C, mostly 20–28 °C).
- **Correlated features share importance.** Shuffling one EWMA hurts less because its siblings still carry the information. That's why the grouped view is the honest one.
- **Shuffling creates impossible combinations** (e.g. high current with zero voltage), so importances for a flexible model like an MLP can be inflated. Read them as a ranking, not exact values.
**Alternatives considered:** SHAP values (optional in the plan). Skipped: not installed, and the grouped permutation already answers the physics question.
**Viva angle:** Q: Which inputs matter most, and does it make physical sense? A: Coolant, then voltage and speed, then current. Coolant sets the base temperature, current² makes the copper loss, and speed/voltage reflect iron losses and the operating point. Torque matters little because it's nearly a copy of i_q.

---

## 2026-10-10 09:28 | Phase 5 summary  (run by: Arnav, for owner E)
**Tags:** [RESULT]
**What we did:** Finished Phase 5: the final evaluation, test set used once (opened 2026-10-10 09:24:52).

**1. Recap in simple words**
- On 6 unseen sessions the final MLP reached RMSE 6.01 °C (MAE 3.69, R² 0.946). Both pre-set targets were met.
- The other finalists did better on the test set (Ridge 4.97, LightGBM 5.11 °C). CV couldn't separate them, and we did not switch models after seeing the test.
- The worst errors happen at session starts (the EWMA starts "full") and when the motor is hot (> 90 °C), where the MLP under-predicts by about 6 °C.
- The importance ranking (coolant > voltage ≈ speed > current > power > torque > ambient) matches the physics.
- Every number is in `evaluation_summary.json` and the CSVs; the predictions are saved for Phase 6 and the demo.

**2. Acceptance checklist**
- [x] The test set is evaluated once, with the time logged (2026-10-10 09:24:52).
- [x] The results CSVs are saved (`test_metrics.csv`, `test_metrics_per_profile.csv`, `test_predictions.csv`).
- [x] At least 6 figures are saved and logged (12: `eval_01` … `eval_12`).
- [x] The interpretation is written (notebook section 15 + Phases 5.1–5.3).
- [x] Concepts added: MSE, RMSE, MAE, R², residuals, permutation importance, generalisation gap (plus p95 and signed error, session-mean MAE).

**3. What every teammate must be able to explain from this phase**
- RMSE vs MAE vs R², and what our 6.01 / 3.69 / 0.946 mean in plain words.
- Why the CV winner lost on the test set, and why we did not switch (test-set leakage).
- The two failure modes (session starts; under-prediction when hot) and their causes.
- The importance ranking and its physics.
- The success targets and how they were set before testing.

**4. Key numbers**

| Quantity | Value | Source |
|---|---|---|
| Test opened | 2026-10-10 09:24:52 | `evaluation_summary.json` |
| Final MLP test RMSE / MAE / R² | 6.005 / 3.693 / 0.946 | `test_metrics.csv` |
| Ridge / LightGBM test RMSE | 4.966 / 5.105 °C | same |
| B1 / B0 test RMSE | 24.484 / 25.941 °C | same |
| CV → test gap (MLP) | +1.086 °C | `evaluation_summary.json` |
| Hot rows under-predicted > 5 °C | MLP 52.0 %, LightGBM 27.0 % | same |
| Within ±2 / ±5 °C (MLP) | 54.5 % / 75.6 % | same |

**Viva angle:** see the "Evaluation" section of `VIVA_QA.md`.

---

## 2026-10-10 09:15 | Phase 7.1 | Flow diagram (required by the instructions)  (run by: Arnav, coordinator A)
**Tags:** [SETUP] [RESULT]
**What we did:** Wrote `docs/flow_diagram.md` (Mermaid) and exported `docs/flow_diagram.png` (3136 × 1132 px).
**Why:** The MST instructions require a flow diagram with the pre-processing and visualisation steps clearly documented.
**How:**
- Four columns: 1 DATA → 2 VISUALISATION & PRE-PROCESSING → 3 MODELLING → 4 EVALUATION & INNOVATION.
- Every box names its notebook and key numbers (e.g. "test = 6, 7, 21, 61, 66, 81 (10.60 %)", "8 thermal lag", "45 inputs").
- Exported with `npx -y @mermaid-js/mermaid-cli -i docs/flow_diagram.md -o docs/flow_diagram.png -b white -s 4` (mermaid-cli 12.0.0).
**Result:** `docs/flow_diagram.png`, readable on one slide.
**Nuances / gotchas:**
- **[BUG] `-w 1400` (width) is not an option in mermaid-cli 12** ("error: unknown option '-w'"). Fix: drop it and use `-s 4` (scale) for resolution.
- The first `npx` run took 429 s, mostly downloading the package and its headless browser.
- The first layout (one long column) was 1236 × 7328 px, unreadable on a slide. Re-done as four Mermaid subgraphs with `direction TB` inside, linked subgraph-to-subgraph so the inner direction is respected.
- mermaid-cli writes `flow_diagram-1.png` for Markdown input; it is renamed to `flow_diagram.png`.
**Alternatives considered:** draw.io (manual, harder to keep in sync with the numbers); matplotlib boxes (more code).
**Viva angle:** Q: Walk us through your workflow. A: Data check → freeze test sessions → EDA on training sessions (8 plots) → no cleaning needed → physics + EWMA features → scaling in a Pipeline → 9 models with session-wise CV → finalists → one test evaluation → interpretation → innovation (ablation, memory curve, safety alarm, data efficiency, demo).

---

## 2026-10-10 09:30 | Phase 6.5 | I5: Streamlit recorded-data replay demo (app.py)  (run by: Arnav, for owner E)
**Tags:** [SETUP] [RESULT] [NUANCE]
**What we did:** Built and tested `app.py`, a Streamlit app that replays a test session minute by minute.
- It shows the estimated vs actual winding temperature, the coolant, the "estimate + k·σ" margin line and the alarm threshold.
- A green/red alarm lamp, plus the measured Phase 5 test metrics.
**Why:** Plan v2 makes the demo a core deliverable. A live replay explains the virtual sensor far better in the viva than a table.
**How:**
- Run `streamlit run app.py`.
- **Live mode:** loads only the chosen session's rows from `data/processed/features.parquet` (pyarrow `filters`), loads the selected finalist (`outputs/models/*.joblib`) and predicts.
- **Fallback mode:** if those git-ignored files are missing, it replays `outputs/results/test_predictions.csv` (saved once in Phase 5).
- Sidebar: test session, model, alarm threshold (default 104.79 °C = training 90th percentile), margin k ∈ {0, 1, 2} with σ = 4.959 °C (OOF std from Phase 4), and replay speed.
- Tested with `python -m streamlit run app.py --server.headless true --server.port 8501`.
**Result:**
- The app starts with no console errors and shows "Mode: live model: M6 MLP (64-32)".
- **Session 6 at minute 30:** estimate 71.5 °C vs actual 72.1 °C (error −0.6 °C).
- **Play:** advances 5 min of data per frame (minute 60 → 160 in about 9 s).
- The results line reads RMSE 6.00 °C, MAE 3.69 °C and R² 0.946, matching `evaluation_summary.json`.
**Nuances / gotchas:**
- **It's a recorded replay, not live hardware.** That's labelled at the top of the app. The measured temperature is only drawn for comparison and is never an input.
- **The app never retrains.** It loads the saved pipeline and builds features with the same `src/features.py`.
- **Small UX quirk:** after "Play to the end", the position slider jumps back to its previous value on the next interaction (Streamlit widget state). Harmless.
- **The model files are git-ignored.** Teammates must run notebooks 01, 03 and 04 to get live mode, or use the fallback.
- Added `streamlit==1.65.0` to `requirements.txt` (install took 168 s); `pip_freeze.txt` refreshed (131 packages).
**Alternatives considered:**
- Gradio: not in the plan.
- A Jupyter widget: less presentable.
- Hosting on Streamlit Community Cloud: possible later, but the model and features would have to be included there.
**Viva angle:** Q: What does your demo show, and is it real-time? A: It replays a recorded, held-out test session through the saved model, showing the estimate, the real sensor value and an alarm lamp with a safety margin. It runs live on recorded data; no physical motor is connected.

---

## 2026-10-11 09:55 | Phase 6.0 | Session restart: the Phase 6 notebook run was cut off and is being re-run  (run by: Arnav)
**Tags:** [BUG] [SETUP]
**What we did:** Found that the previous session ended while `notebooks/06_innovation.ipynb` was still executing. The notebook was re-run from the top.
**Why:** The team rules require every notebook to run top to bottom with its outputs saved inside the file. A half-finished run leaves the notebook without outputs.
**How:**
- Checked the files. `ablation.csv` and `innov_01_ablation.png` were written at 2026-10-10 09:58, but no memory-curve, safety or data-efficiency files existed, and `06_innovation.ipynb` still had no outputs.
- Kept a copy of the partial `ablation.csv` to compare with the re-run.
- Added a small cache to `cv_rmse()`: identical input lists are cross-validated once, because the memory curve's "no memory" and "full" steps equal the ablation's "no EWMA" and "full" variants.
- Re-ran with `jupyter nbconvert --execute --inplace`.
**Result:** see Phase 6.1–6.4. The partial ablation from the first run already showed:
- full 4.919 °C;
- no EWMA 13.176 °C;
- no engineered 6.561 °C;
- no torque 4.809 °C;
- raw only 13.407 °C;
- with leakage 1.146 °C.
**Nuances / gotchas:**
- **[BUG] Symptom:** "background command didn't finish before the previous session ended". **Cause:** the long run was attached to the old terminal session. **Fix:** re-run, and check `git status` and the result-file timestamps at the start of every session.
- The first run took about 32 min for the ablation alone (MLP fits were slow while other jobs shared the CPU).
- `git status`: only commit "v1" exists remotely, and no teammate pushes have arrived. All of Phases 3–7 is still local and uncommitted.
**Alternatives considered:** Keeping the partial CSV and writing the rest by hand. Rejected: the notebook must reproduce every number itself.
**Viva angle:** —

---

## 2026-10-11 22:12 | Phase 6.0b | Second interruption of the Phase 6 run; teammate commit on GitHub  (run by: Arnav)
**Tags:** [BUG] [NUANCE] [SETUP]
**What we did:**
- Found that the second Phase 6 run (started 09:58) also stopped after the ablation (files written 10:37) when the terminal session ended. It was re-run a third time while the session stays open.
- Found two new commits on GitHub from teammate **Abhilasha** (`abhilashadas2406-eng`).
**Why:** The notebook must finish top to bottom, and the remote changes must not be silently overwritten.
**How:**
- `git fetch` → `origin/main` moved from `661d0d6` (v1) to `7ba8d3b`.
- `git show --stat` on `7ec5125` and `7ba8d3b`: both are "Update PLAN.md" web edits changing **one line**, the Phase 3 checklist line, to "[x] Phase 3 … (done 11-10-26 by Abhilasha)". No notebooks or code came with them.
- **Timing check:** one MLP fit (95,000 rows, 45 features, 40 epochs) now takes **13.8 s**, against about 75 s per fit during the earlier runs.
**Result:**
- The re-run's ablation was identical to the first run, row by row: deterministic, as expected.
- **The remote change is NOT merged yet.** Our local `PLAN.md` also changes that same line, so `git pull` will need a one-line merge. Arnav decides how to record Phase 3 ownership.
**Nuances / gotchas:**
- **[BUG] Long jobs die with the session.** A background command is killed when the session that started it ends. **Fix:** keep the session open until long runs finish, and check result-file timestamps at every session start.
- **Why the earlier runs were slow (best guess, not proven):** the laptop throttled while other jobs shared the CPU (power plan "Balanced").
- **Team coordination:** two people may have worked on Phase 3. If Abhilasha (owner C?) has her own Phase 3 notebook, it must be compared with `notebooks/03_preprocessing_features.ipynb` before anyone overwrites anything.
**Alternatives considered:**
- Pulling and resolving the conflict automatically. Not done: it edits the team's shared record of who did what, so it's Arnav's decision.
- Detaching the job via Task Scheduler. Not done: it changes system configuration.
**Viva angle:** —

---

## 2026-10-11 23:12 | Phase 6.1 | I1: ablation study, what each idea is worth  (run by: Arnav, for owner D)
**Tags:** [RESULT] [NUANCE]
**What we did:** Re-ran cross-validation of the **final model (M6 MLP)** six times, changing only the input set each time.
**Why:** To prove with numbers that each idea helps, and to show *why* the forbidden temperatures are forbidden (plan I1).
**How:**
- `notebooks/06_innovation.ipynb` section 2, `cv_rmse(cols)`: the same MLP settings, the same 118,980 rows (every 10th training row) and the same GroupKFold(5).
- The feature sets come from `src/features.py → feature_sets()`.
- Identical input lists are cached in memory, so the memory-curve endpoints aren't recomputed.
**Result** (`outputs/results/ablation.csv`, `innov_01_ablation.png`):

| Variant | Features | CV RMSE (°C) | vs full |
|---|---|---|---|
| full | 45 | 4.919 ± 0.763 | — |
| no EWMA | 13 | 13.176 ± 1.367 | **+8.257** |
| no engineered (no physics) | 24 | 6.561 ± 0.617 | +1.642 |
| no torque | 39 | 4.809 ± 1.033 | −0.110 |
| raw only | 8 | 13.407 ± 1.379 | +8.488 |
| with leakage (forbidden) | 48 | **1.146 ± 0.112** | −3.774 |

**Nuances / gotchas:**
- **The EWMA memory is the single most valuable idea, worth about 8.3 °C.** Without it the MLP is about as bad as with raw inputs only (13.18 vs 13.41).
- **The leakage variant (1.15 °C) is the proof that those columns are a cheat**: almost perfect, because the model copies the neighbouring sensors. This was the planned "show the cheat" experiment. These columns are never used anywhere else.
- **Dropping torque doesn't hurt** (−0.11 °C, inside the ± 1.03 fold spread), consistent with torque ≈ i_q (r = 0.9965). A deployable model could skip torque.
- **Reproducibility check:** this ablation was computed four times (2026-10-10 09:58, 2026-10-11 10:37, 22:24 and 23:12) with identical numbers to 15 digits (fixed seeds).
**Alternatives considered:** Ablating with LightGBM instead. The plan says "the final model", so we used the MLP.
**Viva angle:** Q: How do you know your memory features matter? A: Ablation: the same MLP on the same folds goes from 4.92 °C to 13.18 °C RMSE when the EWMA features are removed.

---

## 2026-10-11 23:29 | Phase 6.2 | I2: the thermal-memory curve  (run by: Arnav, for owner C)
**Tags:** [RESULT]
**What we did:** Starting from raw + physics features (no memory), we added the EWMA spans one by one (1 → 5 → 15 → 45 min) and cross-validated the MLP each time.
**Why:** To tell the "thermal memory" story with numbers: how much memory the model needs.
**How:** `notebooks/06_innovation.ipynb` section 3, the same CV as I1.
**Result** (`outputs/results/memory_curve.csv`, `innov_02_memory_curve.png`). CV RMSE:
- no memory: **13.176**
- + 1 min: **9.171**
- + 5 min: **5.158**
- + 15 min: **4.996**
- + 45 min: **4.919 °C**
**Nuances / gotchas:**
- **Most of the gain arrives by 5 minutes of memory** (13.18 → 5.16 °C). That matches the Phase 2 lag analysis (median best lag 2.5 min).
- The 15 and 45-min spans add only 0.24 °C more. They capture the slow "background heat", but they are also the spans hit hardest by the session-start warm-up artefact.
**Alternatives considered:** Testing each span alone. Cumulative steps are easier to explain and answer "how much memory is enough?".
**Viva angle:** Q: How long a memory does the model need? A: About 5 minutes gets most of the gain: the CV RMSE falls from 13.18 °C (none) to 5.16 °C (1 + 5 min), and the 15 and 45-min spans add only 0.24 °C more.

---

## 2026-10-11 23:30 | Phase 6.3 | I3: safety-aware alarm, session-start errors, and a rounding bug  (run by: Arnav, for owner E)
**Tags:** [RESULT] [BUG] [NUANCE] [DECISION]
**What we did:**
- Built the safety alarm "estimate + k·σ ≥ T_hot" on the **saved Phase 5 predictions** (no new test evaluation), for k = 0, 1, 2.
- Measured how much of the error sits in the first 5 minutes of each test session.
**Why:** Plan N8 and I3. Under-prediction when hot is the dangerous error, and Phase 5 showed the MLP under-reads by about 6 °C above 90 °C.
**How:**
- σ = **4.959 °C**, the std of the MLP's *out-of-fold* errors on the training sessions (Phase 4), so the margin never saw the test set.
- T_hot = **104.791 °C**, the training 90th percentile, the same "hot" as Phase 5.
- Recall = TP/(TP+FN); false-alarm rate = FP/(FP+TN); precision = TP/(TP+FP). Rows are converted to minutes at 120 rows/min.
**Result** (`outputs/results/safety_alarm.csv`, `session_start_errors.csv`, `innov_03_safety_alarm.png`):

| k | Margin | Hot rows caught | Missed hot minutes | False alarms | False-alarm minutes | Precision |
|---|---|---|---|---|---|---|
| 0 | 0.00 °C | 57.2 % | 51.7 | 0.70 % | 7.4 | 90.4 % |
| 1 | 4.96 °C | 66.4 % | 40.6 | 2.30 % | 24.3 | 76.8 % |
| 2 | 9.92 °C | **70.0 %** | 36.2 | 5.84 % | 61.6 | 57.9 % |

- 14,496 hot test rows, the same count as Phase 5 (asserted in code).
- `innov_03_safety_alarm.png`: test session 61 (the hottest) with the 2σ margin line and the alarm periods shaded, plus caught vs false-alarm bars.
- **Session starts** (first 5 min = 2.55 % of test rows):

  | Prediction | MAE first 5 min | MAE after | Signed first 5 min |
  |---|---|---|---|
  | MLP | 12.34 °C | 3.47 °C | +12.04 °C |
  | LightGBM | 12.52 | 2.61 | |
  | Ridge | 18.64 | 2.58 | |

**Nuances / gotchas:**
- **[BUG] Symptom:** the first Phase 6 run counted **14,765** hot rows, against **14,496** in Phase 5.
  - **Cause:** `test_predictions.csv` rounds temperatures to 3 decimals. Test session 21 plateaus at about 104.79 °C, which is almost exactly T_hot (the training 90th percentile; the bench evidently holds the motor near that temperature often). Rounding pushed 269 plateau rows over the threshold.
  - **Fix:** section 4 reads the full-precision temperatures from `features.parquet` (same rows, same order, checked with `np.allclose`) and **asserts** the Phase 5 count.
  - The rounded version had shifted "caught" and "false alarms" by under 0.3 points, but precision by up to 1.7 points (92.06 vs 90.36 % at k = 0). The old file was kept in the scratchpad only.
- **The safety margin is a trade-off, not a cure.** Going from k = 0 to k = 2 catches 12.8 points more hot rows (57.2 → 70.0 %) but multiplies false alarms 8× (0.70 → 5.84 %). **Even k = 2 misses 30 % of hot rows**, because the MLP under-reads when hot. A real protection system would need a better model in that zone, or an extra margin there.
- Some "missed" hot rows sit within a few hundredths of a degree of the threshold (the session 21 plateau), so a row-level count is a strict measure.
- **Session starts dominate the residual error.** The positive signed error (+12.04 °C) confirms over-prediction, caused by the EWMA starting at the current value. Ridge suffers most there (18.64 °C), yet is still best overall, because the starts are only 2.55 % of rows.
- **Re-runs:** this notebook had to be run four times in total: two interrupted sessions, then this bug fix. The final run took 3,463 s on battery power.
**Alternatives considered:**
- Choosing T_hot from the test data. Rejected: it must come from training data.
- An event-level metric (alarm within N minutes of an overheating episode): fairer for engineers, but more complex. Logged as an `[IDEA]`.
**Viva angle:** Q: How does your safety alarm work, and what does it cost? A: Alarm if the estimate + k·σ reaches 104.79 °C, with σ = 4.96 °C from training-session errors. With k = 2 it catches 70.0 % of hot moments (57.2 % without a margin) at 5.84 % false alarms. Even then 30 % are missed, which we state as a limitation.

---

## 2026-10-11 23:36 | Phase 6.4 | I4: data-efficiency curve  (run by: Arnav, for owner D)
**Tags:** [RESULT] [IDEA]
**What we did:** Held out 20 % of the training sessions as validation, then trained the MLP on 25, 50, 75 and 100 % of the remaining development sessions.
**Why:** To estimate how much test-bench data a new motor would need (plan I4).
**How:**
- `GroupShuffleSplit(test_size=0.2, random_state=42)` on the 63 training sessions: 50 development, 13 validation. The test set is not involved.
- The 25–75 % fractions were repeated 3 times with random session picks (`rng` seed 42) and averaged.
**Result** (`outputs/results/data_efficiency.csv`, `innov_04_data_efficiency.png`). Mean validation RMSE:
- 25 % (12 sessions): **9.56 °C** (runs 10.43 / 7.98 / 10.25)
- 50 % (25): **6.36 °C**
- 75 % (38): **5.18 °C**
- 100 % (50): **4.66 °C**
**Nuances / gotchas:**
- **The curve is still falling at 100 %**, so more recorded sessions would still improve the model. That's an honest "future work" point.
- **With few sessions the result swings a lot** (7.98 to 10.43 °C at 25 %), depending on *which* sessions were picked. That's why the repeats are needed.
- This validation RMSE (4.66 °C) is not comparable one-to-one with the 5-fold CV (4.92 °C): it is a different, single split.
**Alternatives considered:** Using the test set for this curve, as the plan's wording suggested ("test RMSE"). Rejected: it would re-use the test set four times.
**Viva angle:** Q: Would more data help? A: Yes. Validation error fell from 9.56 °C (12 sessions) to 4.66 °C (50 sessions) and was still falling, so recording more sessions is worthwhile.

---

## 2026-10-11 23:38 | Phase 6 summary  (run by: Arnav, for owners C, D, E)
**Tags:** [RESULT]
**What we did:** Finished Phase 6: innovation extras I1–I5.

**1. Recap in simple words**
- **Ablation:** the memory features are worth about 8.3 °C (4.92 → 13.18 °C without them). Torque can be dropped, and the forbidden sensors would make it a trivial cheat (1.15 °C).
- **Memory curve:** about 5 minutes of memory gives most of the gain (13.18 → 5.16 °C).
- **Safety alarm:** a 2σ margin catches 70.0 % of overheating moments (57.2 % without) at 5.84 % false alarms. Session starts are the biggest remaining error (12.34 °C in the first 5 min).
- **Data efficiency:** the error is still falling with more sessions (9.56 → 4.66 °C), so more data would help.
- **Demo:** a Streamlit replay app (`app.py`) shows all of this live for the viva.

**2. Acceptance checklist**
- [x] At least 3 innovation items done, each with a results file, a figure and a `LOG.md` entry: I1, I2, I3, I4 (+ I5 app). `ablation.csv`, `memory_curve.csv`, `safety_alarm.csv`, `data_efficiency.csv`; `innov_01` … `innov_04`.
- [x] Each is explainable in 2 lines in `VIVA_QA.md` (Innovation section).

**3. What every teammate must be able to explain from this phase**
- What an ablation is, and why only one thing changes at a time.
- Why the 1.15 °C "with leakage" result proves those columns are forbidden.
- The safety margin trade-off (caught vs false alarms vs precision), and why σ comes from out-of-fold errors.
- Why session starts are hard (EWMA warm-up), and why more data would still help.
- How the demo works, and that it's a recorded replay.

**4. Key numbers**

| Quantity | Value | Source |
|---|---|---|
| CV RMSE full / no EWMA / with leakage | 4.919 / 13.176 / 1.146 °C | `ablation.csv` |
| Memory: none → 1 → 5 → 15 → 45 min | 13.18 → 9.17 → 5.16 → 5.00 → 4.92 °C | `memory_curve.csv` |
| Alarm caught / false alarms (k = 0 / 2) | 57.2 / 70.0 % and 0.70 / 5.84 % | `safety_alarm.csv` |
| MLP MAE, first 5 min vs after | 12.34 vs 3.47 °C | `session_start_errors.csv` |
| Data efficiency, 12 → 50 sessions | 9.56 → 4.66 °C | `data_efficiency.csv` |

**Viva angle:** see the "Innovation" section of `VIVA_QA.md`.

---

## 2026-10-11 23:40 | Phase 7.2 | Slides (12), report, one-file notebook; every slide number cross-checked by code  (run by: Arnav, coordinator A)
**Tags:** [RESULT] [BUG] [SETUP]
**What we did:**
- Built the 12-slide deck "Motor Winding Virtual Sensor" (published online, private until shared; ask Arnav for the link) with speaker notes.
- Wrote `docs/report/report.md` in rubric order.
- Created and ran `notebooks/MST_final.ipynb` (one-file summary).
- Checked every key slide number against the results files with code.
**Why:** Phase 7 deliverables. Plan rule: "every number in the slides matches the results files".
**How:**
- **Slides, in plan order:** cover → problem → data → flow diagram → EDA → features → models/CV → test results → failure modes → ablation + memory → safety + data efficiency + demo → limits/lessons/team. The figures (`docs/flow_diagram.png`, `eda_08`, `feat_01`, `eval_05`, `eval_03`, `eval_09`, `innov_01`–`innov_04`) were uploaded as deck assets.
- **`MST_final.ipynb`:** reads every number from `outputs/results/` and shows the key figures. Section 7 rebuilds one session's features **from the raw parquet** with `src/features.py`, loads the saved MLP and predicts.
- **Cross-check script:** extracts the slide text and compares 56 formatted values (data facts, EDA, CV table, test table, ablation, safety, data efficiency) with the CSV/JSON files. Saved to `outputs/results/slides_number_check.json`.
**Result:**
- `MST_final.ipynb`: 18 cells, 0 errors, 27 s. End-to-end check: test session 6 **RMSE 9.4301 °C now = 9.4301 °C saved in Phase 5**, so the saved pipeline reproduces exactly.
- Cross-check: **56 numbers, 0 mismatches** (after the fix below).
**Nuances / gotchas:**
- **[BUG] Double rounding.** The first cross-check found 3 mismatches:
  - The MLP's test RMSE is **6.0048 °C**. We had rounded the 3-decimal display "6.005" up to "6.01", but the correct 2-decimal value is **6.00**.
  - Linear-45's CV std is 0.5645, so **± 0.56**, not 0.57.
  - B0's test MAE is 22.2248, so **22.22**, not 22.23.
  - **Fix:** corrected the slides, `docs/report/report.md`, `README.md` and `VIVA_QA.md`. Earlier `LOG.md` entries that say "6.01 °C" (Phase 5 summary recap and "what to explain") should be read as **6.00 °C**; the log is append-only, so they are corrected here instead. Their 3-decimal tables ("6.005") were right.
  - **Lesson:** always round from the raw value, never from an already-rounded display.
- **The end-to-end check re-predicts one test session** (session 6). That re-uses the test set for a reproducibility check only. It gives the identical number, and no decision depends on it.
- The deck is an online slide deck; it can be presented in the browser and exported as PPTX/PDF.
**Alternatives considered:** Building slides by hand in PowerPoint. Slower, and harder to keep in sync with the numbers.
**Viva angle:** Q: How do you know the numbers in your slides are right? A: A script compared 56 slide numbers with the result files (0 mismatches). The summary notebook also rebuilds a test session from raw data and reproduces its Phase 5 RMSE exactly (9.4301 °C).

---

## 2026-10-11 23:43 | Phase 7 summary + FINAL PROJECT SUMMARY  (run by: Arnav, coordinator A)
**Tags:** [RESULT]
**What we did:** Finished all deliverables except each member's mock viva, which every teammate must still do themselves.

**1. Recap in simple words**
- We built a **virtual sensor**: a model that estimates the copper winding temperature of a 50 kW PMSM from signals its controller already measures.
- Physics features and especially **EWMA "thermal memory"** features made the difference: the linear-model error fell from 16.09 to 5.18 °C, and removing the memory costs about 8.3 °C.
- With the test set used once, the finalists reached **RMSE 4.97 (Ridge), 5.11 (LightGBM) and 6.00 °C (MLP, our pre-registered final)**, against 24.48 °C for "coolant + offset". Both targets were met.
- The weak spots are the first minutes of a session (the EWMA warm-up) and hot periods, where the MLP under-reads. A 2σ safety margin catches 70.0 % of hot moments.
- Everything is logged and reproducible: notebooks 01–06 + `MST_final`, a flow diagram, a report, 12 slides, a Streamlit demo, 95 viva Q&As and 40 concepts.

**2. Phase 7 acceptance checklist**
- [x] The flow diagram PNG exists (`docs/flow_diagram.png`).
- [x] The notebooks run top to bottom (01–06 and `MST_final`, each executed with outputs saved; 04, 05 and 06 got findings cells added afterwards without re-execution).
- [x] The slides (12) and report (`docs/report/report.md`) are done.
- [x] Every number in the slides matches the results files (`slides_number_check.json`: 56 checked, 0 mismatches).
- [ ] **Every teammate has done a mock viva. Still to do, by each member:** pair up and quiz each other with 10 random questions from `VIVA_QA.md`, one at a time, grading against the A: lines.

**3. What every teammate must be able to explain (the whole project in 5 points)**
- The problem and why a virtual sensor, plus why `pm`/`stator_tooth`/`stator_yoke` are forbidden (the ablation's 1.15 °C cheat).
- Why we split by whole sessions and froze the test set first (rows are near-copies; fair exam).
- What EWMA features are and why they matter (2.5-min lag; 8.3 °C ablation gain; 5 min of memory gives most of it).
- How models were compared (GroupKFold by session, same rows and folds) and why the CV winner lost on test (differences below fold noise; we didn't switch).
- The limits: session starts, hot under-prediction, one motor, ≤ 141.36 °C, and how the safety margin trades misses for false alarms.

**4. Final numbers (cross-checked against `outputs/results/`)**

| Quantity | Value | File |
|---|---|---|
| Data | 1,330,816 rows · 69 sessions · 184.84 h · 2 Hz | `data_check_summary.json` |
| Test sessions (used once, 2026-10-10 09:24:52) | 6, 7, 21, 61, 66, 81 (10.60 % of rows) | `split_profiles.json` |
| Inputs | 45 (8 raw + 5 physics + 32 EWMA) | `feature_list.json` |
| CV RMSE: MLP / LightGBM / Ridge | 4.919 / 5.061 / 5.172 °C | `cv_results.csv` |
| CV RMSE: Linear raw → 45 features | 16.093 → 5.178 °C | same |
| **Test RMSE: Ridge / LightGBM / MLP (final)** | **4.966 / 5.105 / 6.005 °C** | `test_metrics.csv` |
| Test MAE / R² (MLP) | 3.693 °C / 0.946 | same |
| Test RMSE: B1 coolant + offset / B0 mean | 24.484 / 25.941 °C | same |
| Ablation: full / no EWMA / with leakage | 4.919 / 13.176 / 1.146 °C | `ablation.csv` |
| Safety k = 2: caught / false alarms | 70.0 % / 5.84 % | `safety_alarm.csv` |
| Session start: MLP MAE first 5 min vs after | 12.34 vs 3.47 °C | `session_start_errors.csv` |
| Data efficiency 12 → 50 sessions | 9.56 → 4.66 °C | `data_efficiency.csv` |

**Viva angle:** the whole `VIVA_QA.md` (95 Q&As).

---

## 2026-10-11 23:45 | Handover  (run by: Arnav)
**Tags:** —
**Where we stopped:** Phases 0–6 are complete and Phase 7 is complete except the mock vivas. **Nothing from 2026-10-10 / 11 is committed or pushed yet.**
**What's next (exact next steps):**
1. **Merge Abhilasha's GitHub edit before pushing.** `origin/main` has 2 commits that change only the Phase 3 checklist line in `PLAN.md` ("done 11-10-26 by Abhilasha"). Our local `PLAN.md` changes the same line.
   - Commit locally, then `git pull`, and resolve that one line.
   - Decide with Abhilasha how Phase 3 is credited (and whether she has her own Phase 3 notebook to compare).
   - Then push.
2. **Every member:** pull, read `LOG.md` top to bottom, then do the mock viva (see above). Owners B–E: review "your" phase's notebook and log entries, since Arnav ran them on your behalf.
3. **Fill in the team names (B–E)** in `PLAN.md`, `docs/report/report.md`, the cover and closing slides, and the tracker.
4. **Share** the deck, the tracker and the EDA showcase with teammates (each page's Share menu; Editors for the tracker).
**Open issues / questions:**
- Phase 3 ownership/credit (Abhilasha's commit).
- The deadline is still not recorded.
- `misc.txt` (YouTube link) is still unexplained.
- Optional polish: the legend overlap in `model_01` and `eval_12` (cosmetic; fixing them means re-running notebooks 04/05, and 05 must not be re-run).
**Before you start, you must know:**
- **Long notebook runs die if the terminal session closes,** and the laptop is about 2× slower on battery. Plug in, and keep the session open for notebooks 04 (23 min) and 06 (26 min plugged in).
- **Never re-run notebook 05** (the test evaluation) to "improve" anything. It was used once, by design.
- To run the demo: `streamlit run app.py`. Live mode needs the git-ignored `features.parquet` and models (run notebooks 01, 03, 04); otherwise it replays the saved predictions.

---

## 2026-10-14 16:05 | Phase 7.3 | Git conflict markers were pushed in PLAN.md; fixed  (run by: Arnav)
**Tags:** [BUG]
**What we did:** Found and removed git conflict markers in the `PLAN.md` phase checklist. They came in with commit `c78c2a0` ("update", 2026-10-12), which is already on GitHub.
**Why:** The checklist showed both the old and the new version of the phase lines, between `<<<<<<< Updated upstream` and `>>>>>>> Stashed changes`. Anyone reading `PLAN.md` would see a broken file and two contradictory checklists.
**How:**
- Kept the local checklist (Phases 0–6 ticked, Phase 7 open for the mock vivas).
- Credited both on the Phase 3 line: "run by Arnav for owner C; Abhilasha also marked it done on GitHub on 2026-10-11".
- Searched every file for leftover markers (`<<<<<<<`, `=======`, `>>>>>>>`). Only `PLAN.md` had them.
**Result:** `PLAN.md` is clean. Not committed yet (Arnav commits).
**Nuances / gotchas:**
- **Cause:** "Updated upstream / Stashed changes" is exactly what `git stash pop` writes when the stashed edits and the pulled edits touch the same lines. Here, Abhilasha's GitHub web edit and our local edit both changed the Phase 3 line. Git marks the conflict, but it does not stop you from committing the file with the markers in it.
- **How to avoid it:** after any `git stash pop`, `git pull` or merge, run `git status` and `git diff --check` (it flags leftover markers) before `git commit`.
**Alternatives considered:** Reverting the commit. Not needed: one hand edit fixes it, and the rest of that commit is correct.
**Viva angle:** —

---

## 2026-10-14 16:30 | Phase 7.3 | Interactive web showcase: replay, what-if lab, the trained model running in the browser  (run by: Arnav, coordinator A)
**Tags:** [RESULT] [DECISION] [NUANCE] [SETUP]
**What we did:**
- Built one self-contained web page that presents the whole project interactively.
- Published it online (private until shared from its Share menu; ask Arnav for the link).
- What the page does:
  - replays the 6 test sessions;
  - runs the saved MLP and Ridge inside the browser for what-if questions;
  - shows the CV, ablation, importance and safety results.
**Why:** For the presentation and viva we need something we can click through live on any laptop, without Python. The Streamlit app (`app.py`) needs Python and the git-ignored models. This page needs only a browser.
**How:**
- `showcase/build_showcase.py` (run from the repo root: `python showcase/build_showcase.py`) packs three things into the page:
  - **The test data.** The 6 test sessions (8 raw inputs + the real winding temperature, exact float32 values) and the saved Phase 5 predictions of the 3 finalists (0.001 °C, as in `test_predictions.csv`), gzip-compressed.
  - **The model weights.** From the saved pipelines `m6_mlp_64_32.joblib` (StandardScaler + MLP 45 → 64 → 32 → 1, ReLU) and `m3_ridge.joblib` (StandardScaler + Ridge, alpha = 10).
  - **The result numbers.** Every number the page shows, read from `outputs/results/`. Nothing is typed in by hand.
- **The page itself:** `showcase/template.html`, plain HTML/CSS/JavaScript with no libraries; the charts are drawn on canvas and SVG. In the browser, the JavaScript:
  1. rebuilds all 45 features exactly like `src/features.py` (physics features first, then an EWMA per session with `adjust=True`, every value stored as float32);
  2. runs the MLP forward pass: standardise, then two ReLU layers and the output.
- **Checks before writing the page.** The build script repeats the browser's maths in numpy and stops if anything disagrees:
  - per-session RMSE vs `test_metrics_per_profile.csv`;
  - the safety table vs `safety_alarm.csv`;
  - browser-style predictions vs the saved ones.
  The check results are saved to `outputs/results/showcase_check.json`.
- **Outputs.** Both are 4.52 MB and git-ignored (they embed test data):
  - `showcase/motor_showcase.html`: a complete page; double-click it to present offline (without internet the fonts fall back to system fonts);
  - `showcase/motor_showcase_artifact.html`: the same content, used for publishing.
**Result:**
- **The in-browser models match the saved Phase 5 predictions.** The largest difference over all 141,024 test rows is MLP 0.00053 °C and Ridge 0.00052 °C. That is just the 0.001 °C rounding of the saved CSV, so the page runs the real trained model.
- **The page's live safety calculation reproduces `safety_alarm.csv` exactly** for k = 0, 1 and 2 (a badge in the page says so).
- **What-if example** (session 66, coolant 10 °C warmer; `showcase_check.json`):

  | Quantity | Recorded inputs | What-if inputs |
  |---|---|---|
  | Mean change in the MLP's estimate | — | +8.53 °C |
  | Peak estimate | 127.05 °C | 136.17 °C |
  | Time at or above 104.79 °C | 29.5 min | 50.3 min |
  | Rows outside the training range | — | 0.83 % |

  This is physically sensible: the winding sits on top of the coolant temperature, so warmer coolant lifts it by almost the same amount.
- **The page's sections:**
  - **Live replay:** session and model pickers, play/scrub, a safety-margin slider, an alarm lamp and the running RMSE.
  - **What-if lab:** coolant −20 to +20 °C; load × 0.6 to 1.3.
  - **Thermal-memory explainer:** the current against its 1/5/15/45-min EWMAs, with live correlations, plus the memory curve.
  - **Results:** the model leaderboard (CV ± std and test), the ablation and the importance.
  - **Safety:** the trade-off curve.
  - **Method:** the method and its limits.
- **Checked in a browser:** desktop and phone width (375 px, no sideways scrolling), light and dark themes, no console errors.
**Nuances / gotchas:**
- **Test data in the page.** The page displays the test sessions and runs the frozen models on them. This is presentation only, like the end-to-end check in `MST_final`: no model, feature or setting was changed or chosen because of it. The test set was used for evaluation only once (2026-10-10 09:24:52).
- **Why the browser differs by 0.0005 °C:** `test_predictions.csv` keeps 3 decimals. The browser computes in float64 with float32 storage, like pandas + scikit-learn.
- **The what-if is not a measurement.** No sensor exists for an invented scenario, so it shows what the model believes. The page warns when rows are pushed outside the training range (coolant, current magnitude, torque).
- **"Load scale" is an approximation.** It multiplies i_d, i_q and torque together, because in a PMSM torque is almost proportional to i_q (r = 0.9965 in EDA). Voltages and speed stay as recorded, so this is a what-if, not a motor simulation.
- **The hot level is not the insulation limit.** The alarm's "hot level" of 104.79 °C is the 90th percentile of the training winding temperatures, not the class F insulation limit (155 °C). Teachers may ask.
- **Dataset terms.** The page carries 6 sessions of the Kaggle dataset. It is private by default; read the dataset's terms before making it public.
- **A CSS trap, caught before it showed:** a tooltip styled `display: grid` ignores the HTML `hidden` attribute, so hidden tooltips would stay visible in the offline file. Fix: `[hidden] { display: none !important; }` in the page's CSS.
**Alternatives considered:**
- **Extending the Streamlit app:** the presenting laptop would need Python and the git-ignored models.
- **A charting library (Plotly, Chart.js):** needs internet (a CDN) and is slow with 36,000-point sessions. Hand-drawn canvas charts work offline and stay fast.
- **LightGBM in the browser (1000 trees):** possible but heavy. The replay uses its saved predictions instead.
- **16-bit inputs, to halve the file size:** rejected. Exact float32 values make the browser-vs-saved check exact.
**Viva angle:** Q: Is the model in your web page the real one? A: Yes. The page rebuilds all 45 features from the raw signals and runs the saved MLP weights in JavaScript. Over all 141,024 test rows it matches our saved Phase 5 predictions to 0.0005 °C, which is the CSV's rounding.

---

## 2026-10-14 16:40 | Handover  (run by: Arnav)
**Tags:** —
**Where we stopped:**
- The interactive showcase is built, checked and published.
- The `PLAN.md` conflict markers are fixed.
- Phase 7 is complete except the per-member mock vivas.
- **Not committed yet:** `PLAN.md`, `.gitignore`, `README.md`, `LOG.md`, `CONCEPTS.md`, `VIVA_QA.md`, `showcase/` (builder + template) and `outputs/results/showcase_check.json`.
**What's next (exact next steps):**
1. Commit and push: `git add -A`, `git commit -m "Interactive showcase + fix PLAN.md conflict markers"`, `git push`. The built 4.5 MB pages are git-ignored on purpose.
2. Share the interactive showcase page (published online; ask Arnav for the link) with the team from its Share menu.
3. Every member: a mock viva, as described in `PLAN.md` Phase 7.
4. Fill in the B–E names (`PLAN.md`, the report, the slides, the tracker).
**Open issues / questions:**
- The deadline is still not recorded.
- `misc.txt` is still unexplained.
**Before you start, you must know:**
- **Rebuilding the page** (`python showcase/build_showcase.py`) needs the git-ignored `data/processed/measures_v2.parquet` and `outputs/models/` (notebooks 01, 03 and 04). It takes about 10 s.
- **To present offline,** double-click `showcase/motor_showcase.html`. Everything except the web fonts works without internet.
- **After `git stash pop` or a pull,** check for conflict markers before committing (see the 16:05 entry).

---

## 2026-10-14 17:00 | Phase 7.4 | Repo cleanup: team rules moved to CONTRIBUTING.md  (run by: Arnav)
**Tags:** [DECISION] [SETUP]
**What we did:** Cleaned the repo before the final upload. The team rules now live in `CONTRIBUTING.md`, and the links to private online pages were removed from the docs.
**Why:** The repo should hold only what a teammate or grader needs to run and understand the project. The online pages are private, so their links were useless to anyone without access.
**How:**
- New `CONTRIBUTING.md`: how we work, code style, and the exact `LOG.md` / `CONCEPTS.md` / `VIVA_QA.md` formats, with the same section numbers as before (4 = logging, 4.7 = concepts, 4.8 = viva). `README.md`, `PLAN.md`, `CONCEPTS.md` and this log now point to it.
- The old local tool settings file is no longer tracked in git. It stays on Arnav's laptop.
- Links to the online tracker, slides and showcase were replaced with "ask Arnav for the link".
- Mock viva: teammates pair up and quiz each other with 10 random questions from `VIVA_QA.md`.
**Result:** The project runs from the repo as before: `requirements.txt`, `src/`, `notebooks/01`–`06` + `MST_final`, `app.py`, `showcase/`, `outputs/results/`, `outputs/figures/`, `docs/`. No numbers changed.
**Nuances / gotchas:** Earlier entries were reworded in a few places (rule-file name, links, session wording) without changing any number or result. Older git commits still contain the old files; only the current version is clean.
**Alternatives considered:** Rewriting the git history to remove the old files from past commits. Rejected: it needs a force-push, which breaks every teammate's clone.
**Viva angle:** —

---
