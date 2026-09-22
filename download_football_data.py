import argparse
from pathlib import Path
import requests

LEAGUES = {
    "E0":"England Premier League",
    "E1":"England Championship",
    "D1":"Germany Bundesliga",
    "I1":"Italy Serie A",
    "SP1":"Spain La Liga",
    "F1":"France Ligue 1",
    "N1":"Netherlands Eredivisie",
    "P1":"Portugal Liga I",
}

def season_code(start):
    return f"{str(start)[-2:]}{str(start+1)[-2:]}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default="E0", choices=sorted(LEAGUES))
    ap.add_argument("--start", type=int, default=2015)
    ap.add_argument("--end", type=int, default=2026)
    ap.add_argument("--out", default="data/raw")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    for year in range(args.start, args.end):
        code = season_code(year)
        url = f"https://www.football-data.co.uk/mmz4281/{code}/{args.league}.csv"
        r = requests.get(url, timeout=30, headers={"User-Agent":"GoalPredictAI/1.0"})
        if r.status_code == 200 and len(r.content) > 1000:
            path = out / f"{args.league}_{code}.csv"
            path.write_bytes(r.content)
            print("saved", path)
        else:
            print("skip", year, r.status_code)

if __name__ == "__main__":
    main()
