import json
import pandas as pd
import requests
import sys

from datetime import datetime as dt

sys.path.append("../../utils")
from super import Scraper


class GAAPD0000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["GAAPD0000"]
        self.url = (
            "https://services3.arcgis.com/Et5Qfajgiyosiw4d/arcgis/rest/services/CrimeDataExport_2_view"
            "/FeatureServer/1/query"
        )
        self.mapping = {
            # murder
            "Murder & Nonnegligent Manslaughter": "murder",
            # rape
            "Rape": "rape",
            "Sexual Assault With An Object": "rape",
            "Sodomy": "rape",
            # robbery
            "Robbery": "robbery",
            # aggravated_assault
            "Aggravated Assault": "aggravated_assault",
            # burglary
            "Burglary/Breaking & Entering": "burglary",
            # theft
            "All Other Larceny": "theft",
            "Pocket-picking": "theft",
            "Purse-snatching": "theft",
            "Shoplifting": "theft",
            "Theft From Building": "theft",
            "Theft From Coin-Operated Machine or Device": "theft",
            "Theft From Motor Vehicle": "theft",
            "Theft of Motor Vehicle Parts or Accessories": "theft",
            # motor_vehicle_theft
            "Motor Vehicle Theft": "motor_vehicle_theft",
        }

    def scrape(self):
        records = list()

        # get first page of results
        data = {
            "f": "json",
            "where": f"((report_Date >= timestamp '{dt.strftime(self.first, '%Y-%m-%d')} 00:00:00'))",
            "outFields": "nibrs_code_name,report_Date",
            "returnGeometry": "false",
            "returnDistinctValues": "true",
            "orderByFields": "report_Date",
            "resultOffset": 0,
            "resultRecordCount": 2_000,  # max results permitted it seems
        }
        p = requests.post(self.url, data=data)
        j = [d["attributes"] for d in json.loads(p.text)["features"]]
        records.extend(j)

        # offsetting by record count, continue until no more results
        while j:
            data["resultOffset"] += 2_000
            p = requests.post(self.url, data=data)
            j = [d["attributes"] for d in json.loads(p.text)["features"]]
            records.extend(j)

        # extract year and month
        df = pd.DataFrame(records)
        df["report_Date"] = pd.to_datetime(df["report_Date"], unit="ms")
        df["year"] = df["report_Date"].dt.year
        df["month"] = df["report_Date"].dt.month
        df = df.drop(columns=["report_Date"])
        df = df[df["year"] >= self.first.year]

        # extract crime
        df["nibrs_code_name"] = df["nibrs_code_name"].map(self.mapping)
        df = df[df["nibrs_code_name"].notna()]

        # get monthly counts and report
        df = (
            (
                df.groupby(["year", "month"])["nibrs_code_name"]
                .value_counts()
                .reset_index()
            )
            .pivot(index=["year", "month"], columns="nibrs_code_name", values="count")
            .reset_index()
        )

        # note: usually we do not fill missing values with 0s,
        # but in this case values are counts from running through
        # the full set of incidents, so if there's a systematically
        # missing field, we'll have to pick it up later in audit
        df[list(self.crimes.keys())] = (
            df[list(self.crimes.keys())].fillna(0).astype(int)
        )

        return df.to_dict("records")


GAAPD0000().run()
