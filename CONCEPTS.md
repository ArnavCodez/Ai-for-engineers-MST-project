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

### Feature engineering
- **In one line:** creating new input columns from the raw ones, so the model gets information in a form it can use more easily.
- **Explained simply:** The raw data says `i_d = −120 A, i_q = 80 A`. Heat in copper depends on the *total* current squared (I²R), so we hand the model `i_s² = i_d² + i_q²` directly instead of hoping it discovers this formula. It's like giving a student the formula sheet: same knowledge, much easier to use. Our 5 physics features are `i_s`, `u_s`, `i_s²`, `p_el` and `p_mech`; our 32 memory features are EWMAs.
- **Formula (if any):** i_s = √(i_d²+i_q²); u_s = √(u_d²+u_q²); p_el = 1.5(u_d·i_d + u_q·i_q); p_mech = T·n·2π/60.
- **Why we used it here:** no raw signal alone explains the winding (best |r| 0.632), and physics tells us which combinations make heat.
- **Where in our code:** `src/features.py` → `add_physics_features()`, `add_ewma_features()`; `notebooks/03_preprocessing_features.ipynb`.
- **Common confusion / trap:** engineered features must be computed **the same way** in training and in use (the demo app). That's why they live in one shared file, not copied into each notebook.

### EWMA (exponentially weighted moving average)
- **In one line:** an average of a signal's past in which recent values count most and older values fade away smoothly.
- **Explained simply:** Think of "how tired am I?". It depends mostly on the last hour, a bit on this morning, and hardly at all on last week. An EWMA keeps a running memory like that. A short span (1 min) reacts fast; a long span (45 min) remembers the slow build-up of heat. The winding temperature depends on how hard the motor worked over the last minutes (thermal inertia), so EWMAs give the model that memory.
- **Formula (if any):** μ_t = (1 − α)·μ_{t−1} + α·x_t with α = 2/(span + 1). Our spans 120 / 600 / 1800 / 5400 samples ÷ 120 samples per minute = 1 / 5 / 15 / 45 min. The last *span* samples carry about 86.5 % of the total weight.
- **Why we used it here:** Phase 2 showed the winding follows current² with a median delay of 2.5 min. The 5-min EWMA of current has r = 0.705 with the winding, against 0.583 for the raw current.
- **Where in our code:** `src/features.py → add_ewma_features()`, using `df.groupby("profile_id")[col].transform(lambda s: s.ewm(span=sp).mean())`.
- **Common confusion / trap:**
  - Compute it **per session** (or sessions get mixed), **in time order**, and **before** any thinning or shuffling.
  - It must be **causal** (past only). We proved it by recomputing on a cut session (difference 0.0).
  - At a session's start there is no history yet (warm-up): 27.9 % of training rows are in the first 45 min.

### Standardisation (StandardScaler)
- **In one line:** rescale each feature to mean 0 and standard deviation 1.
- **Explained simply:** Our features have very different sizes: `i_s²` reaches 130,693 A², while `ambient` stays around 25 °C. Ridge's penalty treats every coefficient alike, so without scaling it would be unfair to features with small numbers. Neural nets also train badly on unscaled inputs. Trees don't care, because a split "x > 5" works the same as "x/10 > 0.5".
- **Formula (if any):** z = (x − mean) / std, where the mean and std come from the **training** rows only.
- **Why we used it here:** for Linear/Ridge/Lasso/MLP in Phase 4, always inside a `Pipeline([("scale", StandardScaler()), ("model", …)])`.
- **Where in our code:** `notebooks/04_modelling.ipynb`.
- **Common confusion / trap:** fitting the scaler on *all* data before cross-validation leaks the validation folds' mean and std into training. Inside a Pipeline, it is re-fitted on each training fold only.

### Train / validation / test, and cross-validation (GroupKFold)
- **In one line:** training data fits the model, validation data chooses between models and settings, and test data gives the final, untouched score.
- **Explained simply:** Like practice papers (train), mock exams (validation) and the real exam (test). We don't keep one fixed validation set. We use **5-fold cross-validation** on the 63 training sessions: deal the sessions into 5 groups, train on 4 and validate on the 5th, repeat 5 times and average. **GroupKFold** makes sure all rows of a session stay in the same fold, so every validation score is on *unseen sessions*. The 6 test sessions are used only once, in Phase 5.
- **Formula (if any):** CV score = mean (± std) of the 5 fold scores.
- **Why we used it here:** about 60 training sessions is too few for one reliable fixed validation split. 5 folds use every session for validation once, and give a spread (std).
- **Where in our code:** `src/modelling.py → group_cv()` (GroupKFold(5), groups = profile_id); `notebooks/04_modelling.ipynb`.
- **Common confusion / trap:** a normal KFold on rows would put neighbouring 0.5 s rows on both sides and give far too optimistic scores. Always group by session.

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

