import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS
from datetime import datetime as dt
from datetime import timedelta as td

sys.path.append("../../utils")
from pdfs import parse_pdf
from super import Scraper


class CA0190100(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["CA0190100"]
        self.url = "https://www.alhambraca.gov/271/Crime-Statistics"
        self.latest_year, self.latest_month = None, None
        self.mapping = {
            "MURDER": "murder",
            "FORCIBLE RAPE": "rape",
            "AGGRAVATED ASSAULT": "aggravated_assault",
            "ROBBERY": "robbery",
            "BURGLARY": "burglary",
            "LARCENCY/THEFT": "theft",
            "GRAND THEFT AUTO": "motor_vehicle_theft",
        }

    def scrape(self):
        r = requests.get(self.url, verify=True)
        soup = bS(r.text, "lxml")
        pdfs = [
            "https://www.cityofalhambra.org/" + a["href"]
            if a["href"].endswith("-PDF")
            else "https://www.cityofalhambra.org/" + a["href"] + "-"
            for a in soup.find_all("a", {"class": "fileType pdf"})
        ]
        pdfs = [
            p
            for p in pdfs
            if dt(
                int(p.split("-")[-3]),
                dt.strptime(p.split("-")[-4].split("/")[-1], "%B").month,
                1,
            )
            >= self.first
        ]

        # data for the second-to-most-recent month
        # is only maintained in the most recent pdf
        # (which contains 2 months-worth of data)
        # so there must be a unique extraction for
        # the most recent pdf
        latest = [
            (
                int(pdf.split("-")[-3]),
                dt.strptime(pdf.split("-")[-4].split("/")[-1], "%B").month,
            )
            for pdf in pdfs
        ]

        self.latest_year = max([v[0] for v in latest])
        self.latest_month = max([v[1] for v in latest if v[0] == self.latest_year])
        assert (
            self.latest_year == self.last.year
            and abs(self.latest_month - self.last.month) <= 1
        )
        self.latest_month = dt.strftime(
            dt(self.latest_year, self.latest_month, 1, 0, 0), "%B"
        )
        self.latest_year = str(self.latest_year)

        data = list()
        for pdf in pdfs:
            data.extend(self.get_monthly_pdf(pdf))

        # drop duplicates on year/month from getting previous month data in pdfs
        df = pd.DataFrame(data)
        df[["year", "month"]] = df[["year", "month"]].astype(int)
        df = df.drop_duplicates(["year", "month"])
        df = df.sort_values(by=["year", "month"])
        data = df.to_dict("records")
        return data

    def get_monthly_pdf(self, pdf):
        doc = parse_pdf(self, pdf, verify=True)
        assert len(doc.pages) == 1
        page = doc.pages[0]
        rows = page.text.split("\n")
        month, year = [r for r in rows if re.match(r"^[a-zA-Z]+\s\d{4}$", r)][0].split(
            " "
        )

        tables = page.tables
        assert len(tables) == 1
        table = tables[0]

        valid = list()
        for r in table.rows:
            valid.append([cell.text.strip() for cell in r.cells])
        valid = [row for row in valid if row[0] != ""]
        headers = valid[0]
        valid = valid[1:]
        df = pd.DataFrame(valid, columns=headers)

        # handle case of the most recent month
        # (extracting previous month in addition)
        if year == self.latest_year and month == self.latest_month:
            prev = dt.strptime(f"{year}/{month}/1", "%Y/%B/%d") - td(days=1)
            prev_year = prev.year
            prev_month = dt.strftime(prev, "%B")
            df = df[
                [
                    "GROUP A OFFENSES",
                    f"{prev_month.upper()} {prev_year}",
                    f"{month.upper()} {year}",
                ]
            ]
            df = df[df["GROUP A OFFENSES"].isin(self.mapping)]
            df["GROUP A OFFENSES"] = df["GROUP A OFFENSES"].map(self.mapping)
            df = (
                df.rename(
                    columns={
                        "GROUP A OFFENSES": "crime",
                    }
                )
                .set_index("crime")
                .T.reset_index()
                .rename(columns={"index": "date"})
            )
            df["date"] = df["date"].apply(
                lambda s: dt.strptime(s.capitalize(), "%B %Y")
            )
            df["year"] = df["date"].dt.year
            df["month"] = df["date"].dt.month
            df = df.drop(columns=["date"])
            return df.to_dict("records")

        # handle all other months (only take one column)
        else:
            df = df[["GROUP A OFFENSES", f"{month.upper()} {year}"]]
            df = df[df["GROUP A OFFENSES"].isin(self.mapping)]
            df["GROUP A OFFENSES"] = df["GROUP A OFFENSES"].map(self.mapping)
            df = df.rename(
                columns={
                    "GROUP A OFFENSES": "crime",
                    f"{month.upper()} {year}": "count",
                }
            )
            df["year"] = year
            df["month"] = month
            df["month"] = pd.to_datetime(df["month"], format="%B").dt.month
            records = (
                df.pivot(
                    index=["year", "month"],
                    columns="crime",
                    values="count",
                )
                .reset_index()
                .to_dict("records")
            )

            return records


CA0190100().run()
