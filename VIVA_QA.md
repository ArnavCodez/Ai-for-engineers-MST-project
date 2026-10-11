# VIVA Q&A: MST Project (Motor Winding Temperature)

Grouped by phase. Add questions as you go, and replace the `<our number>` placeholders with real results once we have them.
**Mock viva:** pair up and quiz each other with 10 random questions from this file, one at a time; the quizzer grades the answers against the A: lines.

## Problem & motivation

**Q:** What is a PMSM?
**A:** A Permanent Magnet Synchronous Motor. Its rotor has permanent magnets, and its stator windings carry 3-phase AC. It's used in EVs because it is efficient and power-dense.

**Q:** Why predict the winding temperature instead of just measuring it?
**A:** Sensors add cost and wiring, and they can fail. A model (a "virtual sensor") uses signals the motor controller already has: currents, voltages, speed and coolant temperature.

**Q:** Explain your problem statement in simple words.
**A:** GE wants to know how hot the copper winding inside a motor is, without fitting a sensor there. We train a model on test-bench recordings where a real sensor *was* fitted, so it learns to estimate the winding temperature from signals the controller already has: ambient and coolant temperature, voltages, currents, speed and torque. That's a "virtual sensor".

**Q:** What does "supervised regression" mean in your project?
**A:** Supervised: every training row has the true answer, the measured winding temperature. Regression: the answer is a number in °C, not a category. So the model learns inputs → a temperature number.

**Q:** Which dataset columns match the parameters named in the statement?
**A:** Ambient temperature → `ambient`; motor speed → `motor_speed`; load torque → `torque`; supply voltage → `u_d`, `u_q`; current → `i_d`, `i_q`. Our data adds `coolant`. The temperature we estimate is `stator_winding`.

**Q:** The statement says "motor temperature". Why did you pick the winding?
**A:** The statement itself says "winding temperatures", and in our data the winding is the hottest measured part: up to 141.36 °C, against 113.61 °C for the magnet, 111.95 °C for the stator tooth and 101.15 °C for the yoke. So it's the part most at risk.

**Q:** Why does winding temperature matter?
**A:** Insulation ages much faster when hot. Going above its class limit (e.g. Class F = 155 °C) causes insulation failure and motor breakdown.

**Q:** What is an insulation class? Name a few.
**A:** A grade from standard IEC 60085 for the maximum hot-spot temperature the winding insulation is designed for: A 105 °C, E 120 °C, B 130 °C, F 155 °C, H 180 °C. Our hottest winding reading, 141.36 °C, is below Class F.

**Q:** What is the 10 °C rule?
**A:** A rule of thumb that insulation life halves for every 10 °C hotter it runs, and doubles for every 10 °C cooler. So even a few degrees of estimation error matter.

**Q:** What is derating, and how does your model help?
**A:** Running a motor below its capability "just in case", because the real temperature is unknown. A trustworthy estimate lets engineers use more of the motor's capability without risking overheating.

**Q:** Why can a model replace a sensor here? What makes the inputs realistic?
**A:** All our inputs (currents, voltages, speed, coolant and ambient temperature) are signals a motor controller already has. The dataset authors say such models can be plugged into vehicle controls "without further sensor upgrades".

**Q:** What motor is your data from?
**A:** A three-phase 50 kW PMSM on a test bench at Paderborn University (LEA department), sampled at 2 Hz. The version we used has 69 sessions and 184.84 hours.

**Q:** Who would use your model?
**A:** Motor and drive engineers, for thermal protection and smarter derating. Maintenance teams, for tracking each motor's thermal stress and insulation ageing.

**Q:** What are the limits of your project?
**A:** It's one motor on a test bench, so a real vehicle or another motor would need re-checking. The data only goes up to 141.36 °C, so we can't promise accuracy above that. And we assume file order is time order (tested in Phase 0).

**Q:** Why didn't you fix an accuracy target at the start?
**A:** Any number picked before seeing the data would be a guess. We set the target after measuring the baselines (always-average, and coolant + offset) in Phase 4, then log it as a decision.

