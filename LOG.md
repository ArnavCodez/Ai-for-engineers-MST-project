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
