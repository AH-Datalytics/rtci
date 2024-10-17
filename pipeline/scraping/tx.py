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


class Texas(Scraper):
    def __init__(self):
        super().__init__()
        self.path = "tx/"
        self.agency_list_url = (
            "https://txucr.nibrs.com/SRSReport/GetSRSReportByValues?ReportType=Agency"
        )
        self.data_url = "https://txucr.nibrs.com/SRSReport/GetCrimeTrends?"
        self.payload = {
            "ReportType": "Agency",
            "StartDate": "01/01/2017",
            "EndDate": "08/31/2024",
            "OffenseIDs": "P1",
            "DrillDownReportIDs": -1,
        }

    def scrape(self):
        # get list of agencies of interest from airtable
        agencies = [
            d["ori"]
            for d in get_records_from_sheet(
                self.logger, "Metadata", formula="{state}='Texas'"
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
        r = requests.get(self.data_url, params=payload)
        j = json.loads(r.text)

        dates = [dt.strptime(d, "%Y/%b") for d in j["periodlist"]]
        crimes = j["crimeList"]

        out = list()
        for c in crimes:
            out.append(pd.DataFrame({"dates": dates, c["name"]: c["data"]}))
        df = reduce(lambda df1, df2: pd.merge(df1, df2, on="dates"), out)
        df = df.rename(
            columns={
                "dates": "Date",
                "Murder and Nonnegligent Homicide": "Murder",
                "Larceny - Theft": "Theft",
            }
        )
        df = df.drop(columns=["Manslaughter by Negligence"])
        df["ori"] = agency

        df.columns = df.columns.str.lower()
        df.columns = df.columns.str.replace(" ", "_")

        df = df.set_index("date")
        for crime in self.crimes:
            df[f"{crime}_mvs_12mo"] = df[crime].rolling(window=12).sum()
        df = df.reset_index()

        df = df[df["date"] > dt(2017, 12, 31, 0, 0)]

        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        del df["date"]

        return df.to_dict("records")


Texas().run()