**Q:** Torque is in the statement. Is it a fair input?
**A:** In real vehicles torque is usually estimated, not measured, and the dataset authors left it out of their input list. We keep it because the statement names it, but our ablation (Phase 6) also tests the model without torque.

## Data

**Q:** Where is your data from?
**A:** The Kaggle dataset `wkirgsn/electric-motor-temperature` (version 3), from Paderborn University's PMSM test bench. Measured by us: 1,330,816 rows at 2 Hz in 69 sessions (`profile_id`), 184.84 hours in total.

**Q:** How would a teammate get exactly the same data?
**A:** Run `src/download_data.py`. It downloads version 3 of the Kaggle dataset with kagglehub (no login needed) and copies the 300.1 MB `measures_v2.csv` into `data/raw/`.

**Q:** What is one row, and what is a profile?
**A:** One row is one moment: all 13 values measured together, 0.5 s after the previous row (2 Hz). A profile (`profile_id`) is one test session on the bench. We have 69, from 0.302 h to 6.107 h long (median 2.381 h).

**Q:** What does 2 Hz mean for your data?
**A:** Two rows per second, so hours = rows ÷ 2 ÷ 3600. That's how 1,330,816 rows become 184.84 hours.

**Q:** Did your data need cleaning?
**A:** No rows were removed. We found 0 missing values and 0 duplicate rows in 1,330,816, and every temperature was inside our plausible range of −20…200 °C (winding: 18.59–141.36 °C).

**Q:** There is no timestamp. How do you know the rows are in time order?
**A:** Each session is one unbroken block of rows (69 blocks for 69 sessions). The winding temperature changes by a median of only 0.022 °C between neighbouring rows, against 28.85 °C if the rows are shuffled, which only happens for consecutive moments. And sessions start at room temperature, as real runs do.

**Q:** Why are the session lengths important?
**A:** They range from 0.302 h to 6.107 h, so an average over all rows is dominated by the long sessions. That's why we will split by whole sessions and also report errors per session.

**Q:** What are i_d and i_q?
**A:** The current split into two parts in a frame that rotates with the rotor (the Park/dq transform). i_q mainly produces torque; i_d mainly controls the magnetic flux.

**Q:** Why is i_d almost always negative in your data?
**A:** Its maximum is only 0.052 A. Motor controllers push a negative d-current to weaken the magnet's field, so the motor can reach high speeds without the voltage running out. This is called field weakening. It's physics, not an error.

**Q:** Your data has negative torque and negative speed. Are those errors?
**A:** No. Negative torque (33.58 % of rows) means the motor is braking, acting as a generator, or idling near 0 Nm with sensor noise: the 25th percentile is only −0.137 Nm. Negative speed (6.56 % of rows, down to −275.5 rpm) means turning the other way. Both are real operating points.

**Q:** What is the highest winding temperature in the data, and why does it matter?
**A:** 141.36 °C, below the Class F insulation limit (155 °C). Our model can only be trusted up to roughly the temperatures it has seen, so we can't claim accuracy above about 141 °C.

**Q:** Why did you convert the CSV to parquet and float32?
**A:** The 300.1 MB CSV became a 72.2 MB parquet that loads in under 2 s instead of 8–10 s. float32 cut RAM from 138.4 to 74.5 MB, and the biggest error it added was 0.000244 rpm, far below what any sensor can measure.

**Q:** Why use a virtual environment with pinned versions?
**A:** The venv keeps this project's libraries separate. The pinned `requirements.txt` (e.g. `pandas==3.0.6`) makes every teammate install the same versions, so the same code gives the same numbers. We used Python 3.11.14.

**Q:** Why isn't the dataset in your git repo?
**A:** It's 300 MB, and anyone can re-download it with one script. Git is for code and small results; GitHub also blocks files over 100 MB.

**Q:** Why did you drop pm, stator_tooth and stator_yoke?
**A:** They are temperatures measured right next to the target. A real motor wouldn't have them, so using them is data leakage and makes the task trivial. In our ablation (same MLP, same CV folds), adding them dropped the CV RMSE from 4.92 °C to 1.15 °C. That looks fantastic, but it's cheating.

## EDA (Phase 2)

