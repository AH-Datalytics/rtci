import gspread
import pandas as pd

from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe


# For information on setting up Google API interactivity, see:
# https://medium.com/@jb.ranchana/write-and-append-dataframes-to-google-sheets-in-python-f62479460cf0


gc_files = {
    "agencies": "https://docs.google.com/spreadsheets/d/1LXidpQnMRyqpVn4zwZJY3kL5XOeKgVOzQuHbSjV3zds/edit?gid=0"
}


def authorize():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        credentials = Credentials.from_service_account_file(
            "../gc_serv.json", scopes=scopes
        )
    except FileNotFoundError:
        credentials = Credentials.from_service_account_file(
            "../../gc_serv.json", scopes=scopes
        )
    return gspread.authorize(credentials)


def open_sheet(sheet, key=None, url=None):
    assert key or url
    gc = authorize()
    if key:
        gs = gc.open_by_key(key)
    else:
        gs = gc.open_by_url(url)

    worksheet = gs.worksheet(sheet)
    return worksheet


def clear_sheet(sheet, key=None, url=None):
    worksheet = open_sheet(sheet, key, url)
    worksheet.clear()
    return


def pull_sheet(sheet, key=None, url=None):
    worksheet = open_sheet(sheet, key, url)
    list_of_dicts = worksheet.get_all_records()
    return pd.DataFrame(list_of_dicts)


def update_sheet(sheet, df, key=None, url=None):
    worksheet = open_sheet(sheet, key, url)
    set_with_dataframe(
        worksheet=worksheet,
        dataframe=df,
        include_index=False,
        include_column_header=True,
        resize=True,
    )
    return
