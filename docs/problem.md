# Problem understanding: a virtual sensor for motor winding temperature

**UCS321 MST mini project, statement #6 (GE Power Systems)** · Phase 1 · written 2026-10-07

> General Electric (GE) Power Systems aims to improve the operational reliability of its electric motors by predicting winding temperatures under diverse working conditions. Using a dataset containing parameters such as ambient temperature, motor speed, load torque, supply voltage, and current, students will develop a supervised machine learning regression model to estimate motor temperature.

## 1. The problem in one paragraph

Every electric motor has copper coils, the **stator winding**. Current flowing through them makes heat. The winding's insulation slowly breaks down when it runs hot, and if it gets too hot it fails and the motor is lost. GE wants to know the winding temperature **while the motor runs**, under all kinds of loads. Measuring it directly needs a sensor buried inside the machine, which is costly, adds wiring, and can itself fail. Our task is to build a **model that calculates the winding temperature** from signals the motor controller already measures. In other words, a *virtual sensor*.

**Being honest about the setting:**
- **GE is the scenario, not the data source.** GE Power Systems is the business scenario in the assignment. Our data is a public research dataset recorded at Paderborn University on a different motor. We report that provenance openly.
- **We estimate the temperature *now*.** We do not forecast future temperature, and we do not predict failures. Forecasting would need a future target and a different evaluation; failure prediction would need failure labels, which this data doesn't have.

## 2. Why winding temperature matters

- **Insulation ageing.** Insulation doesn't fail suddenly at one temperature. Its useful life gets shorter the hotter it runs. A common rule of thumb, the "10 °C rule", is that **life halves for every 10 °C increase**, or equally doubles for every 10 °C of unused temperature capability [1], [2].
- **Every insulation system has a thermal class** (standard IEC 60085). The class is the maximum hot-spot temperature it is designed for [1]:

  | Class | A | E | B | F | H |
  |---|---|---|---|---|---|
  | Max hot-spot temperature | 105 °C | 120 °C | 130 °C | 155 °C | 180 °C |

  The hot spot is estimated as the rated ambient (often 40 °C) + the temperature rise + a 10 °C hot-spot allowance [1]. An insulation class is rated to give an average life of about 20,000 h at its class temperature [2].
- **Overheating means failure.** Insulation breakdown leads to short circuits between turns and then motor failure. That means downtime, repair cost, and in a vehicle, a safety risk.
- **Being too careful wastes performance.** Without knowing the real temperature, engineers must **derate** the motor: run it below what it could do, "just in case". A good temperature estimate lets the motor work closer to its real limit, safely.

## 3. Why a model instead of more sensors

- A sensor in the winding costs money, needs wiring out of the machine, and can break or drift. In series production, every extra sensor is multiplied by thousands of motors.
- Sensors can't be put everywhere, and the hottest spot can move with the operating point.
- The motor controller **already measures** currents, voltages and speed for control, and the coolant and ambient temperatures are usually known. The dataset authors state that their input signals "are commonly accessible in real-world traction drive systems", so models trained on them "can be plugged into commercial vehicle controls without further sensor upgrades" [3].
- So we learn the link between these cheap signals and the winding temperature **once**, on a test bench where a real winding sensor *was* fitted. Then the model estimates the temperature on motors that have no such sensor. This is called a **virtual sensor** or **soft sensor**.

## 4. Our data in brief (all numbers from `outputs/results/data_check_summary.json`)

- Kaggle dataset `wkirgsn/electric-motor-temperature`, version 3. It was recorded by the LEA department of Paderborn University on a **three-phase, 50 kW PMSM** (permanent magnet synchronous motor) on a test bench, at 2 Hz [3].
- **1,330,816 rows** (one every 0.5 s) in **69 measurement sessions** (`profile_id`), **184.84 hours** in total. Sessions last from 0.302 h to 6.107 h.
- The winding temperature ranges from **18.59 °C to 141.36 °C**. 0 missing values and 0 duplicate rows.

## 5. Objective

