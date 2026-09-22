import argparse, json
import numpy as np, pandas as pd
from engine import RollingGoalEngine
from ratings import EloRatings
from feature_store import make_pre_match_features
from calibration import ProbabilityCalibrator, metrics
from ensemble import GoalEnsemble

def run(df,min_train=300):
    df=df.sort_values("Date").reset_index(drop=True)
    rows=[]
    for i in range(min_train,len(df)):
        train=df.iloc[:i]; test=df.iloc[i]
        eng=RollingGoalEngine(); eng.fit(train)
        lh,la,m=eng.predict(test.HomeTeam,test.AwayTeam,test.Date)
        dc=float(sum(m[h,a] for h in range(m.shape[0]) for a in range(m.shape[1]) if h+a>=2))
        X=make_pre_match_features(train,test.HomeTeam,test.AwayTeam,test.Date)
        rows.append([*X,dc,int(test.FTHG+test.FTAG>=2)])
    z=np.asarray(rows,float)
    if len(z)<100: raise ValueError("Need more historical matches for ensemble walk-forward validation.")
    X=z[:,:6]; dc=z[:,6]; y=z[:,7].astype(int)

    # Fit ensemble only on an early block; evaluate on a later block.
    cut=int(len(y)*.7)
    ens=GoalEnsemble().fit(X[:cut],y[:cut],dc[:cut])
    raw=ens.predict_proba(X[cut:],dc[cut:])

    cal=ProbabilityCalibrator().fit(raw[:max(30,len(raw)//2)],y[cut:][:max(30,len(raw)//2)])
    p=cal.transform(raw)
    out=metrics(p,y[cut:])
    out["n_test"]=len(p)
    out["raw_brier"]=float(((raw-y[cut:])**2).mean())
    pd.DataFrame({"ensemble_raw":raw,"ensemble_calibrated":p,"actual":y[cut:]}).to_csv("models/ensemble_predictions.csv",index=False)
    with open("models/ensemble_metrics.json","w") as f: json.dump(out,f,indent=2)
    return out

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--input",default="data/matches.csv")
    a=ap.parse_args()
    df=pd.read_csv(a.input,parse_dates=["Date"])
    print(run(df))
