# Motor winding temperature: a virtual sensor (UCS321 MST, statement #6)

We estimate the **stator winding temperature (°C)** of an electric motor from signals its controller already measures (ambient and coolant temperature, voltages, currents, speed, torque), using supervised ML **regression**. GE Power Systems is the assignment's scenario. The data is a public Paderborn University test-bench dataset (50 kW PMSM, 2 Hz, 69 sessions, 184.84 h).

| Phase | What | Status |
|---|---|---|
| 0 | Setup & data check (`notebooks/01_data_check.ipynb`) | ✅ |
| 1 | Problem understanding (`docs/problem.md`) | ✅ |
| 2 | EDA, test sessions frozen first (`notebooks/02_eda.ipynb`) | ✅ |
| 3 | Pre-processing & features (physics + EWMA "thermal memory") | next |
| 4–7 | Models → test evaluation → innovation/demo → slides & viva | to do |

**Live team tracker** and **EDA showcase:** published online; ask Arnav for the links (or open `docs/showcase/index.html` locally)

## Start here (new teammate)
Read these in order. Viva questions can go to **anyone**, so read all of them:
1. `PLAN.md`: the phases, the rules and the team split (plan **v2**)
2. `LOG.md`: everything we did, why, and every number, top to bottom
3. `docs/problem.md`: the problem in plain words
4. `CONCEPTS.md`: every concept explained simply
5. `VIVA_QA.md`: likely viva questions with our answers

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
- **Test sessions 6, 7, 21, 61, 66, 81 are locked** until Phase 5. Load the split from `outputs/results/split_profiles.json`, and never re-draw it.
- Use `src/config.py` for the target, inputs and forbidden columns. `pm`, `stator_tooth` and `stator_yoke` are **never** inputs (leakage).
- Every number in slides or reports must come from a file in `outputs/results/`.
- Data, `.venv` and saved models are git-ignored. Don't commit them.

## Folder map
```
CONTRIBUTING.md      team rules: workflow, code style, logging formats
PLAN.md  LOG.md  CONCEPTS.md  VIVA_QA.md
requirements.txt     pinned versions (Python 3.11)
data/README.md       dataset source, version, SHA-256 (data itself is git-ignored)
docs/problem.md      Phase 1 problem definition
docs/showcase/       interactive EDA explorer (index.html + eda_data.js)
notebooks/           01_data_check, 02_eda, ... (run top to bottom)
src/                 config.py, data.py, plotting.py, download_data.py
outputs/figures/     all PNG figures (eda_01 ... eda_08)
outputs/results/     every number we quote (JSON/CSV), incl. split_profiles.json
```
