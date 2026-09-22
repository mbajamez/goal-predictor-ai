import os
import pandas as pd
import streamlit as st
from engine import RollingGoalEngine
from security import clean_team_name, validate_csv_upload, validate_match_frame

st.set_page_config(page_title="GoalPredict AI Pro", page_icon="⚽", layout="wide")
st.title("⚽ GoalPredict AI Pro")
st.caption("Dixon–Coles + rolling form + optional xG + calibrated Over 1.5 probabilities.")

with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Upload historical matches CSV", type=["csv"])
    st.caption("Expected columns include Date, HomeTeam, AwayTeam, FTHG and FTAG. Optional: HomeXG, AwayXG.")

@st.cache_data
def read_uploaded(raw):
    return pd.read_csv(raw, parse_dates=["Date"])

def load_data():
    if uploaded is not None:
        return validate_match_frame(read_uploaded(uploaded))
    local = "data/matches.csv"
    if os.path.exists(local):
        return validate_match_frame(pd.read_csv(local, parse_dates=["Date"]))
    return None

try:
    df = load_data()
except Exception as e:
    st.error(f"Historical data could not be loaded: {e}")
    df = None

if df is None:
    st.info("The app is running. No historical dataset is bundled with this deployment yet.")
    st.markdown("### What to do next")
    st.markdown("1. Download licensed historical football results/xG data.\n2. Upload the CSV using **Historical matches CSV** in the sidebar.\n3. Select the teams and prediction date.\n4. The model will use only matches before the selected date.")
    st.divider()
    st.subheader("Sportmonks")
    try:
        token = os.getenv("SPORTMONKS_TOKEN") or st.secrets.get("SPORTMONKS_TOKEN")
    except Exception:
        token = os.getenv("SPORTMONKS_TOKEN")
    if token:
        st.success("Sportmonks secret is configured.")
    else:
        st.warning("Sportmonks secret is not configured yet. Add SPORTMONKS_TOKEN in Streamlit App Settings → Secrets.")
    st.stop()

teams = sorted(set(df.HomeTeam) | set(df.AwayTeam))
if len(teams) < 2:
    st.error("The dataset must contain at least two teams.")
    st.stop()

c1, c2 = st.columns(2)
with c1:
    home = st.selectbox("Home team", teams)
with c2:
    away = st.selectbox("Away team", teams, index=1 if len(teams) > 1 else 0)

date = st.date_input("Prediction date", value=df.Date.max().date())

if st.button("Predict", type="primary", use_container_width=True):
    home = clean_team_name(home); away = clean_team_name(away)
    if home == away:
        st.error("Choose different teams.")
    else:
        hist = df[df.Date < pd.Timestamp(date)]
        if len(hist) < 100:
            st.warning(f"Only {len(hist)} historical matches are available before this date. Use at least 100 for the current model.")
        else:
            eng = RollingGoalEngine(); eng.fit(hist)
            lh, la, m = eng.predict(home, away, pd.Timestamp(date))
            p15 = float(sum(m[h,a] for h in range(m.shape[0]) for a in range(m.shape[1]) if h+a >= 2))
            p25 = float(sum(m[h,a] for h in range(m.shape[0]) for a in range(m.shape[1]) if h+a >= 3))
            p2 = float(sum(m[h,a] for h in range(m.shape[0]) for a in range(m.shape[1]) if h+a == 2))
            c1,c2,c3=st.columns(3)
            c1.metric("Over 1.5",f"{p15:.1%}"); c2.metric("Over 2.5",f"{p25:.1%}"); c3.metric("Exactly 2",f"{p2:.1%}")
            c1,c2=st.columns(2)
            c1.metric(f"{home} expected goals",f"{lh:.2f}"); c2.metric(f"{away} expected goals",f"{la:.2f}")
            rows=[(f"{h}-{a}",m[h,a]) for h in range(m.shape[0]) for a in range(m.shape[1])]
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
    st.info("Validation metrics will appear after the historical-data training/evaluation pipeline has been run.")
