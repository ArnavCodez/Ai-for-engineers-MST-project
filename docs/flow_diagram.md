# Project flow diagram

The instructions require a flow diagram with the pre-processing and visualisation steps clearly documented. The PNG export is `docs/flow_diagram.png`.

```mermaid
%%{init: {"flowchart": {"wrappingWidth": 340, "nodeSpacing": 28, "rankSpacing": 46}, "themeVariables": {"fontSize": "15px"}}}%%
flowchart LR
    subgraph S1["1 · DATA"]
        direction TB
        A["<b>Data source</b><br/>Kaggle 'Electric Motor Temperature' v3<br/>Paderborn 50 kW PMSM test bench<br/>1,330,816 rows · 69 sessions · 2 Hz"]
        B["<b>Data check</b> (nb 01)<br/>0 missing · 0 duplicates · ranges plausible<br/>row order = time order<br/>(median step 0.022 °C vs 28.85 °C shuffled)<br/>float32 + parquet copy"]
        C["<b>Freeze test sessions</b> (nb 02)<br/>2 per length tertile, seed 42<br/>test = 6, 7, 21, 61, 66, 81 (10.60 %)<br/>locked until the final evaluation"]
        A --> B --> C
    end
    subgraph S2["2 · VISUALISATION & PRE-PROCESSING"]
        direction TB
        D["<b>EDA on 63 training sessions</b> (nb 02)<br/>1 session lengths · 2 one session over time<br/>3 histograms · 4 correlation heatmap<br/>5 hexbins vs current / coolant<br/>6 operating region · 7 per-session boxplots<br/>8 thermal lag"]
        E["<b>Cleaning</b> (nb 03)<br/>none needed (re-checked in code)<br/>keep row order and plausible odd readings"]
        F["<b>Feature engineering</b> (nb 03)<br/>physics: i_s, u_s, i_s², p_el, p_mech<br/>EWMA memory: 8 signals × 1/5/15/45 min<br/>per session, past only → 45 inputs<br/>forbidden pm / tooth / yoke excluded"]
        G["<b>Scaling</b><br/>StandardScaler inside a Pipeline<br/>(linear models and MLP; trees need none)"]
        D --> E --> F --> G
        D -. "lag of minutes → EWMA" .-> F
    end
    subgraph S3["3 · MODELLING"]
        direction TB
        H["<b>Models</b> (nb 04)<br/>B0 mean · B1 coolant + offset<br/>Linear (raw / 45) · Ridge · Lasso<br/>Random Forest · LightGBM · MLP"]
        I["<b>CV tuning</b><br/>GroupKFold(5) by session<br/>every 10th training row<br/>RMSE mean ± std · no random early stopping"]
        J["<b>Final models</b><br/>finalists retrained on all training sessions<br/>saved with metadata · success target set"]
        H --> I --> J
    end
    subgraph S4["4 · EVALUATION & INNOVATION"]
        direction TB
        K["<b>Test evaluation, once</b> (nb 05)<br/>RMSE · MAE · R² · max / p95 · signed error<br/>per-session metrics · predicted vs actual"]
        L["<b>Interpretation</b> (nb 05)<br/>error vs temperature and session time<br/>permutation importance · under-prediction"]
        M["<b>Innovation</b> (nb 06, app.py)<br/>I1 ablation · I2 memory curve<br/>I3 safety alarm (margin kσ)<br/>I4 data efficiency · I5 Streamlit replay"]
        K --> L --> M
    end
    S1 --> S2 --> S3 --> S4
```
