# CONCEPTS: MST Project (Motor Winding Temperature)

Every concept we use, explained simply. The format is in `CONTRIBUTING.md` section 4.7.
Add a concept the first time it is used. Improve an entry when our understanding improves.

## Domain (motors & physics)
<!-- still to add: copper loss I²R, iron loss, coolant -->

### Insulation thermal class (and the 10 °C rule)
- **In one line:** a letter grade (A, E, B, F, H) that says the maximum hot-spot temperature a motor's winding insulation is designed for.
- **Explained simply:** The copper wire in the winding is coated with insulation, like the plastic on a charger cable, so neighbouring turns don't short. Heat slowly "cooks" this coating. Standard IEC 60085 sorts insulation systems into classes by how much heat they survive. The hotter it runs, the faster it ages: a common rule of thumb is that **life halves for every 10 °C hotter** (and doubles for every 10 °C cooler). So a few degrees of error in a temperature estimate really matter.
- **Formula (if any):**
  - Classes: A = 105 °C, E = 120 °C, B = 130 °C, F = 155 °C, H = 180 °C.
  - Hot spot ≈ rated ambient (often 40 °C) + temperature rise + 10 °C hot-spot allowance.
  - Life rule of thumb: L(T + 10 °C) ≈ L(T) / 2.
  - Sources: Wikipedia "Insulation system"; Cowern, EC&M 2000 (see `docs/problem.md`).
