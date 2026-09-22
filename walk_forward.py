import argparse, json
import pandas as pd
import numpy as np
from engine import RollingGoalEngine
from calibration import ProbabilityCalibrator, metrics

def run(df,min_train=300,step=1,calibration_window=250):
    df=df.sort_values("Date").reset_index(drop=True)
    raw=[]; outcomes=[]

    for i in range(min_train,len(df),step):
        train=df.iloc[:i]
        test=df.iloc[i]
        if test.HomeTeam not in set(train.HomeTeam)|set(train.AwayTeam): continue
        if test.AwayTeam not in set(train.HomeTeam)|set(train.AwayTeam): continue

        eng=RollingGoalEngine(); eng.fit(train)
        lh,la,m=eng.predict(test.HomeTeam,test.AwayTeam,test.Date)
        p=float(sum(m[h,a] for h in range(m.shape[0]) for a in range(m.shape[1]) if h+a>=2))
        raw.append(p)
        outcomes.append(int(test.FTHG+test.FTAG>=2))

    raw=np.asarray(raw); y=np.asarray(outcomes)
    if len(raw)<30:
        raise ValueError("Not enough walk-forward predictions. Download more historical seasons.")
    split=max(20,int(len(raw)*0.70))
    cal=ProbabilityCalibrator().fit(raw[:split],y[:split])
    calibrated=cal.transform(raw[split:])
    result=metrics(calibrated,y[split:])
    result["raw_brier"]=metrics(raw[split:],y[split:])["brier"]
    result["n_test"]=len(y[split:])
    pd.DataFrame({"raw_p":raw[split:],"calibrated_p":calibrated,"actual":y[split:]}).to_csv("models/calibration_predictions.csv",index=False)
    with open("models/metrics.json","w") as f: json.dump(result,f,indent=2)
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--input",default="data/matches.csv")
    a=ap.parse_args()
    df=pd.read_csv(a.input); df["Date"]=pd.to_datetime(df.Date)
    print(run(df))
