import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS
from datetime import datetime as dt

sys.path.append("../../utils")
from pdfs import parse_pdf
from super import Scraper


class CA0390500(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["CA0390500"]
        self.url = (
            "https://www.stocktonca.gov/services/police_department/police_news___information"
            "/statistical_reports.php#outer-629"
        )
        self.mapping = {
            "homicide": "murder",
            "criminal homicide": "murder",
            "forcible rape": "rape",
            "aggravated assault": "aggravated_assault",
            "robbery": "robbery",
            "burglary": "burglary",
            "larceny/theft": "theft",
            "larceny-theft": "theft",
            "motor vehicle theft": "motor_vehicle_theft",
        }
        self.max_year, self.max_month = None, None
        self.alt = False
        self.date_pattern = (
            r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug("
            r"?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[_ ](\d{4})"
        )

    def scrape(self):
        # get all pdf urls
        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        pdfs = [
            "https://cms3.revize.com/revize/stockton/" + a["href"]
            for a in soup.find_all("a", href=re.compile(r".*Statistical.*\d{4}.*\.pdf"))
            if int(re.match(r".*(\d{4}).*\.pdf", a["href"]).group(1)) >= self.first.year
        ]

        self.max_year = max(
            [int(re.match(r".*(\d{4}).*\.pdf", pdf).group(1)) for pdf in pdfs]
        )

        self.max_month = max(
            [
                self.extract_month(
                    re.search(self.date_pattern, pdf, re.IGNORECASE).group(1)
                ).month
                for pdf in pdfs
                if str(self.max_year) in pdf
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

        # extract table
        table = page.tables[0]
        rows = list()
        for r in table.rows:
            if "".join([cell.text.strip() for cell in r.cells]).strip() != "":
                rows.append([cell.text.strip() for cell in r.cells])
        assert rows[0][0] == "Incident Type" or rows[0][0] == "Categories"
        df = pd.DataFrame(rows[1:], columns=rows[0]).iloc[:, :3]
        if "Categories" in df.columns:
            self.alt = True
        df = df.rename(columns={"Incident Type": "Categories"})
        df["Categories"] = df["Categories"].str.lower()
        df = df[df["Categories"].isin(self.mapping)]
        df["Categories"] = df["Categories"].map(self.mapping)
        assert len(df) == 7, self.logger.error(df)
        df = df.set_index("Categories").T.reset_index()

        if self.alt:
            df["month"] = pd.to_datetime(df["index"], format="%b-%y").dt.month
            df["year"] = pd.to_datetime(df["index"], format="%b-%y").dt.year
        else:
            df["month"] = pd.to_datetime(df["index"], format="%B %Y").dt.month
            df["year"] = pd.to_datetime(df["index"], format="%B %Y").dt.year
        del df["index"]

        if (
            len(df[(df["year"] == self.max_year) & (df["month"] == self.max_month)])
            == 0
        ):
            df = df[df["year"] == min(df["year"])]
            df = df[df["month"] == min(df["month"])]

        return df.to_dict("records")

    def extract_month(self, s):
        for form in ["%B", "%b"]:
            try:
                return dt.strptime(f"{self.max_year}/{s}", f"%Y/{form}")
            except ValueError:
                self.logger.error(f"unidentified month format: {s}")
        raise ValueError(f"unidentified month format: {s}")


CA0390500().run()
