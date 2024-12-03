import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS
from datetime import datetime as dt

sys.path.append("../../utils")
from super import Scraper


class KY0340200(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["KY0340200"]
        self.url = "https://www.lexingtonky.gov/crime-data"
        self.archive_url = "https://www.lexingtonky.gov/crime-data-archive"
        self.mapping = {
            "Murder": "murder",
            "Forcible Rape": "rape",
            "Robbery": "robbery",
            "Aggravated Assault": "aggravated_assault",
            "Breaking & Entering": "burglary",
            "Larceny - Theft": "theft",
            "Auto Theft": "motor_vehicle_theft",
        }

    def process_url(self, url):
        records = list()

        r = requests.get(url)
        soup = bS(r.text, "lxml")

        # collect yearly tables
        tables = [
            table
            for table in soup.find_all("table", {"class": "tg"})
            if table.find("th", string=re.compile(r"\d{4}\s.*Part I Offenses by Month"))
        ]

        # for each table, parse data
        for table in tables:
            # collect current table's year
            year = int(table.find("tr").text.split()[0])

            # collect table to df
            headers = [
                td.text.strip()
                for td in table.find_all("tr")[1]
                if td.text.strip() != ""
            ]
            rows = [
                [td.text.strip() for td in tr if td.text.strip() != ""]
                for tr in table.find_all("tr")[2:]
            ]
            df = pd.DataFrame([dict(zip(headers, row)) for row in rows])

            # handle crimes and formatting
            df = df[df["Incident Type"].isin(self.mapping)]
            df["Incident Type"] = df["Incident Type"].map(self.mapping)
            if "Total" in df.columns:
                df = df.drop(columns=["Total"])
            df = (
                df.set_index("Incident Type")
                .T.reset_index()
                .rename(columns={"index": "date"})
            )

            # handle date
            df["date"] = df["date"].apply(lambda s: dt.strptime(f"{s}{year}", "%b%Y"))

            records.extend(df.to_dict("records"))

        return records

    def scrape(self):
        # first, handle primary url
        records = self.process_url(self.url)

        # second, handle archive url
        records.extend(self.process_url(self.archive_url))

        return records


KY0340200().run()
