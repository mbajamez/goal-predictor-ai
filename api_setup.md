# Licensed live API integration

This project uses **Sportmonks Football API** as the live-data adapter.

Sportmonks currently documents:
- fixtures/live scores
- lineups and player profiles
- xG/xGA metrics
- player-level xG
- injuries/suspensions via `sidelined`
- historical team/player statistics
- team/player ratings and related data

Official references:
- https://www.sportmonks.com/football-api/
- https://www.sportmonks.com/football-api/xg-data/
- https://www.sportmonks.com/glossary/injuries-and-suspensions/

## Configure

Linux/macOS:
```bash
export SPORTMONKS_TOKEN="YOUR_LICENSED_TOKEN"
```

Windows PowerShell:
```powershell
$env:SPORTMONKS_TOKEN="YOUR_LICENSED_TOKEN"
```

Never commit the token to Git or put it directly in Python source.

## Data flow

1. Scheduled worker pulls fixtures.
2. Historical completed fixtures feed the training store.
3. Pre-match xG and player availability are captured only before kickoff.
4. Elo/team ratings are updated chronologically.
5. Dixon-Coles produces a scoreline distribution.
6. Gradient boosting uses pre-match features.
7. A meta-model blends the base predictions.
8. Calibration is fitted on out-of-fold historical predictions.
9. The dashboard exposes the final calibrated probability and model version.

## Critical leakage rule

Do not train a pre-match prediction using:
- final-match xG
- post-match player ratings
- events occurring after kickoff
- future injury status
- future fixtures
- bookmaker closing prices if the intended prediction timestamp is earlier than market close

Store `observed_at` and `prediction_cutoff` timestamps for every feature.
