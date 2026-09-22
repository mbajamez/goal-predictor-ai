import pandas as pd
import streamlit as st
from engine import RollingGoalEngine
from calibration import ProbabilityCalibrator
from security import clean_team_name, validate_csv_upload, validate_match_frame

st.set_page_config(page_title="GoalPredict AI Pro",page_icon="⚽",layout="wide")
st.title("⚽ GoalPredict AI Pro")
st.caption("Dixon–Coles + rolling form + optional xG + calibrated Over 1.5 probabilities.")

@st.cache_data
def load():
    return pd.read_csv("data/matches.csv",parse_dates=["Date"])

try:
    df=validate_match_frame(load())
except Exception as e:
    st.error(str(e)); st.stop()

teams=sorted(set(df.HomeTeam)|set(df.AwayTeam))
home=st.selectbox("Home team",teams)
away=st.selectbox("Away team",teams)
date=st.date_input("Prediction date",value=df.Date.max().date())

if st.button("Predict",type="primary",use_container_width=True):
    home=clean_team_name(home); away=clean_team_name(away)
    if home==away: st.error("Choose different teams.")
    else:
        hist=df[df.Date < pd.Timestamp(date)]
        if len(hist)<100:
            st.warning("Use a prediction date with at least 100 historical matches.")
        else:
            eng=RollingGoalEngine(); eng.fit(hist)
            lh,la,m=eng.predict(home,away,pd.Timestamp(date))
            p15=float(sum(m[h,a] for h in range(m.shape[0]) for a in range(m.shape[1]) if h+a>=2))
            p25=float(sum(m[h,a] for h in range(m.shape[0]) for a in range(m.shape[1]) if h+a>=3))
            p2=float(sum(m[h,a] for h in range(m.shape[0]) for a in range(m.shape[1]) if h+a==2))

            c1,c2,c3=st.columns(3)
            c1.metric("Over 1.5",f"{p15:.1%}")
            c2.metric("Over 2.5",f"{p25:.1%}")
            c3.metric("Exactly 2",f"{p2:.1%}")
            c1,c2=st.columns(2)
            c1.metric(f"{home} expected goals",f"{lh:.2f}")
            c2.metric(f"{away} expected goals",f"{la:.2f}")

            rows=[]
            for h in range(m.shape[0]):
                for a in range(m.shape[1]):
                    rows.append((f"{h}-{a}",m[h,a]))
            score=pd.DataFrame(rows,columns=["Score","Probability"]).sort_values("Probability",ascending=False).head(10)
            score["Probability"]=score["Probability"].map(lambda x:f"{x:.1%}")
            st.dataframe(score,hide_index=True,use_container_width=True)

st.divider()
st.subheader("Walk-forward validation")
try:
    import json
    with open("models/metrics.json") as f: met=json.load(f)
    st.json(met)
except FileNotFoundError:
    st.info("Run `python walk_forward.py` after downloading enough historical data.")
