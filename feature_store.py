import numpy as np
from ratings import EloRatings

def make_pre_match_features(history, home, away, cutoff):
    h=history[history.Date<cutoff]
    elo=EloRatings().fit(h)
    teams=set(h.HomeTeam)|set(h.AwayTeam)
    def avg(team, col, default):
        rows=[]
        for r in h.itertuples():
            if r.HomeTeam==team: rows.append(getattr(r,col) if col in {"FTHG","FTAG"} else 0)
            elif r.AwayTeam==team: rows.append(getattr(r,col) if col in {"FTHG","FTAG"} else 0)
        return float(np.mean(rows[-10:])) if rows else default
    return np.array([
        elo.predict_diff(home,away),
        avg(home,"FTHG",1.2),
        avg(home,"FTAG",1.2),
        avg(away,"FTHG",1.2),
        avg(away,"FTAG",1.2),
        len(h)
    ],dtype=float)
