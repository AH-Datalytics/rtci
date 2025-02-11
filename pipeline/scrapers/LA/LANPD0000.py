import json
import pandas as pd
import requests
import sys

from datetime import datetime as dt

sys.path.append("../../utils")
from super import Scraper


# TODO: handle turn of the year from 2024 -> 2025 in terms of data availability url


class LANPD0000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["LANPD0000"]
        self.limit = 1_000_000
        self.crosswalk = {
            d["Signal_Description"]: d["#"].lower().replace(" ", "_")
            for d in pd.read_csv(self.crosswalks.LANPD0000).to_dict("records")
        }
        self.urls = {
            2017: "qtcu-97s9",
            2018: "3m97-9vtw",
            2019: "mm32-zkg7",
            2020: "hjbe-qzaz",
            2021: "6pqh-bfxa",
            2022: "9wdb-bznc",
            2023: "j3gz-62a2",
            2024: "c5iy-ew8n",
            # 2025: "",
        }
        self.urls = {
            k: "https://data.nola.gov/resource/" + v + ".json?$query="
            for k, v in self.urls.items()
        }

    def scrape(self):
        dfs = list()

        # run through specific urls for each year
        for url in self.urls.values():
            r = requests.get(
                url + "SELECT"  # 'SELECT'
                "%0A%20%20%60item_number%60%2C"  # '\n  `item_number`,'
                "%0A%20%20%60occurred_date_time%60%2C"  # '\n  `occurred_date_time`,'
                "%0A%20%20%60signal_description%60"  # '\n  `occurred_date_time`'
                "%0AORDER%20BY%20%60occurred_date_time%60%20"  # '\nORDER BY `occurred_date_time` '
                "DESC%20NULL%20FIRST"  # 'DESC NULL FIRST'
                f"%0ALIMIT%20{self.limit}"  # '\nLIMIT {self.limit}'
                "%0AOFFSET%200"  # '\nOFFSET 0'
            )

            # make sure api has returned all records
            j = json.loads(r.text)
            assert len(j) < self.limit

            # format date and crime columns
            df = pd.DataFrame(j)
            df["occurred_date_time"] = pd.to_datetime(
                df["occurred_date_time"], format="ISO8601"
            )
            df["signal_description"] = df["signal_description"].map(self.crosswalk)
            df = df[df["signal_description"].notna()]
            dfs.append(df)

        # combine all annual data
        df = pd.concat(dfs)
        df = df.rename(columns={"occurred_date_time": "date"})
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month

        # drop duplicate `item_number`s except if `signal_description` differs
        df = df.drop_duplicates(["item_number", "signal_description"])

        # get monthly counts and report
        df = (
            (
                df.groupby(["year", "month"])["signal_description"]
                .value_counts()
                .reset_index()
            )
            .pivot(
                index=["year", "month"], columns="signal_description", values="count"
            )
            .reset_index()
        )

        return df.to_dict("records")


LANPD0000().run()