### Baseline model
- **In one line:** a deliberately simple model that every real model must beat.
- **Explained simply:** Before celebrating an error of "5 °C", ask: what does a model that doesn't even look at the inputs get? Ours are:
  - **B0**, always predict the training mean;
  - **B1**, winding = coolant + a fixed offset ("just read the coolant thermometer").
  If a fancy model can't clearly beat these, it has learned nothing useful.
- **Formula (if any):** B0: ŷ = mean(y_train). B1: ŷ = coolant + mean(y_train − coolant_train).
- **Why we used it here:** plan Phase 4. The success target is defined relative to B1.
- **Where in our code:** `src/modelling.py → CoolantPlusOffset`; `notebooks/04_modelling.ipynb` section 4.
- **Common confusion / trap:** a baseline is not a "bad model to throw away". It's the yardstick that gives every other number its meaning.

### Linear regression
- **In one line:** predicts the target as a weighted sum of the inputs plus a constant: ŷ = w₁x₁ + w₂x₂ + … + b.
- **Explained simply:** It finds the weights that make the squared errors on the training rows as small as possible ("least squares"). It's fast, easy to explain (each weight says how much that input pushes the temperature) and hard to overfit with few features. But it can only draw straight-line (flat) relationships. Our features (I², EWMAs) do the non-linear work *before* the model sees them, which is why a linear model can work well here.
- **Formula (if any):** minimise Σ(yᵢ − ŷᵢ)².
- **Why we used it here:** M1 (8 raw inputs) vs M2 (45 features) shows how much the feature engineering adds.
- **Where in our code:** `notebooks/04_modelling.ipynb` section 5.
- **Common confusion / trap:** "linear" means linear in the *weights*, not in the physics. Using I² as an input lets a linear model capture a squared effect.

### Regularisation (Ridge and Lasso)
- **In one line:** a penalty that stops a model from relying on huge weights, so it generalises better.
- **Explained simply:** Our 45 features are strongly related (e.g. the 1, 5, 15 and 45-min EWMAs of current). Plain linear regression can then give one feature +500 and its twin −499, which fits training rows but is fragile. **Ridge** adds α·Σw² to the error, shrinking all weights. **Lasso** adds α·Σ|w|, which can push weights to exactly 0, i.e. it removes features. α sets the strength: too small = overfitting, too big = too simple (underfitting).
- **Formula (if any):** Ridge: minimise Σ(y−ŷ)² + α·Σw². Lasso: minimise (1/2n)·Σ(y−ŷ)² + α·Σ|w|.
- **Why we used it here:** the M3 models. In our CV, Lasso with α = 0.01 reached RMSE 5.20 °C and set 11 of 45 weights to 0. At α = 1.0 it dropped 34 features and got worse (6.57 °C), which is underfitting.
- **Where in our code:** `notebooks/04_modelling.ipynb` section 6 → `tuning_ridge.csv`, `tuning_lasso.csv`, `model_02_regularisation.png`.
- **Common confusion / trap:** the features must be **standardised** first, or the penalty unfairly punishes features measured in small units.

### Decision tree and Random Forest (bagging)
- **In one line:** a tree splits the data with yes/no questions; a Random Forest averages many trees, each trained on a random sample.
- **Explained simply:** A decision tree is like a game of 20 questions: "is i_s_ewma_600 > 150 A? is coolant > 40 °C?". Each final "leaf" predicts the average temperature of the training rows that landed there. One deep tree memorises the training data (overfits). A **Random Forest** grows many trees, each on a random half of the rows (`max_samples=0.5`) and considering random subsets of features at each split, then averages them. That's **bagging**: individual mistakes cancel out.
- **Formula (if any):** prediction = mean of the trees' predictions.
- **Why we used it here:** M4, to capture non-linear interactions. In our CV it overfitted clearly: training RMSE 1.78–3.01 °C against validation 5.82–5.92 °C across the 4 configurations.
- **Where in our code:** `notebooks/04_modelling.ipynb` section 7 → `tuning_rf.csv`.
- **Common confusion / trap:** **trees cannot extrapolate.** A tree can only predict values between the training leaves' averages. A session with a coolant level or load pattern unlike the training sessions is hard for trees, while a linear model can extend its trend.

