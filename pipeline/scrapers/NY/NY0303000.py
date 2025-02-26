import json
import pandas as pd
import requests
import sys

from datetime import datetime as dt
from time import time

sys.path.append("../../utils")
from crimes import rtci_to_nibrs
from super import Scraper


class NY0303000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["NY0303000"]
        self.url = (
            "https://data.cityofnewyork.us/api/views/qgea-i56i/rows.csv?fourfour=qgea-i56i&cacheBust={}&date={"
            "}&accessType=DOWNLOAD"
        )
        self.mapping = {
            "MURDER & NON-NEGL. MANSLAUGHTER": "murder",
            "RAPE": "rape",
            "ROBBERY": "robbery",
            "FELONY ASSAULT": "aggravated_assault",
            "BURGLARY": "burglary",
            "GRAND LARCENY": "theft",
            "PETIT LARCENY": "theft",
            "GRAND LARCENY OF MOTOR VEHICLE": "motor_vehicle_theft",
            "PETIT LARCENY OF MOTOR VEHICLE": "motor_vehicle_theft",
        }
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/133.0.0.0 Safari/537.36",
        }
        self.keys = {
            "Murder": "murder",
            "Rape": "rape",
            "Robbery": "robbery",
            "Fel. Assault": "aggravated_assault",
            "Burglary": "burglary",
            "Gr. Larceny": "theft",
            "G.L.A.": "motor_vehicle_theft",
            "Petit Larceny": "theft",
        }
        self.data = [
            {"key": "PRECINCTKey", "values": ["Citywide"]},
            {"key": "BOROKey", "values": ["Citywide"]},
            {"key": "RECORDID", "values": ["YTD"]},
            {"key": "CrimeKey", "values": ["Murder"]},
        ]
        self.this_year = dt.now().year

    def scrape(self):
        # get historical data up to year before last (from city csv)
        df = pd.read_csv(
            self.url.format(int(time()), int(dt.strftime(dt.now().date(), "%Y%m%d"))),
            low_memory=False,
        )[["RPT_DT", "OFNS_DESC"]]
        df["RPT_DT"] = pd.to_datetime(df["RPT_DT"])
        df["year"] = df["RPT_DT"].dt.year
        df["month"] = df["RPT_DT"].dt.month
        df["OFNS_DESC"] = df["OFNS_DESC"].map(self.mapping)
        df = df[df["OFNS_DESC"].notna()]
        df = (
            df.groupby(["year", "month"])["OFNS_DESC"]
            .value_counts()
            .reset_index()
            .pivot(
                index=["year", "month"],
                columns="OFNS_DESC",
                values="count",
            )
            .reset_index()
        )
        hist_max_year = df["year"].max()
        hist_max_month = df[df["year"] == hist_max_year]["month"].max()

        # get data from last year (from rtci `final_sample` csv)
        fs = pd.read_csv(
            "https://github.com/AH-Datalytics/rtci/blob/development/data/final_sample.csv?raw=true",
            low_memory=False,
        )
        fs = fs[fs["city_state"] == "New York City, NY"]
        fs["date"] = pd.to_datetime(fs["date"])
        fs = fs[
            (fs["date"] > dt(hist_max_year, hist_max_month, 1))
            & (fs["Year"] < self.this_year)
        ]
        fs = fs[
            ["Month", "Year", *[c.title().replace("_", " ") for c in rtci_to_nibrs]]
        ]
        fs.columns = [c.lower().replace(" ", "_") for c in fs.columns]
        assert fs[fs["year"] == fs["year"].max()]["month"].max() == 12

        # fold in last year's data
        df = pd.concat([df, fs]).reset_index()
        df = df[df["year"] < self.this_year]

        # get current year data (from city api)
        data = list()
        for crime in self.keys:
            self.data[-1]["values"] = [crime]
            r = json.loads(
                requests.post(
                    "https://compstat.nypdonline.org/api/reports/f1aa508f-a7bf-4bf9-a475-ccd1a9487d24/data",
                    data=json.dumps(self.data),
                    headers=self.headers,
                ).text
            )
            data.extend(
                [
                    {
                        "crime": self.keys[crime],
                        "year": self.this_year,
                        "month": dt.strptime(d["categoryValue"], "%b").month,
                        "count": d["itemValue"],
                    }
                    for d in r
                ]
            )
        api = pd.DataFrame(data)
        api = (
            api.groupby(["year", "month", "crime"])["count"]
            .sum()
            .reset_index()
            .pivot(
                index=["year", "month"],
                columns="crime",
                values="count",
            )
            .reset_index()
        )

        # stack it all together
        df = pd.concat([df, api])
        df = df.drop(columns=["index"])
        return df.to_dict("records")


NY0303000().run()
