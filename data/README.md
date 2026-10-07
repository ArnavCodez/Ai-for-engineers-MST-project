# Data: where it comes from and how to get it

Everything in `data/` is git-ignored except this file. Every teammate downloads the data themselves.

## Source
- **Dataset:** "Electric Motor Temperature" by wkirgsn (Wilhelm Kirchgässner, Paderborn University, LEA department), on Kaggle: https://www.kaggle.com/datasets/wkirgsn/electric-motor-temperature
- **Version we use:** Kaggle dataset **version 3**, downloaded 2026-10-07 with `kagglehub`.
- **File:** `measures_v2.csv`, 300.1 MB (300,061,411 bytes).
- **SHA-256:** `78f3d150f0f2ad9c5dc7ff24dd12c00d386ad530f48c1589ad24fcd88867d3ad`
  Check yours on Windows with `certutil -hashfile data\raw\measures_v2.csv SHA256`. If it differs, you have a different version: tell the team before running anything.
- **What it is:** a three-phase 50 kW PMSM on a test bench, sampled at 2 Hz. Our check (notebook 01) found 1,330,816 rows, 69 sessions (`profile_id`) and 184.84 h.
- **Paper describing the test bench:** W. Kirchgässner, O. Wallscheid, J. Böcker, "Data-Driven Permanent Magnet Temperature Estimation in Synchronous Motors with Supervised Machine Learning: A Benchmark", IEEE Trans. Energy Conversion, 2021, arXiv:2001.06246.
- **Licence / redistribution:** read the terms on the Kaggle page before sharing the raw file anywhere. We don't commit it to git.
- **GE note:** GE Power Systems is only the assignment's scenario. This is not GE data.

## How to get it
From the repo root, with the venv active:
```
python src\download_data.py
```
This downloads the public dataset without a Kaggle login and copies `measures_v2.csv` into `data/raw/`. Then run `notebooks/01_data_check.ipynb` to create `data/processed/measures_v2.parquet`.

## Folders
- `data/raw/`: the original CSV. **Never edit it.**
- `data/processed/`: files made by our notebooks (parquet copies, features). They can always be recreated.

The test/train session split is **not** here. It lives in `outputs/results/split_profiles.json`, which is committed, so everyone uses exactly the same split.
