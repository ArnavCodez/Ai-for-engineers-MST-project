"""Download measures_v2.csv from Kaggle into data/raw/.

Run from the project folder (MST_Motor_Temperature):
    .venv\\Scripts\\python src\\download_data.py

The dataset is public, so kagglehub can download it without a Kaggle login.
If Kaggle ever asks for a login, download the zip in the browser from
https://www.kaggle.com/datasets/wkirgsn/electric-motor-temperature
and put measures_v2.csv in data/raw/ by hand.
"""
import shutil
from pathlib import Path

import kagglehub

DATASET = "wkirgsn/electric-motor-temperature"
FILE_NAME = "measures_v2.csv"

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"


def download_measures():
    target = RAW_DIR / FILE_NAME
    if target.exists():
        print("Already downloaded:", target)
        return target

    # kagglehub saves into its own cache folder and returns that folder's path
    cache_dir = Path(kagglehub.dataset_download(DATASET))
    print("Downloaded to cache:", cache_dir)
    print("Files in the dataset:", [p.name for p in cache_dir.iterdir()])

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cache_dir / FILE_NAME, target)
    print("Copied to:", target)
    return target


if __name__ == "__main__":
    path = download_measures()
    size_mb = path.stat().st_size / 1e6
    print(f"Size: {size_mb:.1f} MB")