### Gradient boosting (LightGBM)
- **In one line:** builds trees one after another, each new tree correcting the errors left by the previous ones.
- **Explained simply:** The first small tree makes a rough guess. The second tree is trained on the *errors* of the first, the third on what's still wrong, and so on, each contribution scaled down by the **learning rate**. Hundreds of small corrections add up to a strong model. LightGBM is a fast library that grows trees leaf by leaf (`num_leaves`).
- **Formula (if any):** ŷ = tree₁(x) + η·tree₂(x) + η·tree₃(x) + …, with η = learning rate.
- **Why we used it here:** M5, usually the strongest model for tabular data.
- **Where in our code:** `notebooks/04_modelling.ipynb` section 8 → `tuning_lgbm.csv`.
- **Common confusion / trap:** **early stopping on randomly chosen validation rows leaks** neighbouring rows of the same session. We switched early stopping off and judged every setting with session-wise folds.

### Neural network (MLP)
- **In one line:** layers of simple units ("neurons"), each computing a weighted sum followed by a non-linear function, trained by gradient descent.
- **Explained simply:** Inputs go into a layer of 64 neurons, then a layer of 32, then one output. Each neuron computes max(0, w·x + b) (ReLU). Training repeatedly nudges all the weights to reduce the error (the Adam optimiser, 40 passes over the data). It can learn complex shapes, but needs scaled inputs and tuning.
- **Formula (if any):** h = ReLU(W·x + b), layer after layer; output = w·h + b.
- **Why we used it here:** M6, an optional comparison (one fixed configuration).
- **Where in our code:** `notebooks/04_modelling.ipynb` section 9.
- **Common confusion / trap:** sklearn's `early_stopping=True` picks a *random* validation split, which leaks for time series, so we turned it off.

### Hyperparameters and tuning
- **In one line:** settings chosen *before* training (α, tree depth, number of trees, learning rate). They aren't learned from the data directly; we pick them by validation.
- **Explained simply:** **Parameters** (weights, tree splits) are learned by `fit()`. **Hyperparameters** are the knobs that control how learning happens. We tried a few settings per model and kept the one with the best **cross-validated** RMSE, never the test RMSE:
  - Ridge: 6 α values; Lasso: 3 α values;
  - Random Forest: 4 random configurations; LightGBM: 8 random configurations (`ParameterSampler`, seed 42).
- **Formula (if any):** best setting = argmin over settings of the mean CV RMSE.
- **Why we used it here:** plan Phase 4. A small budget, because the laptop has limited time and memory.
- **Where in our code:** `notebooks/04_modelling.ipynb` sections 6–8 → `outputs/results/tuning_*.csv`.
- **Common confusion / trap:** tuning on the test set ("try settings until the test score looks good") turns the test set into training data. Our test set is opened once, in Phase 5.

### Overfitting, underfitting and the bias–variance trade-off
- **In one line:** overfitting = memorising the training data (great training score, poor on new data); underfitting = too simple to capture the pattern (poor on both).
- **Explained simply:** A student who memorises past papers word for word (overfitting, *high variance*) fails new questions. One who only learned "the answer is usually C" (underfitting, *high bias*) fails everything. We spot it by comparing **training RMSE** with **validation RMSE**: a big gap means overfitting. Our Random Forests had training RMSE 1.78–3.01 °C but validation 5.82–5.92 °C, a clear overfit. Regularisation (α, `min_samples_leaf`, fewer leaves) moves a model towards less variance.
- **Formula (if any):** expected error ≈ bias² + variance + noise.
- **Why we used it here:** to read the CV table and choose settings (`model_01_cv_comparison.png` shows training RMSE as dots).
- **Where in our code:** `src/modelling.py → group_cv()` records `train_rmse` for every fold.
- **Common confusion / trap:** a low *training* error is not success. Only errors on unseen sessions count.

### Out-of-fold (OOF) predictions
- **In one line:** the prediction each training row receives from the cross-validation model that did **not** train on it.
- **Explained simply:** In 5-fold CV every session is held out exactly once. Collecting the predictions made for the held-out sessions gives one "honest" prediction per training row, as if each session were new. Their errors show how big our mistakes typically are on unseen sessions, *without* touching the test set.
- **Formula (if any):** residual = ŷ_OOF − y; we use its standard deviation σ as a safety margin (Phase 6, I3).
- **Why we used it here:** to set the safety-alarm margin from training data only.
- **Where in our code:** `notebooks/04_modelling.ipynb` section 14 → `modelling_summary.json["oof_best"]`.
- **Common confusion / trap:** errors of a model on its *own* training rows are far too small to use as a margin (see overfitting above).

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

