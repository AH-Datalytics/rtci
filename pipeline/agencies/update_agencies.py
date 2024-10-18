import numpy as np
import pandas as pd
import sys
import us

sys.path.append("../utils")
from airtable import get_records_from_sheet, insert_to_airtable_sheet
from logger import create_logger


logger = create_logger()


# pull in `final_sample.csv` (existing data maintained by rtci)
df = pd.read_csv("../../data/final_sample.csv")
df = df[
    [
        "State",
        "Agency",
        "city_state",
        "Source.Link",
        "Source.Type",
        "Source.Method",
    ]
]
df = df.drop_duplicates("city_state")
del df["city_state"]
df.columns = ["state_abbrev", "city", "source_url", "source_type", "source_method"]
df = df[df["city"].notna()]
df["state"] = df["state_abbrev"].apply(lambda s: us.states.lookup(s)).fillna("")
df["state"] = np.where(df["state_abbrev"] == "DC", "District of Columbia", df["state"])
df["state"] = df["state"].astype(str)
df["city"] = df["city"].str.title()
del df["state_abbrev"]


# pull in `Populations for RTCI.xlsx` (annual pull from fbi)
pops = pd.read_excel("Populations for RTCI.xlsx")
pops.columns = ["ori", "city", "state", "pop_2022", "pop_2023"]
pops["city"] = pops["city"].str.title()


# merge on city-state (i.e. agency) to get unique agencies/oris dataset
data = pd.merge(pops, df, how="left", on=["state", "city"])
data = data.fillna("")
to_insert = data.to_dict("records")
to_insert = [{"fields": d} for d in to_insert]


# upsert to airtable
insert_to_airtable_sheet(
    logger=logger, sheet_name="Metadata", to_insert=to_insert, keys=["ori"]
)