**Q:** Why did you choose the test sessions before doing EDA?
**A:** So nothing we saw while exploring could influence our features or models. The test set must stay an unseen "final exam". We froze sessions 6, 7, 21, 61, 66, 81 (10.60 % of rows) first, and all EDA used the 63 training sessions only.

**Q:** How were the test sessions chosen?
**A:** Two random sessions from each length group (short, medium, long) with seed 42. We accepted the draw only if it covered 10–15 % of rows and included one hot and one cool session. The first draw passed.

**Q:** Isn't checking how hot the test sessions get a form of peeking?
**A:** We only used each test session's maximum temperature, to make sure the exam includes hot conditions. That's stratification. We never plotted their signals or trained anything on them.

**Q:** What does your correlation heatmap show?
**A:** The forbidden temperatures correlate 0.970 (tooth), 0.862 (yoke) and 0.796 (magnet) with the winding, which proves they'd leak. The best allowed input only reaches |r| = 0.632 (i_d), so no single signal is enough.

**Q:** i_d has r = −0.632 with the winding. Does negative current cool the motor?
**A:** No. Correlation isn't causation. High speeds need negative i_d (field weakening, r = −0.68 with speed), and high speeds go with hotter windings. Speed links the two.

**Q:** Why is torque's correlation with temperature so low (0.105)?
**A:** Torque is positive when motoring and negative when braking, but both heat the winding, so the signs cancel in a straight-line correlation. Current magnitude i_s gives r = 0.583. Also, torque ≈ i_q (r = 0.9965).

**Q:** Why hexbin plots instead of scatter plots?
**A:** With about 1.2 million points a scatter plot becomes a solid blob. Hexbin colours each hexagon by how many points it holds (log scale), so we can see where the data really is.

**Q:** What is thermal lag, and how did you measure it?
**A:** The winding temperature reacts to current with a delay, because heat takes time to build up. We correlated current²(t) with temperature(t + lag) for lags of 0–60 min in each training session. The best lag had a median of 2.5 min, and r rose from 0.645 to 0.746.

**Q:** Why does that matter for your model?
**A:** It shows that the *recent past* of the current matters, not just this instant. So in Phase 3 we add EWMA features, averages over the last 1, 5, 15 and 45 minutes.

**Q:** Can the winding be colder than the coolant?
**A:** Yes, in 4.75 % of training rows (down to −29.66 °C). When the coolant is heated quickly, the winding lags behind it. So the coolant's history matters as well.

**Q:** What does the operating-region plot show?
**A:** The data covers the motor's whole torque–speed envelope (high torque at low speed, a falling limit at high speed), and hot and cool points are mixed everywhere. Median winding temperature rises with speed: 49.05 °C below 1000 rpm, 82.92 °C above 3000 rpm.

**Q:** Did you remove any outliers?
**A:** No. Only 5 ambient readings were below 15 °C (sessions 44 and 68), plus one 1.39 °C jump (session 65). They're plausible, and deleting rows would break the 0.5 s time spacing the memory features rely on.

**Q:** Why are the boxplots drawn without outlier dots?
**A:** Each session has about 19,000 readings, so the dots would cover the plot. The whiskers still show the normal range (1.5 × IQR).

**Q:** What is your showcase page?
**A:** An interactive "Motor Winding Explorer" built from our EDA exports. It shows the 63 training sessions to click through, the lag curve, the correlations and the operating map. Test sessions are locked there too, and every number is read from our results file.

## Pre-processing & features

**Q:** Why not a random train/test split?
**A:** Neighbouring rows are 0.5 s apart and almost identical. A random split puts near-copies in both train and test, which gives fake high accuracy. We split by whole sessions (`profile_id`) instead.

**Q:** What is GroupKFold?
**A:** K-fold cross-validation where all the rows of one group (here, one session) always stay in the same fold, so the model is always tested on sessions it hasn't seen.

**Q:** What is EWMA and why did you use it?
**A:** An Exponentially Weighted Moving Average: an average of past values in which recent values count more. Temperature depends on recent load history (thermal inertia), so EWMA gives the model "memory". In our ablation (same MLP, same folds), removing the EWMA features raised the CV RMSE from 4.92 °C to 13.18 °C, so the memory is worth more than 8 °C of error.