### Error metrics: MSE, RMSE, MAE, R², max, p95 and signed error
- **In one line:** different ways to summarise "how wrong" the predictions are, each answering a slightly different question.
- **Explained simply:** With error = predicted − actual:
  - **MSE**: the average of squared errors, in °C², hard to read directly.
  - **RMSE** = √MSE, in °C. Squaring makes big errors count a lot, so RMSE punishes rare big misses.
  - **MAE**: the average size of the error, in °C. "Typically we're off by this much."
  - **R²**: the share of the temperature's variation the model explains (1 = perfect, 0 = no better than the mean, below 0 = worse).
  - **Max |error|**: the single worst miss.
  - **p95 |error|**: 95 % of errors are smaller than this.
  - **Mean signed error**: negative means we under-predict on average, the dangerous direction here.
  Our final MLP on the test set: RMSE 6.005 °C, MAE 3.693 °C, R² 0.946, p95 14.60 °C, max 60.31 °C, mean signed −1.95 °C.
- **Formula (if any):** RMSE = √(mean(e²)); MAE = mean(|e|); R² = 1 − Σe² / Σ(y − ȳ)².
- **Why we used it here:** RMSE is the plan's selection metric. The others show typical errors (MAE), worst cases (max, p95) and safety (signed error).
- **Where in our code:** `src/modelling.py → regression_metrics()`.
- **Common confusion / trap:**
  - R² looks impressive (0.946) even when the error in °C is meaningful. Always quote RMSE/MAE in °C too.
  - RMSE ≥ MAE always; a big gap between them means a few large errors.

### Residuals
- **In one line:** the error of each single prediction, predicted − actual.
- **Explained simply:** Looking at all residuals together tells you more than one average: are they centred on 0 (no bias)? Are big ones rare? Do they grow at high temperatures? Our MLP's residuals are centred slightly below 0 (−1.95 °C) and grow above 90 °C (MAE 7.5–7.8 °C, mean −6.2 to −6.6 °C), so it under-predicts when hot.
- **Formula (if any):** rᵢ = ŷᵢ − yᵢ.
- **Why we used it here:** `eval_07_residual_histogram.png`, `eval_09_error_by_temperature.png`, and the error panels under each session plot.
- **Where in our code:** `notebooks/05_evaluation.ipynb` sections 5–9.
- **Common confusion / trap:** some books define the residual as actual − predicted (the opposite sign). We always use predicted − actual, so **negative = under-prediction**.

### Generalisation gap
- **In one line:** the difference between the score a model got during development (CV) and its score on truly new data (test).
- **Explained simply:** If a student scores 90 % on mock exams but 75 % in the real exam, the gap shows how much the mocks over-promised. Our gaps are: MLP +1.086 °C (4.919 → 6.005), LightGBM +0.044, Ridge −0.205. A model whose CV advantage was smaller than the fold noise can easily lose on a small test set of 6 sessions.
- **Formula (if any):** gap = test RMSE − CV RMSE.
- **Why we used it here:** plan Phase 5 interpretation; `eval_12_cv_vs_test.png`.
- **Where in our code:** `notebooks/05_evaluation.ipynb` section 11.
- **Common confusion / trap:** a negative gap (test better than CV) is possible and not suspicious when the test set is small. It just means those 6 sessions happened to be a bit easier for that model.

### Permutation importance (single and grouped)
- **In one line:** how much the error grows when you randomly shuffle one input column, breaking its link to the target.
- **Explained simply:** If the model really relies on coolant temperature, scrambling the coolant column should make its predictions much worse. If shuffling an input changes nothing, the model wasn't using it. Our features come in correlated families (e.g. current and its 4 EWMAs). Shuffling one member hurts little because its siblings still carry the information, so we also shuffle **whole families at once**. Grouped result for our MLP (RMSE increase in °C): coolant 19.67, voltage 16.11, speed 15.40, current 11.32, power 8.96, torque 2.45, ambient 0.52.
- **Formula (if any):** importance = RMSE(shuffled) − RMSE(original), averaged over 3 shuffles.
- **Why we used it here:** the physics sanity check (plan N7). The ranking makes physical sense.
- **Where in our code:** `notebooks/05_evaluation.ipynb` section 10 → `permutation_importance*.csv`, `eval_11_permutation_importance.png`.
- **Common confusion / trap:**
  - Importance is **not** causation.
  - Shuffling can create impossible input combinations, so the exact values are rough.
  - We computed it after the one test evaluation, as interpretation only; nothing was changed because of it.

