# Motor winding temperature: a virtual sensor (UCS321 MST, statement #6)

We estimate the **stator winding temperature (°C)** of an electric motor from signals its controller already measures (ambient and coolant temperature, voltages, currents, speed, torque), using supervised ML **regression**. GE Power Systems is the assignment's scenario. The data is a public Paderborn University test-bench dataset (50 kW PMSM, 2 Hz, 69 sessions, 184.84 h).

| Phase | What | Status |
|---|---|---|
| 0 | Setup & data check (`notebooks/01_data_check.ipynb`) | ✅ |
| 1 | Problem understanding (`docs/problem.md`) | ✅ |
| 2 | EDA, test sessions frozen first (`notebooks/02_eda.ipynb`) | ✅ |
| 3 | Pre-processing & features: 45 inputs, physics + EWMA "thermal memory" (`notebooks/03_preprocessing_features.ipynb`) | ✅ |
| 4 | 9 models, session-wise 5-fold CV; finalists MLP, LightGBM, Ridge (`notebooks/04_modelling.ipynb`) | ✅ |
| 5 | Test set used **once** (2026-10-10 09:24:52): MLP RMSE 6.00 °C, Ridge 4.97, LightGBM 5.11; targets met (`notebooks/05_evaluation.ipynb`) | ✅ |
| 6 | Innovation: ablation, memory curve, safety alarm, data efficiency (`notebooks/06_innovation.ipynb`) + demo `app.py` | ✅ |
| 7 | Flow diagram, report (`docs/report/report.md`), 12 slides, `MST_final.ipynb`, interactive showcase (`showcase/`): done. **Mock viva for every member still to do** | almost |

**Headline result:** a virtual sensor that estimates the winding temperature of unseen sessions with RMSE about 5–6 °C, against 24.5 °C for "coolant + offset". The EWMA thermal-memory features are worth more than 8 °C (ablation: 4.92 → 13.18 °C without them).

The **interactive showcase (present this)**, the **slides**, the **live team tracker** and the **EDA showcase** are published online; ask Arnav for the links. Offline: `showcase/motor_showcase.html` (after building it) and `docs/showcase/index.html`.

## Start here (new teammate)
Read these in order. Viva questions can go to **anyone**, so read all of them:
1. `PLAN.md`: the phases, the rules and the team split (plan **v2**)
2. `CONTRIBUTING.md`: how we work and how to log
3. `LOG.md`: everything we did, why, and every number, top to bottom
4. `docs/problem.md`: the problem in plain words
5. `CONCEPTS.md`: every concept explained simply
6. `VIVA_QA.md`: likely viva questions with our answers

## One-time setup (Windows)
1. Install **Python 3.11** (python.org). Newer versions can lack library wheels.
2. Clone and set up:
   ```
   git clone https://github.com/ArnavCodez/Ai-for-engineers-MST-project.git
   cd Ai-for-engineers-MST-project
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   The first install took about 19 min on one laptop.
3. Get the data (300 MB, not in git): `python src\download_data.py`. The source and checksum are in `data/README.md`.
4. Run `notebooks/01_data_check.ipynb` once. It creates `data/processed/measures_v2.parquet`, which the other notebooks use.
5. For the live demo and `MST_final.ipynb`, also run notebooks 03 and 04 (about 25 min). They create the features and the saved models, which are git-ignored.

## The demo
```
streamlit run app.py
```
It replays one of the 6 test sessions: the estimated vs real winding temperature, a safety margin and an overheating alarm lamp. Without the saved models it falls back to the predictions saved in Phase 5, so it always works.

## The interactive showcase (best for the presentation)
A single web page with the whole project: a replay of the 6 test sessions with an alarm lamp, a **what-if lab** where our saved MLP runs inside the browser (change the coolant temperature or the load), the thermal-memory explainer, the model leaderboard, the ablation and the safety-alarm trade-off.
- **Online:** ask Arnav for the link.
- **Offline:** build it once, then double-click `showcase/motor_showcase.html` (needs only a browser):
  ```
  python showcase/build_showcase.py
  ```
  This needs the data and the saved models (notebooks 01, 03 and 04). It re-checks every number against `outputs/results/` before writing the page. The built pages embed test data, so they are git-ignored.

## Every work session
```
git pull
```
Then read the last 3 entries of `LOG.md` and the phase checklist at the top of `PLAN.md`. Do your phase, following `PLAN.md` and `CONTRIBUTING.md`. Log every step in `LOG.md` (plus new concepts in `CONCEPTS.md` and new questions in `VIVA_QA.md`), then upload right away:
```
git add -A
git commit -m "Phase N: what we did"
git push
```
Only one person should run a phase at a time, so `LOG.md` never conflicts.

## Ground rules (from `CONTRIBUTING.md`)
- **Test sessions 6, 7, 21, 61, 66, 81 were used once** (Phase 5). Don't tune anything on them now. Load the split from `outputs/results/split_profiles.json`, and never re-draw it.
- Use `src/config.py` for the target, inputs and forbidden columns. `pm`, `stator_tooth` and `stator_yoke` are **never** inputs (leakage).
- Every number in slides or reports must come from a file in `outputs/results/`.
- Data, `.venv` and saved models are git-ignored. Don't commit them.

## Folder map
```
CONTRIBUTING.md      team rules: workflow, code style, logging formats
PLAN.md  LOG.md  CONCEPTS.md  VIVA_QA.md
requirements.txt     pinned versions (Python 3.11)
data/README.md       dataset source, version, SHA-256 (data itself is git-ignored)
app.py               Streamlit recorded-data replay demo (Phase 6, I5)
showcase/            interactive web showcase: build_showcase.py + template.html (built pages are git-ignored)
docs/problem.md      Phase 1 problem definition
docs/flow_diagram.md (+ .png)  required flow diagram (Mermaid)
docs/report/report.md          written report in rubric order
docs/showcase/       interactive EDA explorer (index.html + eda_data.js)
notebooks/           01_data_check, 02_eda, 03_preprocessing_features, 04_modelling,
                     05_evaluation, 06_innovation, MST_final (one-file summary)
src/                 config.py, data.py, features.py, modelling.py, plotting.py, download_data.py
outputs/figures/     all PNG figures (eda_*, feat_*, model_*, eval_*, innov_*)
outputs/results/     every number we quote (JSON/CSV), incl. split_profiles.json, test_predictions.csv
```
