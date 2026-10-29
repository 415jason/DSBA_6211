# DSBA 6211 Group Project: Broward County Airbnb

Who wins Broward County's Airbnb market, the professional operators or independent hosts, and is it still worth getting in? Project proposal and roles are in the shared Google Drive folder.

## Setup

```
uv sync
```
Run `uv sync` again after every `git pull`: packages change (statsmodels and imbalanced-learn were added on October 29). Then download `data/processed/` (7 .parquet files) from the shared Drive folder into this repo. Data files are not in GitHub because they are too large.

## Layout

| Path | What |
|---|---|
| `notebooks/01_build_dataset.ipynb` | Builds the cleaned data (Tim). Only needed if you have the raw files |
| `notebooks/02_market_overview.ipynb` | Ch 1 (Harper) |
| `notebooks/03_reviews_text.ipynb` | Ch 3 (Matthew) |
| `notebooks/04_performance_drivers.ipynb` | Ch 2 and 4 (Jason) |
| `notebooks/05_world_cup.ipynb` | Ch 5 (Tim) |
| `notebooks/06_newcomer_feasibility.ipynb` | Ch 6 |
| `src/build_dataset.py` | Cleaning and joining code |
| `docs/data_dictionary.md` | What every file and column means. **Read this first** |
| `docs/decisions_log.md` | Every cleaning decision and why |
| `archive/` | First EDA on the June summary file (Jason) |
| `notebooks/figures/ch5/` | Figures saved by the Ch 5 notebook |
| `notebooks/cache/` | Tuned models saved by notebooks so reruns are fast (not in GitHub) |

## Working rules

1. Edit only your own notebook.
2. `git pull` before you start and again before you push.
3. Load data from `data/processed/`, never the raw files.
