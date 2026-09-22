from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
import pandas as pd

from api_client import SportmonksClient

FREE_LEAGUES = {271: "Danish Superliga", 501: "Scottish Premiership"}


def _name(obj: dict) -> str:
    return str(obj.get("name") or obj.get("participant", {}).get("name") or "").strip()


def _participant_location(p: dict) -> str:
    meta = p.get("meta") or {}
    return str(meta.get("location") or p.get("location") or "").lower()


def _goals_from_scores(scores: Any, location: str):
    if not isinstance(scores, list):
        return None
    preferred = []
    for s in scores:
        desc = str(s.get("description") or "").upper()
        sc = s.get("score") or {}
        goals = sc.get("goals") if isinstance(sc, dict) else None
        loc = str(s.get("participant", {}).get("meta", {}).get("location") or s.get("location") or "").lower()
        if goals is None:
            continue
        preferred.append((desc, loc, goals))
    for desc, loc, goals in preferred:
        if loc == location and desc in {"CURRENT", "FT", "FULL_TIME", "FULLTIME"}:
            return float(goals)
    for desc, loc, goals in preferred:
        if loc == location:
            return float(goals)
    return None


def _xg_from_fixture(xgfixture: Any, location: str):
    if not isinstance(xgfixture, list):
        return None
    for item in xgfixture:
        loc = str(item.get("location") or item.get("participant", {}).get("meta", {}).get("location") or "").lower()
        data = item.get("data") or {}
        value = data.get("value") if isinstance(data, dict) else None
        if loc == location and value is not None:
            try:
                return float(value)
            except Exception:
                return None
    return None


def fixture_to_row(f: dict) -> dict | None:
    participants = f.get("participants") or []
    home = next((p for p in participants if _participant_location(p) == "home"), None)
    away = next((p for p in participants if _participant_location(p) == "away"), None)
    if not home or not away:
        # Some responses use a participant_id/meta structure but still expose name.
        if len(participants) >= 2:
            home, away = participants[0], participants[1]
        else:
            return None
    home_name, away_name = _name(home), _name(away)
    if not home_name or not away_name:
        return None
    start = pd.to_datetime(f.get("starting_at"), errors="coerce")
    if pd.isna(start):
        return None
    hg = _goals_from_scores(f.get("scores"), "home")
    ag = _goals_from_scores(f.get("scores"), "away")
    return {
        "FixtureID": int(f.get("id")),
        "Date": start,
        "HomeTeam": home_name,
        "AwayTeam": away_name,
        "FTHG": hg,
        "FTAG": ag,
        "HomeXG": _xg_from_fixture(f.get("xgfixture"), "home"),
        "AwayXG": _xg_from_fixture(f.get("xgfixture"), "away"),
        "LeagueID": int(f.get("league_id")) if f.get("league_id") is not None else None,
        "SeasonID": int(f.get("season_id")) if f.get("season_id") is not None else None,
        "StateID": int(f.get("state_id")) if f.get("state_id") is not None else None,
        "Venue": (f.get("venue") or {}).get("name") if isinstance(f.get("venue"), dict) else None,
    }


def _extract_data(payload: dict) -> list[dict]:
    data = payload.get("data", []) if isinstance(payload, dict) else []
    return data if isinstance(data, list) else [data]


def fetch_league_info(client: SportmonksClient, league_id: int) -> dict:
    return client._get(f"leagues/{int(league_id)}", {"include": "currentSeason;seasons"}).get("data", {})


def fetch_season_fixtures(client: SportmonksClient, season_id: int, include_xg: bool = True) -> list[dict]:
    """Fetch a season using the documented all-fixtures endpoint + season filter.

    Some Sportmonks accounts/versions return 404 for the convenience route
    /fixtures/seasons/{id}. The canonical fixtures endpoint supports season
    filtering, so use it as the primary route and retain the old route only as
    a fallback for older API deployments.
    """
    include = "participants;scores"
    if include_xg:
        include += ";xGFixture"
    rows = []
    page = 1
    last_error = None
    while page <= 60:
        try:
            payload = client._get(
                "fixtures",
                {
                    "include": include,
                    "filters": f"fixtureSeasons:{int(season_id)}",
                    "per_page": 50,
                    "page": page,
                    "order": "asc",
                },
            )
        except RuntimeError as e:
            last_error = e
            # Backward-compatible fallback for accounts where season filtering
            # is unavailable but the convenience route is supported.
            if page == 1:
                payload = client._get(
                    f"fixtures/seasons/{int(season_id)}",
                    {"include": include, "per_page": 50, "page": page, "order": "asc"},
                )
            else:
                raise
        data = _extract_data(payload)
        rows.extend(data)
        meta = payload.get("pagination") or {}
        if not meta.get("has_more") or len(data) == 0:
            break
        page += 1
    return rows


def fetch_recent_seasons(client: SportmonksClient, league_id: int, max_seasons: int = 2) -> tuple[list[dict], dict]:
    info = fetch_league_info(client, league_id)
    seasons = info.get("seasons") or []
    if isinstance(seasons, dict):
        seasons = seasons.get("data", [])
    current = info.get("currentSeason") or {}
    if isinstance(current, dict) and current.get("id"):
        if not any(int(s.get("id", -1)) == int(current["id"]) for s in seasons if isinstance(s, dict)):
            seasons.append(current)
    seasons = [s for s in seasons if isinstance(s, dict) and s.get("id")]
    seasons.sort(key=lambda s: str(s.get("name", "")), reverse=True)
    selected = seasons[:max_seasons]
    raw = []
    for s in selected:
        try:
            raw.extend(fetch_season_fixtures(client, int(s["id"]), include_xg=True))
        except Exception:
            # xG may be an add-on. Retry without it so the core predictor still works.
            raw.extend(fetch_season_fixtures(client, int(s["id"]), include_xg=False))
    return raw, info


def build_history(raw_fixtures: list[dict], league_id: int) -> pd.DataFrame:
    rows = []
    for f in raw_fixtures:
        if int(f.get("league_id", -1)) != int(league_id):
            continue
        r = fixture_to_row(f)
        if r and r["FTHG"] is not None and r["FTAG"] is not None:
            rows.append(r)
    if not rows:
        return pd.DataFrame(columns=["FixtureID", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "HomeXG", "AwayXG", "LeagueID", "SeasonID"])
    df = pd.DataFrame(rows).drop_duplicates("FixtureID").sort_values("Date")
    df["Date"] = pd.to_datetime(df["Date"], utc=False)
    return df.reset_index(drop=True)


def build_upcoming(raw_fixtures: list[dict], league_id: int, now=None) -> pd.DataFrame:
    now = pd.Timestamp(now or datetime.utcnow())
    rows = []
    for f in raw_fixtures:
        if int(f.get("league_id", -1)) != int(league_id):
            continue
        r = fixture_to_row(f)
        if r and r["Date"] >= now and r["FTHG"] is None:
            rows.append(r)
    return pd.DataFrame(rows).sort_values("Date").reset_index(drop=True) if rows else pd.DataFrame()