- **Why we used it here:** it is the main reason winding temperature matters (`docs/problem.md`, section 2). Our hottest reading, 141.36 °C, is below Class F (155 °C).
- **Where in our code:** `docs/problem.md`. Later, the safety alarm (Phase 6, I3) uses a temperature threshold in the same spirit.
- **Common confusion / trap:**
  - The class temperature is not "the temperature where it instantly melts". The insulation just ages much faster above it.
  - We don't know the test motor's insulation class (it isn't in the data), so we never claim a specific limit for it.

### Derating
- **In one line:** deliberately running a motor below its full capability to keep it safe.
- **Explained simply:** If you can't see the winding temperature, you must assume the worst and hold back power "just in case", like driving slowly because your temperature gauge is broken. That wastes performance. A trustworthy temperature estimate lets the motor work closer to its true limit.
- **Formula (if any):** —
- **Why we used it here:** it is the "cost of not knowing" in our motivation (`docs/problem.md`, section 2).
- **Where in our code:** `docs/problem.md`.
- **Common confusion / trap:** derating isn't a fault. It's a protection strategy. Our model's job is to make it smarter, not to remove protection.

### Virtual sensor (soft sensor)
- **In one line:** a model that *calculates* a quantity from other, easy measurements instead of measuring it with a physical sensor.
- **Explained simply:** Putting a temperature sensor inside the copper winding of a motor is costly and fiddly, and the sensor can break. But the motor controller already knows the currents, voltages, speed, torque and coolant temperature. If we learn how these relate to the winding temperature, using lab recordings where a real sensor *was* fitted, the model can then estimate the temperature on motors that have no sensor. It's like guessing how hot the inside of a pressure cooker is from how long and how high the flame has been on, without opening it.
- **Formula (if any):** estimated winding temperature = f(ambient, coolant, u_d, u_q, i_d, i_q, motor_speed, torque, and their recent history), where f is the trained model.
- **Why we used it here:** it is exactly what the GE statement asks for: estimate winding temperature from ambient temperature, speed, torque, voltage and current.
- **Where in our code:** the whole project. The model is trained in Phase 4 and judged in Phase 5.
- **Common confusion / trap:** a virtual sensor may only use signals a real motor would have. Using the neighbouring temperature sensors (`pm`, `stator_tooth`, `stator_yoke`) as inputs is cheating (leakage). If a motor had those sensors, it wouldn't need our model.

### PMSM (Permanent Magnet Synchronous Motor)
- **In one line:** an AC motor whose rotor carries permanent magnets and turns exactly in step ("synchronously") with the rotating magnetic field made by the stator.
- **Explained simply:** The outer, fixed part (the **stator**) has copper windings fed with 3-phase AC. Together these currents make a magnetic field that rotates. The inner part (the **rotor**) has permanent magnets, which get "dragged" along by that rotating field at exactly the same speed. There are no brushes and no current in the rotor, so it is very efficient and compact. That's why EVs use it. The current flowing in the stator copper heats it up. That stator **winding** temperature is what we predict.
- **Formula (if any):** speed (rpm) = 60 × electrical frequency (Hz) / number of pole pairs.
- **Why we used it here:** our dataset is a PMSM on a test bench at Paderborn University.
- **Where in our code:** the whole project. The data is described in `notebooks/01_data_check.ipynb`.
- **Common confusion / trap:** "synchronous" doesn't mean "slow" or "constant speed". It means the rotor turns at the *same* speed as the field, unlike an induction motor, whose rotor slightly lags (slips).

### dq frame / Park transform
- **In one line:** a maths trick that turns the three sinusoidal phase currents (or voltages) into two almost-constant values, `i_d` and `i_q`.
- **Explained simply:** In the stator, the three phase currents are sine waves that swing hundreds of times per second, which is hard to control. The Park transform looks at them from a frame that **rotates with the rotor**. Think of a merry-go-round: from the ground a horse whizzes past, but if you sit on the merry-go-round it seems to stand still. From the rotor's point of view, the currents become two steady "DC-like" values:
  - `i_d` (direct axis, along the magnet's field) controls the magnetic flux;
  - `i_q` (quadrature axis, 90° ahead) makes the torque.
  Voltages work the same way (`u_d`, `u_q`).
- **Formula (if any):** First the Clarke transform: iα = i_a and iβ = (i_a + 2·i_b) / √3. Then Park, with θ the rotor's electrical angle: i_d = iα·cos θ + iβ·sin θ and i_q = −iα·sin θ + iβ·cos θ. Current magnitude: i_s = √(i_d² + i_q²), which equals the amplitude of each phase current (in the "amplitude-invariant" version).
- **Why we used it here:** the dataset gives currents and voltages already in dq form. In Phase 3 we build i_s and electrical power from them.
- **Where in our code:** columns `i_d`, `i_q`, `u_d`, `u_q` (notebook 01 shows their ranges).
- **Common confusion / trap:**
  - `i_d` and `i_q` are not two physical wires. They are a mathematical *view* of the 3 phase currents.
  - A negative `i_d` is normal. In our data `i_d` is at most 0.052 A. It means **field weakening**: the controller weakens the magnet's field so the motor can reach high speeds.

### Thermal inertia
- **In one line:** things take time to heat up and cool down, so temperature follows the load slowly, with a delay.
- **Explained simply:** A pressure cooker stays hot for a while after you switch off the gas. A motor winding is the same: it has mass, and heat takes time to build up or flow away. So the winding temperature depends on how hard the motor worked over the last *minutes*, not just on the current at this instant. In our data the winding temperature changes by a median of only **0.022 °C** between two rows 0.5 s apart.
- **Formula (if any):** the simplest model is a first-order system, with time constant τ = thermal resistance × thermal capacity. The temperature covers about 63 % of a step change after τ.
- **Why we used it here:**
  1. It is the reason we expect "memory" features (EWMA, Phase 3) to help.
  2. It is the evidence that the rows are in time order (Phase 0.5).
- **Where in our code:** `notebooks/01_data_check.ipynb`, section 4 (row-to-row change).
- **Common confusion / trap:** thermal inertia also makes neighbouring rows nearly identical, so the rows are **not independent**. A random train/test split would leak near-copies into the test set (N2).

## Data & pre-processing
<!-- still to add: GroupKFold, feature engineering, EWMA, standardisation -->

### Data leakage
- **In one line:** the model gets information during training that it would not have in real use, so its score looks better than it really is.
- **Explained simply:** It's like an exam where the answer key is printed on the back of the question paper: a perfect score that means nothing. Leakage can come from:
  - an input that is secretly almost the answer (our `stator_tooth`, r = 0.970 with the target);
  - near-copies of test rows in training (neighbouring rows 0.5 s apart);
  - decisions made after peeking at the test data.
- **Formula (if any):** —
- **Why we used it here:** It drives three choices:
  - we forbid `pm`, `stator_tooth` and `stator_yoke` (EDA proved r = 0.80–0.97);
  - we split by whole sessions;
  - we froze the test sessions before EDA.
- **Where in our code:** `src/config.py` (`FORBIDDEN`), `notebooks/02_eda.ipynb` sections 3 and 8. Phase 3 adds a leakage checklist.
- **Common confusion / trap:** a "too good to be true" score (e.g. R² ≈ 1) is usually leakage, not genius. Always ask: "Would the real motor have this information at this moment?"

### Train / test split by session (and freezing the test set)
- **In one line:** we keep 6 whole recording sessions completely unseen until the very end, and judge the final model only on them.
- **Explained simply:** The test set is the final exam. It must contain questions the student has never seen. Because neighbouring rows are near-copies, we hold out *whole sessions*, not random rows. We also chose and locked the test sessions **before** exploring the data, so nothing we noticed in plots could be tuned towards them. The choice was stratified: 2 short, 2 medium and 2 long sessions, with seed 42.
- **Formula (if any):** test share = test rows / all rows = 141,024 / 1,330,816 = 10.60 %.
- **Why we used it here:** for an honest final score on "unseen operating sessions" (`docs/problem.md`, success criterion 2).
- **Where in our code:** `notebooks/02_eda.ipynb` section 3 → `outputs/results/split_profiles.json`, loaded by `src/data.py → load_split()`.
- **Common confusion / trap:**
  - Re-drawing the split later, or choosing it by hand to look good, ruins its fairness. Use the saved file.
  - The *validation* used for tuning (Phase 4) comes from the training sessions only.

## Exploratory data analysis

### Distribution and histogram
- **In one line:** a histogram shows how often each value occurs, by counting values in equal-width bins.
- **Explained simply:** Sort all the readings into buckets (say 60 buckets from the smallest to the largest value) and draw a bar for how full each bucket is. Tall bars = common values. It shows the range, the typical values, spikes (like torque = 0 when idling) and gaps. Our target spans 18.59–141.36 °C, with median 64.63 °C.
- **Formula (if any):** bin width = (max − min) / number of bins.
- **Why we used it here:** Fig 3, to see every column's range, check units, and spot fixed levels and spikes.
- **Where in our code:** `notebooks/02_eda.ipynb` section 7 → `eda_03_histograms.png`.
- **Common confusion / trap:** the shape depends on the number of bins. Also, a histogram of 2 Hz data counts *time*: a value that lasted a long time looks "common" even if it's just one long, steady phase.

### Outlier
- **In one line:** a value far away from the rest. It might be an error, or a rare but real event.
- **Explained simply:** Our lowest ambient reading, 8.78 °C, is about 8 standard deviations below the mean ambient (24.565 °C). That's an outlier. But "unusual" isn't "wrong": it's only 5 rows and physically possible. Deleting real data needs a reason, and removing rows would break the 0.5 s time spacing.
- **Formula (if any):** a common rule is |x − mean| > k × std, or outside 1.5 × IQR beyond the quartiles (boxplot whiskers).
- **Why we used it here:** to decide what to clean. We kept the readings (`LOG.md` Phase 2.3).
- **Where in our code:** `notebooks/02_eda.ipynb` section 13.
- **Common confusion / trap:** automatically dropping every "outlier" can delete exactly the extreme operating points (very hot moments) the model most needs to learn.

### Pearson correlation (and why it is not causation)
- **In one line:** a number r between −1 and +1 that measures how well two columns follow a straight-line relationship.
- **Explained simply:**
  - r = +1: when one goes up, the other always goes up in proportion.
  - r = −1: one goes up while the other goes down.
  - r ≈ 0: no straight-line link (there may still be a curved one).
  But correlation doesn't tell you *why*. Our `i_d` has r = −0.632 with the winding temperature. That's not because negative current cools the winding: high speed needs more negative `i_d` (field weakening, r = −0.68 with speed), and high speed goes with hotter windings. A third factor connects them.
- **Formula (if any):** r = cov(X, Y) / (std(X) · std(Y)).
- **Why we used it here:** Fig 4, to prove the forbidden temperatures leak (0.970 / 0.862 / 0.796) and that no allowed signal alone is enough (best |r| = 0.632). Also torque vs i_q, r = 0.9965.
- **Where in our code:** `notebooks/02_eda.ipynb` section 8 → `eda_correlation_matrix.csv`, `eda_target_correlations.csv`.
- **Common confusion / trap:**
  - Correlation ≠ causation.
  - A low r doesn't mean "unimportant" if the link is curved or changes sign (torque is + when motoring and − when braking, so r is only 0.105).

### Hexbin plot
- **In one line:** a 2-D histogram. The plot area is cut into hexagons, each coloured by how many points fall inside.
- **Explained simply:** With 1.2 million points, a scatter plot is one solid blob and hides where most of the data is. Hexbin counts the points per hexagon instead, usually on a log colour scale, so you can see dense and rare regions.
- **Formula (if any):** colour = log(count of points in the hexagon).
- **Why we used it here:** Fig 5, winding vs current and vs coolant. It showed that at the same current the winding can be cold or hot, and that the winding is sometimes below the coolant (4.75 % of rows).
- **Where in our code:** `notebooks/02_eda.ipynb` section 9 → `eda_05_hexbin_current_and_coolant.png`.
- **Common confusion / trap:** colour shows *how many rows*, not temperature. Here, many rows can simply mean "the motor stayed in this state for a long time".

### Lagged (cross-)correlation
- **In one line:** the correlation between one signal now and another signal shifted later by some delay, computed for many delays.
- **Explained simply:** If heat today depends on current a few minutes ago, then lining up current(t) with temperature(t + a few minutes) should match better than lining up the same moments. We slide the temperature later by 0, 0.5, 1, …, 60 minutes and compute r each time. The delay with the highest r tells us how "late" the temperature reacts. Our median across 53 sessions is 2.5 min, with r rising from 0.645 to 0.746.
- **Formula (if any):** r(lag) = corr( x[t], y[t + lag] ), lag in rows = minutes × 120 (at 2 Hz).
- **Why we used it here:** Fig 8, the evidence for thermal memory, and the motivation for EWMA features (Phase 3).
- **Where in our code:** `notebooks/02_eda.ipynb` section 12 → `eda_thermal_lag_per_session.csv`.
- **Common confusion / trap:**
  - The best lag is **not** the thermal time constant. It just says "the recent past matters".
  - With slowly drifting signals, correlations can be high for many lags, so read the peak, not the absolute values.

### Sampling rate
- **In one line:** how many measurements are taken per second, here **2 Hz**: one row every 0.5 s.
- **Explained simply:** The test bench writes down all 13 values twice a second. So the number of rows tells us the time: 7,200 rows = 1 hour. Our 1,330,816 rows are 184.84 hours.
- **Formula (if any):**
  - time step Δt = 1 / f = 1 / 2 Hz = 0.5 s;
  - hours = rows / 2 / 3600;
  - minutes = samples / 2 / 60, so an EWMA span of 120 samples = 1 minute.
- **Why we used it here:** to convert session lengths into hours (Phase 0), and later to convert EWMA spans into minutes (Phase 3).
- **Where in our code:** `SAMPLE_RATE_HZ = 2` in `notebooks/01_data_check.ipynb`, cell 2.
- **Common confusion / trap:** a high sampling rate doesn't mean "more independent data". 1.3M rows sounds huge, but neighbouring rows are almost the same moment, so the real amount of information is closer to "69 sessions".

### Parquet vs CSV
- **In one line:** CSV is plain text that any program can open; parquet is a compressed, column-by-column binary format that is much smaller and faster to load.
- **Explained simply:** A CSV stores each number as text, like `19.086669921875`. That's 15 characters for one number, and the computer has to re-read and convert it every time. Parquet stores the numbers in binary, groups each column together (similar numbers compress well), and remembers each column's type. For us: **300.1 MB CSV → 72.2 MB parquet**, and loading takes 0.42–1.75 s instead of 7.66–10.31 s.
- **Formula (if any):** —
- **Why we used it here:** every later notebook loads the data, so a small, fast file saves time and RAM.
- **Where in our code:** `notebooks/01_data_check.ipynb`, section 7. The output is `data/processed/measures_v2.parquet`.
- **Common confusion / trap:** you can't open parquet in Notepad or Excel. It needs `pyarrow` (or `fastparquet`) installed. The raw CSV stays untouched in `data/raw/`.

### float32 vs float64
- **In one line:** two ways to store a decimal number. float64 uses 8 bytes (about 16 significant digits); float32 uses 4 bytes (about 7 significant digits).
- **Explained simply:** float32 is like writing a measurement with 7 digits instead of 16. A temperature sensor isn't accurate to even 4 digits, so 7 is plenty. Switching halved the memory of our 12 decimal columns (127.8 → 63.9 MB; 138.4 → 74.5 MB in total). The largest change to any value was **0.000244 rpm** in `motor_speed`. The target changed by at most 0.0000076 °C.
- **Formula (if any):** largest rounding error ≈ half the gap between neighbouring float32 numbers. For values between 4,096 and 8,192 that gap is 2⁻¹¹ ≈ 0.000488, so the error is ≤ 0.000244.
- **Why we used it here:** to save RAM for Random Forest / LightGBM on a laptop (N6).
- **Where in our code:** `notebooks/01_data_check.ipynb`, section 7.
- **Common confusion / trap:** float32 is fine for sensor data. It is *not* fine for adding up millions of tiny numbers, or for money, where rounding errors pile up.

## Tools & environment

### Virtual environment (venv) and pinned requirements
- **In one line:** a private folder (`.venv/`) with its own Python and libraries, just for this project.
- **Explained simply:** Without a venv, every project on the laptop shares one Python, and installing a library for one project can break another. A venv is like a separate toolbox per project. `requirements.txt` lists the exact versions (e.g. `pandas==3.0.6`), so every teammate builds an identical toolbox. `pip freeze` records *everything* installed, including dependencies (119 packages for us).
- **Formula (if any):** —
- **Why we used it here:** team rule (one venv per project, Python 3.11), so the same code gives the same numbers on every laptop.
- **Where in our code:** `.venv/` (git-ignored), `requirements.txt`, `outputs/results/pip_freeze.txt`.
- **Common confusion / trap:**
  - Forgetting to activate the venv (`.venv\Scripts\activate`) installs packages into the global Python instead.
  - In Jupyter or VS Code, pick the `.venv` kernel, or the notebook can't find our libraries.

## Models
<!-- still to add: linear regression, Ridge/Lasso, decision tree, Random Forest, gradient boosting (LightGBM), MLP, hyperparameter tuning, overfitting -->

### Supervised learning
- **In one line:** learning from examples where the correct answer is already known.
- **Explained simply:** Like practising with a solved question bank: you see the question and the answer, and slowly learn the pattern. Each of our 1,330,816 rows is one example. The "question" is the inputs (currents, voltages, speed, torque, coolant, ambient), and the "answer" (the **label** or **target**) is the real winding temperature measured on the test bench. The model adjusts itself until its guesses match the answers as closely as possible.
- **Formula (if any):** learn f so that f(inputs) ≈ target, by making an error measure (e.g. the mean squared error) as small as possible on the training examples.
- **Why we used it here:** the statement explicitly asks for a *supervised* model, and our data has the true answer (`stator_winding`) in every row.
- **Where in our code:** every model in Phase 4 is trained with `model.fit(X_train, y_train)`. `y_train` holds the answers.
- **Common confusion / trap:** "supervised" doesn't mean a human watches the training. It means the data contains the answers. The opposite, unsupervised learning (e.g. clustering), has no answers to learn from.

### Regression (vs classification)
- **In one line:** predicting a *number* (e.g. 87.3 °C), as opposed to classification, which predicts a *category* (e.g. "hot" / "not hot").
- **Explained simply:** If the question is "how hot is the winding?", the answer is a number on a scale, so it's regression. If the question were "is the motor overheating, yes or no?", it would be classification. A number is more useful here: an engineer can compare it with the insulation limit and see how close we are.
- **Formula (if any):** regression errors are measured in the target's unit, e.g. RMSE in °C (added fully in Phase 4).
- **Why we used it here:** the statement says "regression model to estimate motor temperature", and temperature is a continuous number.
- **Where in our code:** Phase 4 models are all regressors (`LinearRegression`, `RandomForestRegressor`, `LGBMRegressor`).
- **Common confusion / trap:** "Logistic regression" is actually a *classification* method, despite its name. We don't use it.

## Evaluation & interpretation
<!-- MSE, RMSE, MAE, R², residuals, permutation importance, SHAP, generalisation gap, ablation study -->
