import pandas as pd
import requests
import sys

from io import StringIO

sys.path.append("../../utils")
from crimes import rtci_to_nibrs
from super import Scraper


class NV0020100(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["NV0020100"]
        self.urls = [
            "https://services.arcgis.com/jjSk6t82vIntwDbs/arcgis/rest/services"
            "/LVMPD_Reported_NIBRS_Crimes_Against_Persons/FeatureServer/replicafilescache"
            "/LVMPD_Reported_NIBRS_Crimes_Against_Persons_2558264091583054136.csv",
            "https://services.arcgis.com/jjSk6t82vIntwDbs/arcgis/rest/services"
            "/LVMPD_Reported_NIBRS_Crimes_Against_Property/FeatureServer/replicafilescache"
            "/LVMPD_Reported_NIBRS_Crimes_Against_Property_6012106592085849777.csv",
        ]
        self.map = {}
        for crime in rtci_to_nibrs:
            for el in rtci_to_nibrs[crime]:
                self.map[el["Offense Code"]] = crime

    def scrape(self):
        dfs = list()

        for url in self.urls:
            r = requests.get(url).content
            df = pd.read_csv(StringIO(r.decode("utf-8")))[
                ["Reported On Date", "NIBRS Offense Code"]
            ]
            df["Reported On Date"] = pd.to_datetime(
                df["Reported On Date"], format="%m/%d/%Y %I:%M:%S %p"
            )
            df["year"] = df["Reported On Date"].dt.year
            df["month"] = df["Reported On Date"].dt.month
            del df["Reported On Date"]
            df = df[df["NIBRS Offense Code"].isin(self.map)]
            df["NIBRS Offense Code"] = df["NIBRS Offense Code"].map(self.map)
            df = (
                df.groupby(["year", "month"])["NIBRS Offense Code"]
                .value_counts()
                .reset_index()
                .pivot(
                    index=["year", "month"],
                    columns="NIBRS Offense Code",
                    values="count",
                )
            ).reset_index()
            dfs.append(df)

        assert len(dfs[0]) == len(dfs[1])
        df = pd.merge(dfs[0], dfs[1], on=["year", "month"])
        return df.to_dict("records")


NV0020100().run()
