"""Aggregate local JSON scrape output into a single CSV.
Reads from ~/Downloads/scrape_output/{STATE}/{ORI}.json
Writes to ~/Downloads/aggregated.csv
"""
import json
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path.home() / "Downloads" / "scrape_output"
OUT_CSV = Path.home() / "Downloads" / "aggregated.csv"

all_records = []

for state_dir in sorted(OUTPUT_DIR.iterdir()):
    if not state_dir.is_dir():
        continue
    for json_file in sorted(state_dir.glob("*.json")):
        with open(json_file) as f:
            records = json.load(f)
        for r in records:
            r["state"] = state_dir.name
        all_records.extend(records)
        print(f"  {state_dir.name}/{json_file.stem}: {len(records)} records")

if all_records:
    df = pd.DataFrame(all_records)
    # Reorder columns: ori, state, year, month first
    front = ["ori", "state", "year", "month"]
    rest = [c for c in df.columns if c not in front]
    df = df[front + rest]
    df.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {len(df)} total records to {OUT_CSV}")
else:
    print("No records found!")
