import json
import pandas as pd
import streamlit as st
from api_client import SportmonksClient
from sportmonks_data import FREE_LEAGUES, fetch_recent_seasons, build_history, build_upcoming
from engine import RollingGoalEngine
from calibration import ProbabilityCalibrator, metrics
from security import clean_team_name

st.set_page_config(page_title="GoalPredict AI Pro", page_icon="⚽", layout="centered")
st.title("⚽ GoalPredict AI Pro")
st.caption("Sportmonks automatic data + Dixon–Coles + rolling form + optional xG + calibrated Over 1.5")

@st.cache_resource
def get_client():
    return SportmonksClient(timeout=25)

@st.cache_data(ttl=900, show_spinner=False)
def load_league(league_id: int):
    client = get_client()
    raw, info = fetch_recent_seasons(client, league_id, max_seasons=2)
    hist = build_history(raw, league_id)
    upcoming = build_upcoming(raw, league_id)
    return hist, upcoming, info

def over_prob(mat, minimum):
    return float(sum(mat[h,a] for h in range(mat.shape[0]) for a in range(mat.shape[1]) if h+a >= minimum))

def exact_prob(mat, total):
    return float(sum(mat[h,a] for h in range(mat.shape[0]) for a in range(mat.shape[1]) if h+a == total))

def calibrate_from_walkforward(hist: pd.DataFrame):
    # Out-of-sample calibration: every historical prediction only sees matches before its date.
    if len(hist) < 80:
        return None, None
    start = max(40, int(len(hist) * 0.35))
    raw_p, y = [], []
    engine = RollingGoalEngine()
    engine.fit(hist)
    for i in range(start, len(hist)):
        r = hist.iloc[i]
        try:
            _, _, m = engine.predict(r.HomeTeam, r.AwayTeam, r.Date)
            p = over_prob(m, 2)
            raw_p.append(p)
            y.append(int(r.FTHG + r.FTAG >= 2))
        except Exception:
            continue
    if len(y) < 25 or len(set(y)) < 2:
        return None, None
    cal = ProbabilityCalibrator().fit(raw_p, y)
    return cal, metrics(cal.transform(raw_p), y)

with st.sidebar:
    st.header("Sportmonks")
    if st.button("Refresh Sportmonks data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    try:
        get_client()
        st.success("Sportmonks secret is configured")
    except Exception as e:
        st.error(str(e))
        st.stop()
    league_name = st.selectbox("Competition", list(FREE_LEAGUES.values()))
    league_id = next(k for k,v in FREE_LEAGUES.items() if v == league_name)
    st.caption("Free-plan competitions: Danish Superliga and Scottish Premiership.")

with st.spinner("Loading fixtures and recent history from Sportmonks…"):
    try:
        hist, upcoming, league_info = load_league(league_id)
    except Exception as e:
        st.error(f"Sportmonks data request failed: {e}")
        st.info("If your token is correct, try Refresh Sportmonks data. If the message mentions a plan/coverage restriction, the selected competition or data add-on is not available on your account.")
        st.stop()

if hist.empty:
    st.warning("Sportmonks returned no completed matches for this competition in the seasons available to this account.")
    st.stop()

st.success(f"Loaded {len(hist)} completed matches from Sportmonks.")

# Prefer an actual upcoming fixture; otherwise allow a manual matchup.
if not upcoming.empty:
    upcoming["label"] = upcoming.apply(lambda r: f"{r.HomeTeam} vs {r.AwayTeam} — {pd.Timestamp(r.Date).strftime('%d %b %Y %H:%M')}", axis=1)
    choice = st.selectbox("Upcoming fixture", upcoming["label"].tolist())
    fx = upcoming.loc[upcoming.label == choice].iloc[0]
    home, away, pred_date = fx.HomeTeam, fx.AwayTeam, pd.Timestamp(fx.Date)
else:
    teams = sorted(set(hist.HomeTeam) | set(hist.AwayTeam))
    c1,c2 = st.columns(2)
    home = c1.selectbox("Home team", teams)
    away = c2.selectbox("Away team", teams, index=1 if len(teams)>1 else 0)
    pred_date = pd.Timestamp(st.date_input("Prediction date", value=pd.Timestamp.utcnow().date()))

st.write(f"**Selected:** {home} vs {away}")

if home == away:
    st.error("Choose two different teams.")
    st.stop()

history_before = hist[hist.Date < pred_date].copy()
if len(history_before) < 30:
    st.warning(f"Only {len(history_before)} completed matches are available before this fixture. The model can run, but calibration may be unavailable and uncertainty will be higher.")

if st.button("🎯 Predict automatically", type="primary", use_container_width=True):
    engine = RollingGoalEngine().fit(hist)
    lh, la, matrix = engine.predict(clean_team_name(home), clean_team_name(away), pred_date)
    raw15 = over_prob(matrix, 2)
    p25 = over_prob(matrix, 3)
    p2 = exact_prob(matrix, 2)
    cal, cal_metrics = calibrate_from_walkforward(history_before)
    p15 = float(cal.transform([raw15])[0]) if cal else raw15

    st.subheader("Prediction")
    c1,c2,c3 = st.columns(3)
    c1.metric("Over 1.5 goals", f"{p15:.1%}")
    c2.metric("Over 2.5 goals", f"{p25:.1%}")
    c3.metric("Exactly 2 goals", f"{p2:.1%}")
    c1,c2 = st.columns(2)
    c1.metric(f"{home} expected goals", f"{lh:.2f}")
    c2.metric(f"{away} expected goals", f"{la:.2f}")

    rows=[]
    for h in range(matrix.shape[0]):
        for a in range(matrix.shape[1]):
            rows.append((f"{h}-{a}", matrix[h,a]))
    score=pd.DataFrame(rows,columns=["Score","Probability"]).sort_values("Probability",ascending=False).head(10)
    score["Probability"]=score["Probability"].map(lambda x:f"{x:.1%}")
    st.subheader("Most likely scorelines")
    st.dataframe(score, hide_index=True, use_container_width=True)

    if cal_metrics:
        st.caption(f"Calibration evaluated with walk-forward historical predictions: Brier {cal_metrics['brier']:.3f}, log loss {cal_metrics['log_loss']:.3f}.")
    else:
        st.caption("Calibration needs more completed historical matches; the displayed Over 1.5 value is the raw model probability.")

st.divider()
st.subheader("Data status")
st.write(f"Completed matches: **{len(hist)}**")
st.write(f"Upcoming fixtures found: **{len(upcoming)}**")
st.write(f"Latest completed match: **{pd.Timestamp(hist.Date.max()).strftime('%d %b %Y')}**")
st.caption("This model is a statistical estimate, not a guarantee of match outcome. Sportmonks coverage and add-ons determine which fields are available to your account.")
