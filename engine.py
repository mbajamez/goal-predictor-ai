import math
from collections import defaultdict
import numpy as np
from dixon_coles import score_matrix

class RollingGoalEngine:
    def __init__(self, decay=0.035, window=30):
        self.decay=decay
        self.window=window
        self.history=defaultdict(list)
        self.df=None

    def fit(self,df):
        self.df=df.sort_values("Date").copy()
        self.history=defaultdict(list)
        for r in self.df.itertuples():
            self.history[r.HomeTeam].append((r.Date, r.FTHG, r.FTAG, getattr(r,"HomeXG",np.nan),getattr(r,"AwayXG",np.nan),True))
            self.history[r.AwayTeam].append((r.Date, r.FTAG, r.FTHG, getattr(r,"AwayXG",np.nan),getattr(r,"HomeXG",np.nan),False))
        return self

    def _team(self,t, cutoff):
        rows=[x for x in self.history[t] if x[0] < cutoff]
        if not rows: return 1.0,1.0,1.0,1.0
        rows=rows[-self.window:]
        w=np.array([math.exp(-self.decay*(len(rows)-1-i)) for i in range(len(rows))])
        scored=np.array([x[1] for x in rows],float)
        conceded=np.array([x[2] for x in rows],float)
        xgf=np.array([x[3] for x in rows],float)
        xga=np.array([x[4] for x in rows],float)
        def ew(v, fallback):
            mask=np.isfinite(v)
            return float(np.average(v[mask],weights=w[mask])) if mask.any() else fallback
        s=ew(scored,1.2); c=ew(conceded,1.2)
        x1=ew(xgf,s); x2=ew(xga,c)
        return s,c,x1,x2

    def _league_means(self, cutoff):
        h=self.df[self.df.Date < cutoff] if self.df is not None else None
        if h is None or h.empty:
            return 1.45,1.15
        return max(float(h.FTHG.mean()),0.05), max(float(h.FTAG.mean()),0.05)

    def predict(self,home,away,cutoff):
        league_home, league_away = self._league_means(cutoff)
        hs,hc,hx,hxa=self._team(home,cutoff)
        ass,ac,ax,axa=self._team(away,cutoff)
        base=(league_home+league_away)/2
        home_attack=0.55*(hs/max(base,0.1))+0.45*(hx/max(base,0.1))
        away_attack=0.55*(ass/max(base,0.1))+0.45*(ax/max(base,0.1))
        home_def=0.55*(hc/max(base,0.1))+0.45*(hxa/max(base,0.1))
        away_def=0.55*(ac/max(base,0.1))+0.45*(axa/max(base,0.1))
        lh=league_home*home_attack/max(away_def,0.15)
        la=league_away*away_attack/max(home_def,0.15)
        lh=float(np.clip(lh,0.05,4.5)); la=float(np.clip(la,0.05,4.5))
        mat=score_matrix(lh,la,rho=-0.05,max_goals=10)
        return lh,la,mat
