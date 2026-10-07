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
**A:** They are temperatures measured right next to the target. A real motor wouldn't have them, so using them is data leakage and makes the task trivial. With them included our R² was `<our number>`.

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
**A:** An Exponentially Weighted Moving Average: an average of past values in which recent values count more. Temperature depends on recent load history (thermal inertia), so EWMA gives the model "memory". It improved RMSE from `<our number>` to `<our number>` °C.

**Q:** Why did you add i² as a feature?
**A:** Copper loss = I²R is the main source of heat in the winding, so i² relates to heating more directly than i does.

**Q:** Why compute the EWMA separately for each profile?
**A:** Otherwise, at the boundary between two sessions, the average would mix data from a different session.

## Models

**Q:** Why start with Linear Regression?
**A:** It's a simple, interpretable baseline. It shows how much the complex models actually add.

**Q:** Why don't tree models need feature scaling?
**A:** They split on thresholds of one feature at a time. Scaling doesn't change the order of the values, so the splits stay the same.

## Evaluation

**Q:** RMSE vs MAE?
**A:** Both are in °C. MAE is the average size of the error. RMSE punishes big errors more, because errors are squared before averaging.

**Q:** What does R² mean?
**A:** The fraction of the target's variation that the model explains: 1 = perfect, 0 = no better than always predicting the mean.

**Q:** Why is under-prediction worse than over-prediction here?
**A:** If the model says "cool" while the motor is actually overheating, no protective action is taken and the insulation gets damaged.

## Team & process

**Q:** How did you divide the work, and what was your own contribution?
**A:** By pipeline stage. Arnav did setup, the data check and the problem definition; B did EDA; C did pre-processing and features; D did the models; E did evaluation and the safety alarm. The next stage's owner reviewed each stage, and everyone read the full log, so anyone can answer for any stage. (Each member: say your own stage first, with one real number from it.)

## Innovation
<!-- ablation study, safety margin & alert, data-efficiency curve, demo app -->
