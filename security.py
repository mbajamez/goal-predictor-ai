from pathlib import Path
import re
import pandas as pd

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
TEAM_PATTERN = re.compile(r"^[A-Za-z0-9 .,'&()_\-/]+$")

def clean_team_name(value):
    value = str(value).strip()
    if not value or len(value) > 100 or not TEAM_PATTERN.fullmatch(value):
        raise ValueError("Invalid team name.")
    return value

def validate_csv_upload(upload):
    if upload is None:
        raise ValueError("No file uploaded.")
    if upload.size > MAX_UPLOAD_BYTES:
        raise ValueError("CSV exceeds the 10 MB safety limit.")
    if not upload.name.lower().endswith(".csv"):
        raise ValueError("Only CSV files are accepted.")

def validate_match_frame(df):
    required = {"Date","HomeTeam","AwayTeam","FTHG","FTAG"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if df.empty:
        raise ValueError("Dataset is empty.")
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    if df["Date"].isna().any():
        raise ValueError("Invalid match date detected.")
    for c in ["FTHG","FTAG"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if df[["FTHG","FTAG"]].isna().any().any():
        raise ValueError("Invalid goal value detected.")
    if (df[["FTHG","FTAG"]] < 0).any().any():
        raise ValueError("Negative goals are invalid.")
    for c in ["HomeTeam","AwayTeam"]:
        df[c] = df[c].map(clean_team_name)
    if (df.HomeTeam == df.AwayTeam).any():
        raise ValueError("A team cannot play itself.")
    return df.sort_values("Date").reset_index(drop=True)
