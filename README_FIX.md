# GoalPredict AI — Sportmonks endpoint fix

This build fixes a common Sportmonks 404 encountered on `/fixtures/seasons/{season_id}` by using the canonical `/fixtures` endpoint with the documented `fixtureSeasons:{season_id}` filter, with the older route retained as a fallback.

It also authenticates using the `Authorization` header so the API token is not included in request URLs/error messages.

## IMPORTANT: rotate the exposed token
If your Streamlit error page showed the full `api_token=...` URL, treat that token as compromised. Delete/revoke that token in MySportmonks, create a new token, and update the Streamlit Secret `SPORTMONKS_TOKEN`.

Do not paste the token into chat, GitHub, screenshots, or source files.
