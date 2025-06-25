import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS
from datetime import datetime as dt

sys.path.append("../../utils")
from pdfs import parse_pdf
from super import Scraper


# TODO: pull in next-year data to handle missing PDF for June 2021


class NY0590300(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["NY0590300"]
        self.url = "https://www.cmvny.com/518/Annual-Reports-Monthly-Crime-Stats-Histo"
        self.mapping = {
            "Murder": "murder",
            "Rape": "rape",
            "Robbery": "robbery",
            "Agg. Assault": "aggravated_assault",
            "Burglary": "burglary",
            "Grand & Petit Larcen": "theft",
            "Grand & Petit Larceny": "theft",
            "G.L.A.": "motor_vehicle_theft",
        }
        self.min_year, self.min_month = None, None

    def scrape(self):
        # get all pdf urls
        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        pdfs = [
            "https://www.cmvny.com" + a["href"]
            for a in soup.find_all("a", href=re.compile(r".*\d{4}-Monthly-Crime-Stats"))
        ]

        # set minimum year and month reported
        self.min_year = min([int(pdf.split("-")[-4]) for pdf in pdfs])
        self.min_month = min(
            [
                dt.strptime(
                    f"{self.min_year}/{pdf.split('/')[-1].split('-')[-5]}", "%Y/%B"
                ).month
                for pdf in pdfs
                if int(pdf.split("-")[-4]) == self.min_year
            ]
        )

        data = list()
        for pdf in pdfs:
            data.extend(self.get_monthly_pdf(pdf))
        return data

    def get_monthly_pdf(self, pdf):
        self.logger.info(f"running: {pdf}")
        doc = parse_pdf(self, pdf, verify=True, pages=1)
        assert len(doc.pages) == 1
        page = doc.pages[0]

        # make sure year and month printed in pdf align with pdf url
        line = [
            line.text.strip()
            for line in page.lines
            if line.text.strip().startswith("REPORT COVERING THE MONTH OF")
        ][0].split(" ")
        month = line[-4].capitalize()
        year = str(max([int(line[-3]), int(line[-1])]))
        assert (
            month == pdf.split("/")[-1].split("-")[0]
            and year == pdf.split("/")[-1].split("-")[1]
        )

        # extract table
        table = page.tables[0]
        rows = list()
        for r in table.rows:
            if "".join([cell.text.strip() for cell in r.cells]).strip() != "":
                rows.append([cell.text.strip() for cell in r.cells])
        header_index = 1
        data_index = 1
        for i, r in enumerate(rows):
            if year in r:
                header_index = i
            if r[0] == "Murder":
                data_index = i
        headers = rows[header_index]
        rows = rows[data_index:]

        # if data from previous year isn't available separately, collect
        if int(year) == self.min_year or (
            dt.strptime(f"{self.min_year}/{month}", "%Y/%B").month < self.min_month
            and int(year) == self.min_year + 1
        ):
            df = (
                pd.DataFrame(rows, columns=headers)
                .iloc[:, :3]
                .rename(columns={"": "crime"})
            )
            df = df[df["crime"].isin(self.mapping)]
            df["crime"] = df["crime"].map(self.mapping)
            df = df.set_index("crime").T.reset_index().rename(columns={"index": "year"})
            df["year"] = df["year"].astype(int)

        # otherwise, just collect current year
        else:
            df = (
                pd.DataFrame(rows, columns=headers)
                .iloc[:, :2]
                .rename(columns={"": "crime", str(year): "count"})
            )
            df = df[df["crime"].isin(self.mapping)]
            df["crime"] = df["crime"].map(self.mapping)
            df = df.set_index("crime").T
            df["year"] = int(year)

        df["month"] = dt.strptime(f"{year}/{month}", "%Y/%B").month
        return df.to_dict("records")


NY0590300().run()
