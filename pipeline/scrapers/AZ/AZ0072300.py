import numpy as np
import pandas as pd
import requests
import sys

from io import StringIO

sys.path.append("../../utils")
from super import Scraper


class AZ0072300(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["AZ0072300"]
        self.url = (
            "https://www.phoenixopendata.com/dataset/cc08aace-9ca9-467f-b6c1-f0879ab1a358/resource/0ce3411a"
            "-2fc6-4302-a33f-167f68608a20/download/crime-data_crime-data_crimestat.csv"
        )
        self.mapping = {
            "AGGRAVATED ASSAULT": "aggravated_assault",
            "BURGLARY": "burglary",
            "LARCENY-THEFT": "theft",
            "MOTOR VEHICLE THEFT": "motor_vehicle_theft",
            "MURDER AND NON-NEGLIGENT MANSLAUGHTER": "murder",
            "RAPE": "rape",
            "ROBBERY": "robbery",
        }

    def scrape(self):
        # get csv from source
        r = requests.get(self.url).content
        df = pd.read_csv(StringIO(r.decode("utf-8")), low_memory=False)[
            ["OCCURRED ON", "OCCURRED TO", "UCR CRIME CATEGORY"]
        ]

        # handle year/month extraction (two potential column sources)
        df["OCCURRED ON"] = pd.to_datetime(df["OCCURRED ON"], format="mixed")
        df["OCCURRED TO"] = pd.to_datetime(df["OCCURRED TO"], format="mixed")
        df["year"] = df["OCCURRED ON"].dt.year
        df["month"] = df["OCCURRED ON"].dt.month
        df["year"] = np.where(df["year"].isna(), df["OCCURRED TO"].dt.year, df["year"])
        df["month"] = np.where(
            df["month"].isna(), df["OCCURRED TO"].dt.month, df["month"]
        )
        df[["year", "month"]] = df[["year", "month"]].astype(int)
        df = df.drop(columns=["OCCURRED ON", "OCCURRED TO"])
        df = df[df["year"] >= self.first.year]

        # extract crime
        df["UCR CRIME CATEGORY"] = df["UCR CRIME CATEGORY"].map(self.mapping)
        df = df[df["UCR CRIME CATEGORY"].notna()]

        # get monthly counts and report
        df = (
            (
                df.groupby(["year", "month"])["UCR CRIME CATEGORY"]
                .value_counts()
                .reset_index()
            )
            .pivot(
                index=["year", "month"], columns="UCR CRIME CATEGORY", values="count"
            )
            .reset_index()
        )

        return df.to_dict("records")


AZ0072300().run()
