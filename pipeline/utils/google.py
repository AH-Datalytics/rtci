import gspread
import pandas as pd

from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

CREDENTIALS = Credentials.from_service_account_file(
    "/Users/ojt/Downloads/rtcitest-028467fea159.json", scopes=SCOPES
)

gc = gspread.authorize(CREDENTIALS)
gauth = GoogleAuth()
drive = GoogleDrive(gauth)

# # open a google sheet
# # gs = gc.open_by_key("1EYumcJg46E2uOzzjnCum9aPgs5wXnmfZYjE-JGJZmrk")
# gs = gc.open_by_url(
#     "https://docs.google.com/spreadsheets/d/1EYumcJg46E2uOzzjnCum9aPgs5wXnmfZYjE-JGJZmrk/edit?gid=0#gid=0"
# )
#
# # select a work sheet from its name
# worksheet1 = gs.worksheet("Sheet1")
#
# df = pd.read_csv("https://rtci.s3.us-east-1.amazonaws.com/fbi/cde_filtered_oris.csv")
#
# worksheet1.clear()
# set_with_dataframe(worksheet=worksheet1, dataframe=df, include_index=False,
# include_column_header=True, resize=True)
