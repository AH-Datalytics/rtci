import numpy as np
import pandas as pd
import requests
import sys

from io import StringIO

sys.path.append("../../utils")
from crimes import rtci_to_nibrs
from super import Scraper


class MDBPD0000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["MDBPD0000"]
        self.url = (
            "https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/NIBRS_GroupA_Crime_Data"
            "/FeatureServer/replicafilescache/NIBRS_GroupA_Crime_Data_8914151926081121180.csv"
        )
        self.map = {
            k: v
            for e in [
                {d["Offense Code"]: crime for d in rtci_to_nibrs[crime]}
                for crime in rtci_to_nibrs
            ]
            for k, v in e.items()
        }

    def scrape(self):
        # get csv from source
        r = requests.get(self.url).content
        df = pd.read_csv(StringIO(r.decode("utf-8")), low_memory=False)[
            ["CrimeDateTime", "CrimeCode", "Total_Incidents"]
        ]
        df["CrimeDateTime"] = pd.to_datetime(df["CrimeDateTime"])
        df = df[df["CrimeCode"].isin(self.map)]
        df["CrimeCode"] = df["CrimeCode"].map(self.map)
        df["year"] = df["CrimeDateTime"].dt.year
        df["month"] = df["CrimeDateTime"].dt.month
        df = (
            df.groupby(["year", "month", "CrimeCode"])["Total_Incidents"]
            .sum()
            .reset_index()
            .rename(columns={"CrimeCode": "crime", "Total_Incidents": "count"})
        )
        df = df.pivot(
            index=["year", "month"],
            columns="crime",
            values="count",
        ).reset_index()
        return df.to_dict("records")


MDBPD0000().run()
