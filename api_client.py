import os, time, requests

class SportmonksClient:
    def __init__(self, token=None, timeout=20):
        self.token = token or os.getenv("SPORTMONKS_TOKEN")
        if not self.token:
            try:
                import streamlit as st
                self.token = st.secrets.get("SPORTMONKS_TOKEN")
            except Exception:
                pass
        if not self.token:
            raise RuntimeError("SPORTMONKS_TOKEN is not configured in Streamlit Secrets.")
        self.base_url = "https://api.sportmonks.com/v3/football"
        self.timeout = timeout
        self.session = requests.Session()

    def _get(self, path, params=None, retries=3):
        params = dict(params or {})
        params["api_token"] = self.token
        last = None
        for attempt in range(retries):
            try:
                r = self.session.get(
                    f"{self.base_url}/{path.lstrip('/')}",
                    params=params, timeout=self.timeout
                )
                if r.status_code == 429:
                    time.sleep(min(int(r.headers.get("Retry-After", "2")), 10))
                    continue
                r.raise_for_status()
                return r.json()
            except requests.RequestException as e:
                last = e
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"Sportmonks request failed: {last}")

    def fixture(self, fixture_id):
        return self._get(f"fixtures/{int(fixture_id)}", {
            "include": "participants;scores;lineups.player;lineups.xGLineup;statistics.type;xgfixture.type;sidelined.player;sidelined.type"
        })

    def livescores(self):
        return self._get("livescores", {"include": "participants;scores"})

    def team(self, team_id):
        return self._get(f"teams/{int(team_id)}", {"include": "statistics;latest;sidelined"})

    def player(self, player_id):
        return self._get(f"players/{int(player_id)}", {"include": "sidelined"})
