"""
Local-only replacement for google_configs.py — reads cached CSV copies
of the Google Sheets instead of requiring service account credentials.
"""
import os
import pandas as pd

UTILS_DIR = os.path.dirname(os.path.abspath(__file__))

gc_files = {
    "agencies": "https://docs.google.com/spreadsheets/d/1LXidpQnMRyqpVn4zwZJY3kL5XOeKgVOzQuHbSjV3zds/edit?gid=0"
}


def authorize():
    return None


def pull_sheet(sheet, key=None, url=None):
    """Read from local CSV instead of Google Sheets."""
    csv_path = os.path.join(UTILS_DIR, f"{sheet}_sheet.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    raise FileNotFoundError(f"Local sheet cache not found: {csv_path}. Run the download script first.")


def open_sheet(sheet, key=None, url=None):
    raise NotImplementedError("Google Sheets API disabled in local mode")


def clear_sheet(sheet, key=None, url=None):
    raise NotImplementedError("Google Sheets API disabled in local mode")


def update_sheet(sheet, df, key=None, url=None):
    """In local mode, save to CSV instead of updating Google Sheets."""
    csv_path = os.path.join(UTILS_DIR, f"{sheet}_sheet.csv")
    df.to_csv(csv_path, index=False)
    print(f"[local] Updated {csv_path} ({len(df)} rows)")