### One-standard-error rule (a lesson from our project)
- **In one line:** among models whose CV score is within one standard deviation of the best, choose the simplest.
- **Explained simply:** If two models' CV scores differ by less than the natural noise between folds, the data can't really tell them apart, so prefer the simpler, cheaper, more explainable one. Our top five models were within 0.3 °C, while their fold std was 0.58–0.84 °C. This rule would have chosen **Ridge**, which then did best on the test set (4.966 °C). We had not decided on it in advance, so we did not switch after seeing the test results.
- **Formula (if any):** choose the simplest model with CV RMSE ≤ best CV RMSE + its std.
- **Why we used it here:** a lesson learned, and the recommended rule for future work.
- **Where in our code:** `LOG.md` Phases 4.3 and 5.1.
- **Common confusion / trap:** applying such a rule *after* seeing test results is cheating. It must be fixed before the test set is opened.

## Innovation

### Ablation study
- **In one line:** remove one ingredient at a time, keeping everything else the same, and measure how much worse the model gets.
- **Explained simply:** It's like testing a recipe by baking it again without the sugar, then without the eggs. If the cake gets much worse without an ingredient, that ingredient matters. We kept the **same model (the final MLP), the same rows and the same 5 session-folds**, and only changed the inputs. Removing the EWMA memory raised the CV RMSE from 4.92 to 13.18 °C. Removing the physics features raised it to 6.56 °C. Removing torque changed almost nothing (4.81 °C). Adding the forbidden temperatures dropped it to 1.15 °C, which proves they are a cheat.
- **Formula (if any):** effect of an idea = CV RMSE without it − CV RMSE of the full model.
- **Why we used it here:** innovation I1. It turns "we think EWMA helps" into a measured number.
- **Where in our code:** `notebooks/06_innovation.ipynb` section 2 → `outputs/results/ablation.csv`, `innov_01_ablation.png`.
- **Common confusion / trap:** an ablation must change only ONE thing. If the folds, rows or settings also changed, you couldn't tell what caused the difference.

### Safety margin and alarm (recall, false alarms, precision)
- **In one line:** raise an overheating alarm when the estimate **plus a safety margin** passes a threshold, so fewer real overheating moments are missed.
- **Explained simply:** Our model sometimes reads too low when the motor is hot. If the protection only trusts the raw estimate, it can miss real overheating. Adding k × σ (σ = the typical error, measured on the training sessions) to the estimate before comparing with the threshold catches more hot moments, at the price of more false alarms. We report three numbers:
  - **caught (recall):** of the truly hot moments, how many raised the alarm;
  - **false-alarm rate:** of the not-hot moments, how many raised it anyway;
  - **precision:** of all alarms, how many were real.
- **Formula (if any):** alarm if ŷ + k·σ ≥ T_hot; recall = TP/(TP+FN); false-alarm rate = FP/(FP+TN); precision = TP/(TP+FP).
- **Why we used it here:** innovation I3, plan nuance N8: under-prediction is the dangerous direction.
- **Where in our code:** `notebooks/06_innovation.ipynb` section 4 → `safety_alarm.csv`, `innov_03_safety_alarm.png`; the margin slider in `app.py`.
- **Common confusion / trap:** σ must come from data the model didn't train on. We used out-of-fold errors from cross-validation, never the test set and never training-fit errors (those are far too small).

### Data-efficiency (learning) curve
- **In one line:** how the error changes when the model is trained on less and less data.
- **Explained simply:** We trained the final model on 25 %, 50 %, 75 % and 100 % of the development sessions and scored it on a fixed set of validation sessions. If the error is still falling at 100 %, more test-bench sessions would help; if it is flat, more data of the same kind won't. Ours: 9.56 °C (12 sessions), 6.36 °C (25), 5.18 °C (38), 4.66 °C (50). It is still falling, so **more sessions would still help**.
- **Formula (if any):** —
- **Why we used it here:** innovation I4. It tells GE how much data a new motor would need.
- **Where in our code:** `notebooks/06_innovation.ipynb` section 6 → `data_efficiency.csv`, `innov_04_data_efficiency.png`.
- **Common confusion / trap:** with few sessions the result depends a lot on *which* sessions were picked. That's why the smaller fractions are repeated 3 times with different random picks and averaged.
