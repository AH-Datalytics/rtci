import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS
from datetime import datetime as dt

sys.path.append("../../utils")
from google_configs import gc_files, pull_sheet
from super import Scraper


class California(Scraper):
    def __init__(self):
        super().__init__()
        self.url = "https://crimestats.arjis.org/default.aspx"
        self.mapping = {
            "Murder": "murder",
            "Rape**": "rape",
            "Armed Robbery": "robbery",
            "Strong Arm Robbery": "robbery",
            "Aggravated Assault**": "aggravated_assault",
            "Residential Burglary": "burglary",
            "Non-Residential Burglary": "burglary",
            "Theft >= $400": "theft",
            "Theft < $400": "theft",
            "Motor Vehicle Theft": "motor_vehicle_theft",
        }
        self.agencies = None
        self.payload = {
            "ddAgency": "All Agencies",
            "btnSubmit": "Submit",
        }

    @staticmethod
    def get_cal_agencies():
        agencies = pull_sheet(sheet="sample", url=gc_files["agencies"])
        agencies = agencies[
            ((agencies["exclude"] == "No") | (agencies["clearance_exclude"] == "No"))
            & (agencies["scraper"] == "CA")
        ]
        agencies = dict(zip(agencies["name"], agencies["ori"]))
        return {
            k.upper()
            .replace(" POLICE DEPARTMENT", "")
            .replace("SAN DIEGO COUNTY SHERIFF'S OFFICE", "COUNTY SHERIFF"): v
            for k, v in agencies.items()
        }

    def scrape(self):
        # get months in proper post format
        months = self.get_months()

        # get list of agencies in state from airtable
        self.agencies = self.get_cal_agencies()

        # first request is just a get to retrieve initial asp state params
        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        states = self.get_states(soup)

        # run through months and retrieve data, updating params on each iteration
        records = list()
        for m in months:
            self.logger.info(f"retrieving {m}...")

            # update post data for month
            self.payload.update({"ddBeginDate": m, "ddEndDate": m, **states})
            p = requests.post(self.url, data=self.payload)
            soup = bS(p.text, "lxml")

            # parse data from returned html
            records.extend(self.parse(soup, m))

            # update asp params
            states = self.get_states(soup)

        # update list of oris based on those present across all records
        self.oris.extend(list(set([d["ori"] for d in records])))

        return records

    def get_months(self):
        dates = list()
        years = list(range(self.first.year, self.last.year + 1))
        for year in years:
            months = list(range(1, 13))
            dates.extend([dt(year, month, 1) for month in months])
        return [dt.strftime(d, "%b / %Y") for d in dates if d <= self.last]

    @staticmethod
    def get_states(soup):
        packet = dict()
        for field in [
            "__PREVIOUSPAGE",
            "__VIEWSTATE",
            "__VIEWSTATEGENERATOR",
        ]:
            packet.update({field: soup.find("input", {"name": field})["value"]})
        return packet

    def parse(self, soup, month):
        # retrieve data and pass to df
        table = soup.find("table", {"id": "G_UltraWebTab1xctl00xWebDataGrid1"})
        headers = [th.text.strip() for th in table.find("thead").find_all("th")]
        rows = [
            [td.text.strip() for td in tr.find_all("td")]
            for tr in table.find_all(
                "tr", id=re.compile(r"UltraWebTab1xctl00xWebDataGrid1_r_*")
            )
        ]
        df = pd.DataFrame([dict(zip(headers, row)) for row in rows])

        # only keep relevant crimes
        df = df[df["CRIME"].isin(self.mapping)]
        df[df.columns.difference({"CRIME"})] = df[df.columns.difference({"CRIME"})].map(
            lambda s: int(s.strip("*")) if s != "" else None
        )
        df["CRIME"] = df["CRIME"].map(self.mapping)

        # workaround to deal with partially missing summed-row fields
        # (e.g., `Jul / 2022` for `Coronado`)
        df_stacked = df.groupby("CRIME").transform(
            lambda g: None if g.isna().any() else g.sum()
        )
        df_stacked["CRIME"] = df["CRIME"]
        df_stacked = df_stacked.drop_duplicates("CRIME")

        # reformat df
        df = (
            df_stacked.groupby("CRIME")
            .sum(min_count=1)
            .reset_index()
            .set_index("CRIME")
            .transpose()
            .reset_index()
            .rename(columns={"index": "agency"})
            .rename_axis(None, axis=1)
        )

        # only keep agencies, and map to oris from airtable
        df = df[df["agency"].isin(self.agencies)]
        df["ori"] = df["agency"].map(self.agencies)
        df = df.drop(columns=["agency"])

        # append current month
        df["date"] = dt.strptime(month, "%b / %Y")

        return df.to_dict("records")


California().run()
