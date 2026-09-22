import argparse
from pathlib import Path
import pandas as pd
from security import validate_match_frame

def load_raw(folder):
    frames=[]
    for p in sorted(Path(folder).glob("*.csv")):
        df=pd.read_csv(p)
        if {"Date","HomeTeam","AwayTeam","FTHG","FTAG"}.issubset(df.columns):
            keep=["Date","HomeTeam","AwayTeam","FTHG","FTAG"]
            # Optional match statistics available in many Football-Data files.
            for c in ["HS","AS","HST","AST","HC","AC","HF","AF","HY","AY","HR","AR"]:
                if c in df.columns: keep.append(c)
            frames.append(df[keep])
    if not frames: raise ValueError("No compatible Football-Data CSV files found.")
    return pd.concat(frames, ignore_index=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="data/raw")
    ap.add_argument("--xg",default=None)
    ap.add_argument("--output",default="data/matches.csv")
    args=ap.parse_args()

    df=load_raw(args.input)
    df=validate_match_frame(df)

    if args.xg:
        xg=pd.read_csv(args.xg)
        xg["Date"]=pd.to_datetime(xg["Date"],errors="coerce")
        xg=xg.rename(columns={"HomeXG":"HomeXG","AwayXG":"AwayXG"})
        need={"Date","HomeTeam","AwayTeam","HomeXG","AwayXG"}
        if not need.issubset(xg.columns):
            raise ValueError(f"xG file needs {sorted(need)}")
        xg["HomeXG"]=pd.to_numeric(xg["HomeXG"],errors="coerce")
        xg["AwayXG"]=pd.to_numeric(xg["AwayXG"],errors="coerce")
        df=df.merge(xg[list(need)],on=["Date","HomeTeam","AwayTeam"],how="left")

    df=df.drop_duplicates(["Date","HomeTeam","AwayTeam"]).sort_values("Date")
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(args.output,index=False)
    print(f"Wrote {len(df):,} matches to {args.output}")

if __name__=="__main__":
    main()
