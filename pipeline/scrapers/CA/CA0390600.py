import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS

sys.path.append("../../utils")
from pdfs import parse_pdf
from super import Scraper


class CA0390600(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["CA0390600"]
        self.url = "https://tracypd.com/crime-mapping"
        self.mapping = {
            "CRIMINAL HOMICIDE": "murder",
            "FORCIBLE RAPE": "rape",
            "ROBBERY": "robbery",
            "AGGRAVATED ASSAULT": "aggravated_assault",
            "BURGLARY": "burglary",
            "LARCENY-THEFT": "theft",
            "ILARCENY-THEFT": "theft",
            "MOTOR VEHICLE THEFT": "motor_vehicle_theft",
        }

    def scrape(self):
        # get all pdf urls
        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        pdfs = [
            a["href"]
            for a in soup.find("table", {"id": "dlp_ea1e8a2f8f07d5d0_1"}).find_all(
                "a", href=re.compile(r".*\.pdf")
            )
        ]

        data = list()
        for pdf in pdfs:
            data.extend(self.get_monthly_pdf(pdf))
        df = pd.DataFrame(data)
        duplicates = df[df.duplicated(subset=["year", "month"], keep=False)]
        assert len(duplicates) == 0
        return df.to_dict("records")

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
        assert rows[0][0] == "Categories"
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df["Categories"] = df["Categories"].apply(lambda s: self.check_mapping(s))
        df = df[df["Categories"].isin(self.mapping)]
        assert len(df) == 7, self.logger.error(df)
        df["Categories"] = df["Categories"].map(self.mapping)
        df = df[[df.columns[0], df.columns[2]]]
        df = df.set_index("Categories").T.reset_index()
        for col in df.columns:
            if col in self.mapping.values():
                df[col] = (
                    df[col]
                    .str.replace(r"\D", "", regex=True)
                    .apply(lambda s: self.convert(s))
                )
        df["month"] = pd.to_datetime(
            df["index"].apply(lambda s: s.split("-")[0]), format="%b"
        ).dt.month
        df["year"] = pd.to_datetime(
            df["index"].apply(lambda s: s.split("-")[1]), format="%y"
        ).dt.year
        del df["index"]
        return df.to_dict("records")

    def check_mapping(self, s):
        for k in self.mapping:
            if s.startswith(k):
                return k

    @staticmethod
    def convert(s):
        try:
            return float(s)
        except ValueError:
            return None


CA0390600().run()
