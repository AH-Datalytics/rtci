import pandas as pd
import sys

sys.path.append("../utils")
from airtable import insert_to_airtable_sheet
from logger import create_logger


logger = create_logger()


# pull in source xlsx file as df
src = pd.read_excel("Populations for RTCI.xlsx")
src.columns = ["ori", "city", "state", "pop_2022", "pop_2023"]
to_insert = src.to_dict("records")
to_insert = [{"fields": d} for d in to_insert]


# upsert to airtable
insert_to_airtable_sheet(
    logger=logger, sheet_name="Metadata", to_insert=to_insert, keys=["ori"]
)
