# GoalPredict AI Pro — Sportmonks automatic mode

This version replaces the manual historical CSV requirement with automatic Sportmonks retrieval for the two competitions available on the current free Football API plan:

- Danish Superliga (league 271)
- Scottish Premiership (league 501)

The app discovers the current/recent seasons, downloads completed fixtures and upcoming fixtures, and builds a pre-match Dixon–Coles/rolling-form prediction. If xG is available to the account, it is blended into the rolling team estimates; if xG is not included in the plan, the model automatically falls back to goals.

## Streamlit Secrets

```toml
SPORTMONKS_TOKEN = "your_token_here"
```

Never commit the token to GitHub.

## Deploy

Replace your repository's `app.py`, `api_client.py`, `engine.py`, and add `sportmonks_data.py`. Keep the existing `requirements.txt` and security modules. Then redeploy/reboot the Streamlit app.
