import json
import pandas as pd
import requests
import sys

from datetime import datetime as dt
from functools import reduce

sys.path.append("../utils")
from airtable import get_records_from_sheet
from parallelize import thread
from super import Scraper


class SouthDakota(Scraper):
    def __init__(self):
        super().__init__()
        self.path = "SD/"
        self.agency_list_url = (
            "https://sdcrime.nibrs.com/Report/GetReportByValues?ReportType=Agency"
        )
        self.data_url = "https://sdcrime.nibrs.com/Report/GetCrimeTrends?"
        self.payload = {
            "ReportType": "Agency",
            "startDate": "012017",
            "endDate": "082024",
            "DrillDownReportIDs": -1,
            "IsGroupAOffense": True,
        }
        self.offense_ids = {
            "09A": "murder",
            "11A,11B,11C": "rape",
            "120": "robbery",
            "13A": "aggravated_assault",
            "220": "burglary",
            "23A,23B,23C,23D,23E,23F,23G,23H": "theft",
            "240": "motor_vehicle_theft",
        }

    def scrape(self):
        # get list of agencies of interest from airtable
        agencies = [
            d["ori"]
            for d in get_records_from_sheet(
                self.logger, "Metadata", formula="{state}='South Dakota'"
            )
        ]

        # get list of input values from website
        r = requests.get(self.agency_list_url)
        a = pd.DataFrame(json.loads(r.text))
        a["Value"] = a["Value"].astype(str)

        # match together two sources
        agencies = [
            (agency, a[a["Description"].str.startswith(agency)]["Value"].item())
            for agency in agencies
        ]

        all_agencies = thread(self.get_agency, agencies)
        return all_agencies

    def get_agency(self, agency):
        agency, value = agency
        payload = self.payload.copy()
        payload.update({"ReportIDs": value})

        out = list()
        for offense in self.offense_ids:
            payload.update({"OffenseIDs": offense})
            r = requests.get(self.data_url, params=payload)
            j = json.loads(r.text)

            dates = [dt.strptime(d, "%Y/%b") for d in j["periodlist"]]
            crimes = j["crimeList"]
            assert len(crimes) == 1
            crimes = crimes[0]

            if crimes["data"]:
                out.append(
                    pd.DataFrame(
                        {"date": dates, self.offense_ids[offense]: crimes["data"]}
                    )
                )
            else:
                out.append(
                    pd.DataFrame({"date": dates, self.offense_ids[offense]: None})
                )

        df = reduce(lambda df1, df2: pd.merge(df1, df2, on="date"), out)
        df["ori"] = agency

        df = df.set_index("date")
        for crime in self.crimes:
            df[f"{crime}_mvs_12mo"] = df[crime].rolling(window=12).sum()
        df = df.reset_index()

        df = df[df["date"] > dt(2017, 12, 31, 0, 0)]

        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        del df["date"]

        return df.to_dict("records")


SouthDakota().run()
