import pandas as pd
import requests
import sys

from io import StringIO

sys.path.append("../../utils")
from super import Scraper


class MD0172100(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["MD0172100"]
        self.url_2023 = (
            "https://data.princegeorgescountymd.gov/api/v3/views/xjru-idbe/export.csv"
        )
        self.url_2017 = (
            "https://data.princegeorgescountymd.gov/api/v3/views/wb4e-w4nf/export.csv"
        )
        self.headers = {"X-App-Token": "U29jcmF0YS0td2VraWNrYXNz0"}
        self.pay_2023 = {"cacheBust": 1760116516, "accessType": "DOWNLOAD"}
        self.pay_2017 = {"cacheBust": 1747335346, "accessType": "DOWNLOAD"}
        self.crosswalk = {
            d["clearance_code_inc_type"]: d["Type"].lower().replace(" ", "_")
            for d in pd.read_excel(self.crosswalks.MD0172100).to_dict("records")
        }
        self.records = list()

    def scrape(self):
        # collect data from 2023 to present
        r = requests.get(
            self.url_2023, data=self.pay_2023, headers=self.headers
        ).content
        df = pd.read_csv(StringIO(r.decode("utf-8")))[
            ["Date", "Clearance Code Inc Type"]
        ]
        df["Date"] = pd.to_datetime(df["Date"])
        df["year"] = df["Date"].dt.year
        df["month"] = df["Date"].dt.month
        del df["Date"]
        df = df[df["Clearance Code Inc Type"].isin(self.crosswalk)]
        df["Clearance Code Inc Type"] = df["Clearance Code Inc Type"].map(
            self.crosswalk
        )
        df = (
            df.groupby(["year", "month"])["Clearance Code Inc Type"]
            .value_counts()
            .reset_index()
            .pivot(
                index=["year", "month"],
                columns="Clearance Code Inc Type",
                values="count",
            )
        ).reset_index()
        self.records.extend(df.to_dict("records"))

        # if necessary, collect data from source for 2017-2023
        if self.first.year < 2023:
            r = requests.get(
                self.url_2017, data=self.pay_2017, headers=self.headers
            ).content
            df = pd.read_csv(StringIO(r.decode("utf-8")))[
                ["Date", "Clearance Code Inc Type"]
            ]
            df["Date"] = pd.to_datetime(df["Date"])
            df["year"] = df["Date"].dt.year
            df["month"] = df["Date"].dt.month
            del df["Date"]
            df = df[df["Clearance Code Inc Type"].isin(self.crosswalk)]
            df["Clearance Code Inc Type"] = df["Clearance Code Inc Type"].map(
                self.crosswalk
            )
            df = (
                df.groupby(["year", "month"])["Clearance Code Inc Type"]
                .value_counts()
                .reset_index()
                .pivot(
                    index=["year", "month"],
                    columns="Clearance Code Inc Type",
                    values="count",
                )
            ).reset_index()
            self.records.extend(df.to_dict("records"))

        # sum over duplication that may occur around 07-2023
        df = pd.DataFrame(self.records)
        df = df.groupby(["year", "month"]).sum().reset_index()
        return df.to_dict("records")


MD0172100().run()
