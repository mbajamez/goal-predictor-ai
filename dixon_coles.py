import math
import numpy as np
from scipy.optimize import minimize

def tau(h, a, lh, la, rho):
    # Dixon-Coles low-score correction.
    if h == 0 and a == 0: return 1 - lh*la*rho
    if h == 0 and a == 1: return 1 + lh*rho
    if h == 1 and a == 0: return 1 + la*rho
    if h == 1 and a == 1: return 1 - rho
    return 1.0

def score_matrix(lh, la, rho=0.0, max_goals=8):
    m=np.zeros((max_goals+1,max_goals+1))
    for h in range(max_goals+1):
        for a in range(max_goals+1):
            p=math.exp(-lh)*lh**h/math.factorial(h)
            p*=math.exp(-la)*la**a/math.factorial(a)
            m[h,a]=max(p*tau(h,a,lh,la,rho),0.0)
    s=m.sum()
    return m/s if s else m

def dc_objective(params, home, away):
    # params: attack_home..., defence..., attack-away encoded separately.
    n=len(home)
    k=(len(params)-1)//2
    attack=params[:k]
    defence=params[k:2*k]
    rho=params[-1]
    ll=0.0
    teams=sorted(set(home)|set(away))
    idx={t:i for i,t in enumerate(teams)}
    avg=1.35
    for h,a,hg,ag in zip(home,away,HOME_GOALS,AWAY_GOALS):
        lh=math.exp(avg+attack[idx[h]]-defence[idx[a]])
        la=math.exp(attack[idx[a]]-defence[idx[h]])
        p=math.exp(-lh)*lh**hg/math.factorial(hg)
        p*=math.exp(-la)*la**ag/math.factorial(ag)
        p*=tau(hg,ag,lh,la,rho)
        ll += math.log(max(p,1e-12))
    return -ll

# Kept as a reusable low-score distribution module; the application uses
# a regularized rolling-strength estimator for speed in walk-forward runs.
HOME_GOALS=[]
AWAY_GOALS=[]
