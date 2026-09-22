# GoalPredict AI Pro

Production-oriented football goal prediction starter with:

- real historical football-data.co.uk results/match statistics downloader
- optional xG/xGA data ingestion
- chronological walk-forward validation
- Dixon-Coles low-score correction
- Poisson goal distributions
- isotonic calibration for Over 1.5 probabilities
- Brier score, log loss, calibration error and MAE
- leakage-safe rolling team features
- Streamlit prediction dashboard

## Important data note

Football-Data.co.uk provides extensive historical results and match statistics, but its standard CSV files do **not** provide a universal xG field. The app therefore treats xG as an optional external dataset. Supply an xG CSV with:

`Date,HomeTeam,AwayTeam,HomeXG,AwayXG`

The xG rows must refer to information available before prediction time. Do not upload post-match xG to a prediction row.

Football-Data's website says its historical results go back decades and match statistics are available for many major leagues. It also states that its free data is intended for private individuals rather than commercial automated AI/data-training products. Check the current terms before commercial deployment.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt

python scripts/download_football_data.py --league E0 --start 2015 --end 2026
python scripts/build_dataset.py --input data/raw --output data/matches.csv

# Optional xG:
# Put an xG CSV at data/xg.csv with Date,HomeTeam,AwayTeam,HomeXG,AwayXG
python scripts/build_dataset.py --input data/raw --xg data/xg.csv --output data/matches.csv

python walk_forward.py --input data/matches.csv --output models/walk_forward.csv

streamlit run app.py
```

## Model design

The prediction engine estimates home and away goal rates using:

- exponentially weighted historical goals
- opponent-adjusted attack/defence strength
- home advantage
- pre-match xG/xGA when available
- Dixon-Coles tau correction for 0-0, 1-0, 0-1 and 1-1

The total-goal probability is obtained by summing the scoreline distribution.

## Validation

The walk-forward validator trains only on matches strictly before each test match. It never randomly shuffles football matches.

Reported metrics include:

- Brier score for Over 1.5
- log loss
- calibration error
- goal MAE
- baseline comparison

Calibration is fit only on predictions that occurred before the current evaluation period.

## Security

- input allow-lists
- file-size/type checks
- no shell execution from user input
- no API secrets in source code
- no arbitrary URL fetching from the UI
- model artifacts stored locally
- data schema validation
- prediction audit metadata

This is probabilistic software. It cannot guarantee match outcomes or profits.