**Q:** Why did you add i² as a feature?
**A:** Copper loss = I²R is the main source of heat in the winding, so i² relates to heating more directly than i does.

**Q:** Why compute the EWMA separately for each profile?
**A:** Otherwise, at the boundary between two sessions, the average would mix data from a different session.

**Q:** Which features did you engineer, and why?
**A:** Five physics features (current and voltage magnitudes, current² for I²R copper loss, electrical and mechanical power), plus 32 EWMAs (8 signals × 1, 5, 15, 45 min) for thermal memory. That's 45 inputs in total.

**Q:** How do you know your EWMA doesn't use future data?
**A:** We computed it for session 20 on only its first 10,000 rows and compared with the full-session result. The first 10,000 values were identical (difference 0.0), so each value only uses the past.

**Q:** You computed EWMA features on the test rows too. Isn't that leakage?
**A:** No. Each row's EWMA uses only its own session's past signals, exactly what a real controller would have at that moment. Nothing is fitted or averaged across rows, so no test information reaches training.

**Q:** Why spans of 1, 5, 15 and 45 minutes?
**A:** Phase 2 found the winding follows current with a delay of a few minutes and heats and cools over tens of minutes. The spans cover that range. 120 samples at 2 Hz = 1 min.

**Q:** Which feature correlates best with the winding temperature?
**A:** The 5-minute EWMA of current magnitude (r = 0.705). The raw current only reaches 0.583, and the top 5 features are all EWMAs of current.

**Q:** Why is there a 1.5 in your electrical power formula?
**A:** The dq values use the amplitude-invariant Park transform. With that convention, three-phase power is 1.5 × (u_d·i_d + u_q·i_q).

**Q:** What is the warm-up problem?
**A:** At the start of a session the EWMA has no history yet, so a 45-min average isn't meaningful for the first 45 min. That's 27.9 % of training rows, and we expect larger errors there.

**Q:** Did you clean or remove anything?
**A:** No. We re-checked in code: 0 missing values, 0 duplicates, sessions unbroken. Removing rows would also break the regular 0.5 s spacing the EWMA relies on.

## Models

**Q:** Why start with Linear Regression?
**A:** It's a simple, interpretable baseline. It shows how much the complex models actually add.

**Q:** Why don't tree models need feature scaling?
**A:** They split on thresholds of one feature at a time. Scaling doesn't change the order of the values, so the splits stay the same.

**Q:** What are your baselines and why do you need them?
**A:** B0 always predicts the training mean; B1 predicts coolant + a constant offset. Any real model must clearly beat them, otherwise it hasn't learned anything useful. Our success target is defined relative to B1.

**Q:** How did you compare models fairly?
**A:** Every model was evaluated with the same GroupKFold(5) folds (grouped by session) on the same rows (every 10th training row). The main metric was RMSE in °C, as mean ± std over the 5 folds.

**Q:** Why GroupKFold and not normal K-fold?
**A:** Normal K-fold splits rows randomly, so neighbouring 0.5 s rows (near-copies) land in both training and validation, and the score looks far too good. GroupKFold keeps whole sessions together, so every validation score is on unseen sessions.

**Q:** Why did you use only every 10th row for cross-validation?
**A:** Neighbouring rows are near-duplicates, so one row per 5 s keeps almost all the information while making slow models (Random Forest) about 10× faster. The EWMA features were computed before thinning, so they still carry the full 2 Hz history. We also measured the cost of thinning in the notebook.

**Q:** What is the difference between Ridge and Lasso?
**A:** Both add a penalty on large weights. Ridge (L2) shrinks all weights; Lasso (L1) can set weights exactly to 0, removing features. Our best Lasso (α = 0.01) dropped 11 of 45 features.

**Q:** Your Random Forest had a much lower training error than validation error. What does that mean?
**A:** Overfitting. Training RMSE was 1.78–3.01 °C, but validation RMSE on unseen sessions was 5.82–5.92 °C. Trees also cannot extrapolate beyond the training targets, which hurts on sessions unlike the training ones.

