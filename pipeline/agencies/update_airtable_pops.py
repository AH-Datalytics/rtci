import pandas as pd
import sys

sys.path.append("../utils")
from airtable import get_records_from_sheet
from logger import create_logger


# pull in source xlsx file as df
src = pd.read_excel("Populations for RTCI.xlsx")
src.columns = ["ori", "city", "state", "pop_2022", "pop_2023"]

logger = create_logger()

# get dest airtable sheet
results = get_records_from_sheet(logger, "Metadata")
