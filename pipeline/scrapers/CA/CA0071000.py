import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS
from datetime import datetime as dt

sys.path.append("../../utils")
from pdfs import parse_pdf
from super import Scraper


class CA0071000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["CA0071000"]
        self.url = "https://www.ci.richmond.ca.us/4010/Crime-Stat-Reports"
        self.map = {
            "MURDER": "murder",
            "SEXUAL ASSAULT": "rape",
            "ROBBERY": "robbery",
            "AGGRAVATED ASSAULT": "aggravated_assault",
            "BURGLARY": "burglary",
            "LARCENY-THEFT": "theft",
            "VEHICLE-THEFT": "motor_vehicle_theft",
        }

    def scrape(self):
        data = list()

        # go to site and get list of pdf urls
        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        hrefs = [
            "https://www.ci.richmond.ca.us" + a["href"]
            for a in soup.find_all("a", string=re.compile(r".*Crime([ \-]?)Stat.*"))
        ]

        # convoluted process for extracting year and month from pdf name
        # (includes a bunch of issue handling)
        pdfs = list()
        for h in hrefs:
            year, month = None, None
            d = h.split("/")[-1]
            d = [
                el.lower().strip()
                for sub in [e.split("_") for e in d.split("-")]
                for el in sub
            ]
            d = [el if el != "sept" else "sep" for el in d]
            for el in d:
                if el.isdigit() and len(el) == 4:
                    year = int(el)
                else:
                    for fmt in ("%B", "%b"):
                        try:
                            month = dt.strptime(el, fmt).month
                        except ValueError:
                            continue

            if isinstance(year, int) and year >= 2023:
                pdfs.append((year, month, h))

        for pdf in pdfs:
            # get most recent month from most recent year available
            if pdf[0] == max([p[0] for p in pdfs]) and pdf[1] == max(
                [p[1] for p in pdfs if p[0] == max([p[0] for p in pdfs])]
            ):
                self.logger.info(f"collecting: {pdf[0]}-{pdf[1]}")
                data.extend(self.parse(pdf[2], pdf[0]))

            # otherwise if previous years, just collect end-of-year (december)
            elif pdf[1] == 12:
                self.logger.info(f"collecting: {pdf[0]}-{pdf[1]}")
                data.extend(self.parse(pdf[2], pdf[0]))

        return data

    def parse(self, pdf, year):
        doc = parse_pdf(self, pdf, verify=True, pages=1)
        page = doc.pages[0]
        tables = page.tables
        table = [
            t
            for t in tables
            if t.rows[0].cells[0].text.startswith("CITYWIDE INDEX CRIMES")
        ][0]

        rows = list()
        for r in table.rows:
            rows.append([cell.text.strip() for cell in r.cells])

        headers = rows[0]
        rows = rows[1:]
        df = pd.DataFrame(rows, columns=headers)

        assert df.columns[0] == f"CITYWIDE INDEX CRIMES {year}"
        df = df.rename(columns={f"CITYWIDE INDEX CRIMES {year}": "crime"})

        df = df[df["crime"].isin(self.map)]
        df["crime"] = df["crime"].map(self.map)
        if df.columns[-1].strip().lower() == "ytd total":
            df = df.iloc[:, :-1]
        if "SEPT" in df.columns:
            df = df.rename(columns={"SEPT": "SEP"})

        df = df.set_index("crime").T.reset_index().rename(columns={"index": "month"})
        df["month"] = pd.to_datetime(df["month"], format="%b").dt.month
        df["year"] = year

        return df.to_dict("records")


CA0071000().run()
