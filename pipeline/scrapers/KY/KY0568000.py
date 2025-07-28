import pandas as pd
import requests
import sys

from collections import ChainMap

sys.path.append("../../utils")
from super import Scraper


class KY0568000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["KY0568000"]
        self.prefix = (
            "https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/"
        )
        self.suffix = "/FeatureServer/0/query"
        self.mapping = dict(
            ChainMap(
                *[{d["Offense Code"]: k for d in self.crimes[k]} for k in self.crimes]
            )
        )
        # note: there's a different url for each year
        # also, different fields are used depending on the year
        # TODO: query to get urls for each year of open data available?
        self.years = [
            (t[0], self.prefix + t[1] + self.suffix, t[2])
            for t in [
                (2017, "Crime_Data_2017", "reported"),
                (2018, "Crime_Data_2018_", "reported"),
                (2019, "CRIME_DATA2019", "reported"),
                (2020, "crime_2020", "reported"),
                (2021, "Louisville_Metro_KY_Crime_Data_2021", "reported"),
                (2022, "Louisville_Metro_KY_Crime_Data_2022", "reported"),
                (2023, "crime_data_2023", "occurred"),
                (2024, "crimedata2024", "occurred"),
                (2025, "crime_data_2025", "occurred"),
            ]
        ]
        self.years = [year for year in self.years if year[0] >= self.first.year]

        # make sure we're representing years up to most recent
        assert self.years[-1][0] == self.last.year

    def scrape(self):
        all_years_records = list()

        for year in self.years:
            self.logger.info(f"collecting {year[0]}...")

            # post for full record count
            data = {
                "f": "json",
                "where": "1=1",
                "outFields": "*",
                "returnCountOnly": True,
            }
            count = requests.post(year[1], data=data).json()["count"]
            self.logger.info(f"{count} records found")

            # update payload for data retrieval
            del data["returnCountOnly"]
            data.update(
                {"returnGeometry": False, "resultOffset": 0, "resultRecordCount": 1_000}
            )
            records = [
                d["attributes"]
                for d in requests.post(year[1], data=data).json()["features"]
            ]

            # iterate through offsets until all records collected
            while data["resultOffset"] <= count:
                data["resultOffset"] += 1_000
                records.extend(
                    [
                        d["attributes"]
                        for d in requests.post(year[1], data=data).json()["features"]
                    ]
                )

            assert len(records) == count

            try:
                df = pd.DataFrame(records)[
                    ["DATE_REPORTED", "DATE_OCCURED", "NIBRS_CODE"]
                ].rename(
                    columns={
                        "DATE_REPORTED": "date_reported",
                        "DATE_OCCURED": "date_occurred",
                        "NIBRS_CODE": "nibrs_code",
                    }
                )
            except KeyError:
                df = pd.DataFrame(records)[
                    ["date_reported", "date_occurred", "nibrs_code"]
                ]

            # different date field depending on the year
            # (from 2023 on, `date_occurred` is used rather than `date_reported`)
            if year[2] == "reported":
                df["date"] = df["date_reported"]
                df = df.drop(columns=["date_reported"])
            elif year[2] == "occurred":
                df["date"] = df["date_occurred"]
            df = df.drop(columns=["date_occurred"])

            # extract year/month
            if df["date"].dtype != object:
                df["date"] = pd.to_datetime(df["date"], unit="ms")
            else:
                df["date"] = pd.to_datetime(df["date"])
            df["year"] = df["date"].dt.year
            df["month"] = df["date"].dt.month
            df = df.drop(columns=["date"])

            # extract crime
            df = df[df["nibrs_code"].isin(self.mapping)]
            df["nibrs_code"] = df["nibrs_code"].map(self.mapping)

            df = (
                df.groupby(["year", "month"])["nibrs_code"]
                .value_counts()
                .reset_index()
                .pivot(index=["year", "month"], columns="nibrs_code", values="count")
                .reset_index()
            )

            all_years_records.extend(df.to_dict("records"))

        # drop duplicates on year/month from getting previous month data in pdfs
        df = pd.DataFrame(all_years_records)
        df[["year", "month"]] = df[["year", "month"]].astype(int)
        df = df.drop_duplicates(["year", "month"])
        df = df.sort_values(by=["year", "month"])
        data = df.to_dict("records")
        return data


KY0568000().run()