**Q:** What is the difference between Random Forest and gradient boosting?
**A:** Random Forest builds many independent trees on random samples and averages them (bagging). Boosting builds trees one after another, each correcting the previous trees' errors, scaled by a learning rate.

**Q:** Why did you turn off early stopping?
**A:** LightGBM and sklearn's MLP pick their early-stopping validation rows at random. That mixes rows from the same session and gives over-optimistic scores. We used a fixed number of trees or epochs, judged only by session-wise CV.

**Q:** What are hyperparameters? How did you tune them?
**A:** Settings chosen before training (α, depth, trees, learning rate). We tried a small set per model (6 Ridge α, 3 Lasso α, 4 Random Forest and 8 LightGBM random configurations, seed 42) and kept the best mean CV RMSE. The test set was never used for this.

**Q:** Why are errors larger at the start of some sessions?
**A:** 16 of our 63 training sessions start already warm (session 46 starts at 99.3 °C). At a session's first row the EWMA "memory" has no history, so the model can't know the motor was heated before the recording began. A real controller would run its EWMAs continuously from power-on.

## Evaluation

**Q:** RMSE vs MAE?
**A:** Both are in °C. MAE is the average size of the error. RMSE punishes big errors more, because errors are squared before averaging.

**Q:** What does R² mean?
**A:** The fraction of the target's variation that the model explains: 1 = perfect, 0 = no better than always predicting the mean.

**Q:** Why is under-prediction worse than over-prediction here?
**A:** If the model says "cool" while the motor is actually overheating, no protective action is taken and the insulation gets damaged.

**Q:** What are your final test results?
**A:** On the 6 unseen test sessions (141,024 rows), the final MLP got RMSE 6.00 °C, MAE 3.69 °C and R² 0.946, meeting both targets set beforehand (≤ 6.5 °C and ≤ 13.02 °C). The other finalists got Ridge 4.97 °C and LightGBM 5.11 °C; the coolant baseline got 24.48 °C.

**Q:** When was the test set used?
**A:** Once, at 2026-10-10 09:24:52, after the models, settings and success targets were all frozen. Nothing was changed afterwards.

**Q:** Your best CV model did worst of the finalists on the test set. Why? Did you switch?
**A:** The top models were within 0.3 °C in CV, less than the fold-to-fold noise (0.58–0.84 °C), so CV couldn't really rank them, and one hard test session (6) hurt the MLP most. We did not switch: choosing a model after seeing test scores turns the test set into training data. Next time we'd pre-register a "simplest within one std" rule, which would have picked Ridge.

**Q:** What does an MAE of 3.69 °C mean?
**A:** On average the estimate is 3.69 °C away from the real winding temperature. 54.5 % of predictions are within ±2 °C and 75.6 % within ±5 °C, but rare large errors exist (max 60.31 °C).

**Q:** Where does your model fail?
**A:** In the first minutes of a session: a cold motor that starts under heavy load looks hot to the memory features (up to +60.31 °C error, session 21). And when hot (above 90 °C), where the MLP under-predicts by about 6 °C on average; session 6, with high coolant under load, was worst (RMSE 9.43 °C).

**Q:** Why does the session start cause errors?
**A:** pandas' EWMA starts each session at the current value, so the 15 and 45-minute memories behave as if the load had been running that long. A real controller would run its EWMAs continuously from power-on, so this is mostly an artefact of how the recordings were cut.

**Q:** How often does the model dangerously under-predict?
**A:** Of hot moments (≥ 104.79 °C, 10.3 % of test rows), the MLP under-predicts by more than 5 °C in 52.0 % of them (LightGBM 27.0 %). Its largest under-prediction was −22.03 °C. That's why we add a safety margin in Phase 6.

**Q:** Which inputs matter most? Is that physically sensible?
**A:** Grouped permutation importance: coolant (19.67 °C RMSE increase) > voltage (16.11) > speed (15.40) > current (11.32) > power > torque (2.45) > ambient (0.52). Coolant sets the base temperature, current² is the copper loss, and speed/voltage reflect iron losses and the operating point. Torque adds little because it's nearly a copy of i_q.

