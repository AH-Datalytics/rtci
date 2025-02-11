import pandas as pd
import requests
import sys

from io import StringIO

sys.path.append("../../utils")
from super import Scraper


class MI8234900(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["MI8234900"]
        self.url = (
            "https://hub.arcgis.com/api/v3/datasets/8e532daeec1149879bd5e67fdd9c8be0_0/downloads/data?format"
            "=csv&spatialRefId=4326&where=1%3D1"
        )
        self.crosswalk = {
            d["state_offense_code"]: d["#"].lower().replace(" ", "_")
            for d in pd.read_csv(self.crosswalks.MI8234900).to_dict("records")
        }

    def scrape(self):
        # get csv from source
        r = requests.get(self.url).content
        df = pd.read_csv(StringIO(r.decode("utf-8")), low_memory=False)[
            ["state_offense_code", "incident_occurred_at"]
        ]

        # extract crime
        df = df[df["state_offense_code"].isin(self.crosswalk)]
        df["state_offense_code"] = df["state_offense_code"].map(self.crosswalk)

        # extract year and month
        df["incident_occurred_at"] = pd.to_datetime(df["incident_occurred_at"])
        df["year"] = df["incident_occurred_at"].dt.year
        df["month"] = df["incident_occurred_at"].dt.month

        # get monthly counts and report
        df = (
            (
                df.groupby(["year", "month"])["state_offense_code"]
                .value_counts()
                .reset_index()
            )
            .pivot(
                index=["year", "month"], columns="state_offense_code", values="count"
            )
            .reset_index()
        )

        return df.to_dict("records")


MI8234900().run()
