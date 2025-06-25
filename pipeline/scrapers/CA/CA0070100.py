import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS
from datetime import datetime as dt

sys.path.append("../../utils")
from pdfs import parse_pdf
from super import Scraper


class CA0070100(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["CA0070100"]
        self.url = "https://www.antiochca.gov/police/crime-statistics/"
        self.hist_url = (
            "https://www.antiochca.gov/police/crime-statistics/crime-statistics/"
        )
        self.legacy_map = {
            "HOMI": "murder",
            "RAPE": "rape",
            "AGR ASSAULT": "aggravated_assault",
            "AGGRAVATED ASSAULT": "aggravated_assault",
            "ROBB": "robbery",
            "ROBBERY": "robbery",
            "BURG": "burglary",
            "THEFT": "theft",
            "MVTHEFT": "motor_vehicle_theft",
        }
        self.nibrs_map = {
            "Murder": "murder",
            "Rape": "rape",
            "Robbery": "robbery",
            "Aggravated Assault": "aggravated_assault",
            "Burglary": "burglary",
            "Larceny": "theft",
            "Motor Vehicle Theft": "motor_vehicle_theft",
        }
        self.discards = ["total", "totals", "ytd"]

    def scrape(self):
        # get current year data
        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        match = int(
            (
                soup.find(
                    "h3", string=re.compile(r"City of Antioch \d{4} Crime Statistics")
                )
                .text.strip()
                .split(" ")
            )[3]
        )
        assert match == self.last.year
        table = soup.find("table")
        headers = [td.text.strip() for td in table.find("tr").find_all("td")]
        rows = [
            [td.text.strip() for td in tr.find_all("td")]
            for tr in table.find_all("tr")[1:]
        ]
        df = pd.DataFrame(rows, columns=headers)
        df = df[df["GROUP A CRIMES"].isin(self.nibrs_map)]
        df["GROUP A CRIMES"] = df["GROUP A CRIMES"].map(self.nibrs_map)
        df = (
            df.set_index("GROUP A CRIMES")
            .T.reset_index()
            .rename(columns={"index": "month"})
        )
        df["month"] = df["month"].apply(lambda s: s.capitalize())
        df["month"] = pd.to_datetime(df["month"], format="%b").dt.month
        df["year"] = self.last.year
        data = df.to_dict("records")

        # get urls of pdfs of previous years' data
        r = requests.get(self.hist_url)
        soup = bS(r.text, "lxml")
        pdfs = [
            a["href"]
            for a in soup.find_all("a", string=re.compile(r"Year \d{4}"))
            if self.first.year <= int(a.text.strip().split(" ")[-1]) <= self.last.year
        ]

        # run through historical pdfs
        for pdf in pdfs:
            self.logger.info(f"collecting: {pdf}")
            year = int(pdf.split("/")[-1].split("-")[-1].split(".")[0])
            if "nbrs-" in pdf:
                data.extend(self.get_yearly_pdf(pdf, year))
            else:
                data.extend(self.get_yearly_pdf(pdf, year, nibrs=False))

        return data

    def get_yearly_pdf(self, pdf, year, nibrs=True):
        doc = parse_pdf(self, pdf, verify=True)
        assert len(doc.pages) == 1
        page = doc.pages[0]

        if nibrs:
            tables = page.tables
            assert len(tables) == 1
            table = tables[0]

            rows = list()
            for r in table.rows:
                rows.append([cell.text.strip() for cell in r.cells])
            headers = rows[0]
            rows = rows[1:]
            df = pd.DataFrame(rows, columns=headers)
            df = df[df["GROUP A CRIMES"].isin(self.nibrs_map)]
            df["GROUP A CRIMES"] = df["GROUP A CRIMES"].map(self.nibrs_map)
            if df.columns[-1].strip().lower() in self.discards:
                df = df.iloc[:, :-1]
            df = (
                df.set_index("GROUP A CRIMES")
                .T.reset_index()
                .rename(columns={"index": "month"})
            )
            df["month"] = df["month"].apply(lambda s: s.capitalize())
            df["month"] = pd.to_datetime(df["month"], format="%b").dt.month
            df["year"] = year
            return df.to_dict("records")

        else:
            tables = page.tables
            assert len(tables) == 1
            table = tables[0]

            rows = list()
            for r in table.rows:
                rows.append([cell.text.strip() for cell in r.cells])
            rows = [r for r in rows if "".join(r) != ""]
            headers = rows[0]
            rows = rows[1:]
            df = pd.DataFrame(rows, columns=headers)
            df = df.rename(columns={"": "crime"})
            df = df[df["crime"].str.contains(str(year))]
            df["crime"] = df["crime"].apply(
                lambda s: s.strip("*").replace(str(year), "").replace("-", "").strip()
            )
            df = df[df["crime"].isin(self.legacy_map)]
            df["crime"] = df["crime"].map(self.legacy_map)
            if df.columns[-1].strip().lower() in self.discards:
                df = df.iloc[:, :-1]
            df = (
                df.set_index("crime").T.reset_index().rename(columns={"index": "month"})
            )
            df["month"] = df["month"].apply(lambda s: s.capitalize())
            df["month"] = pd.to_datetime(df["month"], format="%b").dt.month
            df["year"] = year
            return df.to_dict("records")


CA0070100().run()