**Q:** Why did you report both row-weighted MAE and session-mean MAE?
**A:** Test sessions range from 2.0 to 5.6 h, so row-weighted scores are dominated by long sessions. Session-mean MAE weighs every session equally: LightGBM is best by that measure (2.38 °C), Ridge by RMSE (4.97 °C).

**Q:** Is R² = 0.946 good?
**A:** It means 94.6 % of the temperature's variation is explained. But R² can look high even when errors in °C matter, so we always quote RMSE and MAE in °C as well, plus the worst-case and under-prediction numbers.

## Team & process

**Q:** How did you divide the work, and what was your own contribution?
**A:** By pipeline stage. Arnav did setup, the data check and the problem definition; B did EDA; C did pre-processing and features; D did the models; E did evaluation and the safety alarm. The next stage's owner reviewed each stage, and everyone read the full log, so anyone can answer for any stage. (Each member: say your own stage first, with one real number from it.)

## Innovation

**Q:** What is an ablation study, and what did yours show?
**A:** We removed one idea at a time with the same MLP, rows and folds. CV RMSE was 4.92 °C with everything; 13.18 °C without the EWMA memory; 6.56 °C without the physics features; 4.81 °C without torque; and 13.41 °C with raw signals only. So the memory features are worth more than 8 °C.

**Q:** How do you prove the forbidden temperatures are cheating?
**A:** In the ablation, adding pm, stator_tooth and stator_yoke drops the CV RMSE from 4.92 °C to 1.15 °C. That's almost perfect, because the model just copies the neighbouring sensors, which a real motor without a winding sensor wouldn't have.

**Q:** Removing torque made the model slightly better. How?
**A:** 4.81 vs 4.92 °C, which is within the fold noise (± 1.03). Torque is almost a copy of i_q (r = 0.9965), so it adds no new information. That's good news, because in real vehicles torque is usually estimated rather than measured.

**Q:** How long a memory does the model need?
**A:** About 5 minutes gives most of the gain: CV RMSE falls from 13.18 °C (no memory) to 9.17 (1 min) and 5.16 °C (1 + 5 min). The 15 and 45-min spans add only 0.24 °C more, which matches the 2.5-minute lag we found in EDA.

**Q:** How does your safety alarm work?
**A:** It raises an alarm when the estimate + k·σ ≥ 104.79 °C, where σ = 4.96 °C is the model's typical error measured on training sessions (out-of-fold), never on the test. With k = 2 it catches 70.0 % of hot moments (57.2 % with no margin) at 5.84 % false alarms (0.70 % with no margin).

**Q:** Why not just make the margin huge?
**A:** False alarms grow fast: precision falls from 90.4 % (k = 0) to 57.9 % (k = 2). An alarm that cries wolf gets ignored or derates the motor needlessly. It's a trade-off engineers must choose, and even k = 2 still misses 30 % of hot moments.

**Q:** Why take σ from out-of-fold errors and not from training errors?
**A:** Errors on rows the model trained on are far too small (e.g. LightGBM's training RMSE is 1.14 vs 5.06 °C in validation). Out-of-fold errors come from sessions the model hadn't seen, so they reflect real use, and they don't touch the test set.

**Q:** Would more data help?
**A:** Yes. Training on 12 → 25 → 38 → 50 sessions gave validation RMSE 9.56 → 6.36 → 5.18 → 4.66 °C, still falling. Recording more varied sessions is the cheapest improvement.

**Q:** How big is the session-start problem?
**A:** The first 5 minutes of each test session are only 2.55 % of rows, but the MLP's error there is 12.34 °C vs 3.47 °C afterwards (mostly over-prediction, +12.04 °C). A real controller would keep its EWMA running from power-on, or initialise it from a known idle state.

**Q:** Is your demo real-time?
**A:** It's a recorded-data replay. The Streamlit app feeds a held-out test session through the saved model minute by minute, showing the estimate, the real sensor value for comparison, and an alarm lamp. No physical motor is connected.

**Q:** Walk us through your flow diagram.
**A:** Data check → freeze 6 test sessions → EDA on 63 training sessions (8 plots) → no cleaning needed → physics + EWMA features → scaling inside a Pipeline → 9 models with session-wise CV → finalists → one test evaluation → interpretation → innovation.
