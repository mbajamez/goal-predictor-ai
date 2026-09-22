import math
from collections import defaultdict

class EloRatings:
    """Leakage-safe chronological Elo ratings."""
    def __init__(self,k=20,home_advantage=55,initial=1500):
        self.k=k; self.home_advantage=home_advantage; self.initial=initial
        self.r={}

    def rating(self,t): return self.r.get(t,self.initial)

    def expected(self,a,b):
        return 1/(1+10**(-(self.rating(a)-self.rating(b))/400))

    def predict_diff(self,home,away):
        return self.rating(home)+self.home_advantage-self.rating(away)

    def update(self,home,away,hg,ag):
        ra=self.rating(home); rb=self.rating(away)
        exp=1/(1+10**(-((ra+self.home_advantage)-rb)/400))
        if hg>ag: actual=1
        elif hg==ag: actual=.5
        else: actual=0
        margin=max(1,abs(hg-ag))
        multiplier=math.log(margin+1)+1
        delta=self.k*multiplier*(actual-exp)
        self.r[home]=ra+delta
        self.r[away]=rb-delta

    def fit(self,df):
        for r in df.sort_values("Date").itertuples():
            self.update(r.HomeTeam,r.AwayTeam,r.FTHG,r.FTAG)
        return self
