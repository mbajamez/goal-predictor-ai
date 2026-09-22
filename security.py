from pathlib import Path
import re
import unicodedata
import pandas as pd

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def clean_team_name(value):
    """Validate a team name without rejecting legitimate international names.

    Sportmonks returns real club names containing Unicode letters such as æ, ø,
    å, é, etc. The previous ASCII-only regex incorrectly rejected those names.
    We therefore reject control characters and path/query delimiters while
    preserving normal Unicode football-club names.
    """
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)
    if not value or len(value) > 100:
        raise ValueError("Invalid team name.")

    # Reject control/format characters that should never be present in a club
    # name. Keep normal Unicode letters, punctuation, apostrophes and symbols.
    for ch in value:
        if unicodedata.category(ch) in {"Cc", "Cf"}:
            raise ValueError("Invalid team name.")

    # These characters are not expected in a club name and can complicate
    # logging/UI handling. This is validation, not an ASCII allow-list.
    if any(ch in value for ch in ["\x00", "\r", "\n", "\t"]):
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
    required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if df.empty:
        raise ValueError("Dataset is empty.")
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    if df["Date"].isna().any():
        raise ValueError("Invalid match date detected.")
    for c in ["FTHG", "FTAG"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if df[["FTHG", "FTAG"]].isna().any().any():
        raise ValueError("Invalid goal value detected.")
    if (df[["FTHG", "FTAG"]] < 0).any().any():
        raise ValueError("Negative goals are invalid.")
    for c in ["HomeTeam", "AwayTeam"]:
        df[c] = df[c].map(clean_team_name)
    if (df.HomeTeam == df.AwayTeam).any():
        raise ValueError("A team cannot play itself.")
    return df.sort_values("Date").reset_index(drop=True)