**Build a supervised regression model:**

- **Output (target):** `stator_winding`, the stator winding temperature in °C. It is the "winding temperature" of the statement, and the hottest measured part in our data (max 141.36 °C, against 113.61 °C for the magnet).
- **Inputs:** the 8 measured signals, matching the statement's parameters:

  | Statement says | Column(s) | Unit |
  |---|---|---|
  | ambient temperature | `ambient` | °C |
  | motor speed | `motor_speed` | rpm |
  | load torque | `torque` | Nm |
  | supply voltage | `u_d`, `u_q` (dq components) | V |
  | current | `i_d`, `i_q` (dq components) | A |
  | (extra in our data) | `coolant` | °C |

  Plus features we engineer from them (Phase 3), such as current², power, and averages of the recent past that give the model "thermal memory".
- **Not allowed as inputs:** `pm`, `stator_tooth`, `stator_yoke`. These are temperatures measured right next to the winding. They aren't "wrong" data in general. We exclude them because our virtual-sensor assumption is that only operating and environmental signals are available, and a motor that had these sensors wouldn't need our model. Using them would quietly change the problem and make it trivial (data leakage under our assumption).
- **Not a feature:** `profile_id`. It only identifies the session, and we use it to split the data.

## 6. Success criteria

1. **Clearly beat the baselines.** These are "always predict the average" and "winding = coolant temperature + an offset" (Phase 4). The numeric target (e.g. "test RMSE below X °C") is set **after** the baselines are measured, and logged as a decision. We won't pick a number before we have data to justify it.
2. **Generalise to unseen sessions.** We judge the model only on whole sessions it never saw during training. Neighbouring rows are 0.5 s apart and almost identical, so a random split would give fake accuracy.
3. **Be safe.** Under-estimating is worse than over-estimating, because the motor could overheat while the model says "fine". We report the largest under-prediction and how often we under-predict at high temperatures.
4. **Be cheap to run.** The model should be able to run on a motor controller. If a simpler model is almost as accurate (within about 0.3 °C RMSE), we prefer it.

## 7. Who would use it

- **Motor and drive engineers** at GE: thermal protection (alarm or power reduction before overheating) and smarter derating.
- **Maintenance teams:** tracking how much thermal stress each motor has seen, which helps estimate insulation ageing.

## 8. Constraints and assumptions

- **Test-bench data, one motor.** The results apply to this 50 kW PMSM and these test conditions. A different motor or a real vehicle would need new data or at least re-checking.
- **Temperature range.** The data reaches 141.36 °C. We can't promise accuracy above roughly that, since the model has never seen hotter conditions.
- **Row order = time order** inside each session. There is no timestamp column. We tested this in Phase 0: the median row-to-row change is 0.022 °C in file order vs 28.85 °C when shuffled.
- **Torque.** In real vehicles torque is usually estimated rather than measured, and the dataset authors' own input list does not include torque [3]. We keep it, because the statement names it, but we test the model without it (Phase 6 ablation).
- **The insulation class of the test motor is not given in the data**, so we don't claim a specific limit for it.

## Sources

1. Wikipedia, "Insulation system": IEC 60085 thermal classes, hot-spot definition, 10 °C rule of thumb. https://en.wikipedia.org/wiki/Insulation_system
2. E. Cowern, "The Hot Issue of Motor Temperature Ratings", EC&M, 1 Sept 2000: insulation life doubles per 10 °C of unused capability; class temperature tied to about 20,000 h average life. https://www.ecmweb.com/content/article/20899136/the-hot-issue-of-motor-temperature-ratings
3. W. Kirchgässner, O. Wallscheid, J. Böcker, "Data-Driven Permanent Magnet Temperature Estimation in Synchronous Motors with Supervised Machine Learning: A Benchmark", IEEE Trans. Energy Conversion, 2021 (arXiv:2001.06246): the 50 kW three-phase PMSM test bench, 2 Hz, signals available in real traction drives, input list without torque, EWMA features. https://arxiv.org/abs/2001.06246
