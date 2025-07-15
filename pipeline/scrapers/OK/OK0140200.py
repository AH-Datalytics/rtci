import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS

sys.path.append("../../utils")
from crimes import rtci_to_nibrs
from super import Scraper


class OK0140200(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["OK0140200"]
        self.url = "https://www.normanok.gov/public-safety/police-department/open-data-portal/offenses"

        # set mapping of NIBRS codes
        self.mapping = dict()
        for category in rtci_to_nibrs:
            for crime in rtci_to_nibrs[category]:
                self.mapping[crime["Offense Code"]] = category

    def scrape(self):
        data = list()

        # get list of xlsx file urls
        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        urls = [
            "https://www.normanok.gov" + a["href"]
            for a in soup.find_all(
                "a", string=re.compile(r"Case Offenses Data Set - \d{4}.*")
            )
        ]

        # run through urls and collect data
        for url in urls:
            df = pd.read_excel(url)[["ReportedDate", "Counts", "IBRCrimeCode"]]
            df["ReportedDate"] = pd.to_datetime(df["ReportedDate"])
            df["year"] = df["ReportedDate"].dt.year
            df["month"] = df["ReportedDate"].dt.month
            del df["ReportedDate"]
            df = df[df["IBRCrimeCode"].isin(self.mapping)]
            df["crime"] = df["IBRCrimeCode"].map(self.mapping)
            del df["IBRCrimeCode"]
            df = df.groupby(["year", "month", "crime"])["Counts"].sum().reset_index()

            df = df.pivot(
                index=["year", "month"], columns="crime", values="Counts"
            ).reset_index()

            # manually fill na with 0 in this case
            for crime in rtci_to_nibrs:
                df[crime] = df[crime].fillna(0)

            data.extend(df.to_dict("records"))

        return data


OK0140200().run()
