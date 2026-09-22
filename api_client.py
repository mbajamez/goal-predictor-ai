import os, time, requests

class SportmonksClient:
    """Licensed live-data adapter. Put SPORTMONKS_TOKEN in the environment."""
    BASE="https://api.sportmonks.com/v3/football"

    def __init__(self, token=None, timeout=20):
        self.token=token or os.getenv("SPORTMONKS_TOKEN")
        self.timeout=timeout
        if not self.token:
            raise RuntimeError("SPORTMONKS_TOKEN is not configured.")

    def get(self, path, params=None):
        params=dict(params or {})
        headers={"Authorization": self.token}
        for attempt in range(3):
            r=requests.get(self.BASE+path,params=params,headers=headers,timeout=self.timeout)
            if r.status_code == 429:
                time.sleep(2**attempt); continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError("API rate limit did not recover.")

    def fixture(self, fixture_id):
        return self.get(f"/fixtures/{fixture_id}", {
            "include":"participants;scores;lineups.player;lineups.xGLineup;statistics.type;xgfixture.type;sidelined.player;sidelined.type"
        })

    def livescores(self):
        return self.get("/livescores", {
            "include":"participants;scores;events;statistics.type;xgfixture.type"
        })

    def team(self, team_id):
        return self.get(f"/teams/{team_id}", {"include":"players;sidelined;upcoming"})

    def player(self, player_id):
        return self.get(f"/players/{player_id}", {"include":"sidelined"})
