import pandas as pd
import re
import sys

from bs4 import BeautifulSoup as bS
from datetime import datetime as dt

sys.path.append("../../utils")
from pdfs import parse_pdf
from requests_configs import tls_mimic
from super import Scraper


class CA0302400(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["CA0302400"]
        self.url = (
            "https://www.westminster-ca.gov/departments/police/services/investigations-bureau/crime-analysis"
            "/crime-statistics"
        )
        self.hist_url = (
            "https://www.westminster-ca.gov/departments/police/services/investigations-bureau/crime-analysis"
            "/crime-statistics/-folder-110#docfold_1113_1695_507_110"
        )
        self.new_map = {
            "HOMICIDE": "murder",
            "RAPE": "rape",
            "ROBBERY": "robbery",
            "AGGRAVATED ASSAULT": "aggravated_assault",
            "BURGLARY": "burglary",
            "LARCENY": "theft",
            "STOLEN VEHICLE": "motor_vehicle_theft",
        }
        self.old_map = {
            k.title().replace("Aggravated Assault", "AggravatedAssault"): v
            for k, v in self.new_map.items()
        }

    def scrape(self):
        # get most recent year data
        r = tls_mimic(self.url)
        soup = bS(r.text, "lxml")
        table = soup.find("table").find("tbody")
        headers = [td.text.strip() for td in table.find("tr").find_all("td")]
        rows = [
            [td.text.strip() for td in tr.find_all("td")]
            for tr in table.find_all("tr")[1:]
        ]
        assert re.fullmatch(
            r"\d{4}", headers[0]
        ), f"first cell does not contain year in appropriate format: {headers[0]}"
        year = int(headers[0])

        df = pd.DataFrame(rows, columns=headers)
        data = self.parse_new_df(year, df)
        self.logger.info(f"collected: {year}")

        # get previous years' data
        r = tls_mimic(self.hist_url)
        soup = bS(r.text, "lxml")

        hrefs = [
            (
                int(re.search(r".*(\d{4}).*", a.text.strip()).group(1)),
                "https://www.westminster-ca.gov" + a["href"],
            )
            for a in soup.find_all("a", string=re.compile(r".*\d{4} .*Crime.*"))
        ]
        hrefs = [h for h in hrefs if h[0] >= self.first.year]

        for pdf in hrefs:
            self.logger.info(f"attempting: {pdf[0]}")
            doc = parse_pdf(self, pdf[1], mimic=True)
            pages = doc.pages
            assert len(pages) == 1
            page = pages[0]
            tables = page.tables
            assert len(tables) == 1
            table = tables[0]

            rows = list()
            for r in table.rows:
                rows.append([cell.text.strip() for cell in r.cells])
            headers = rows[0]
            rows = rows[1:]
            df = pd.DataFrame(rows, columns=headers)

            # different table structures in pdfs depending on year (before 2020)
            if pdf[0] >= 2020:
                data.extend(self.parse_new_df(pdf[0], df))
            else:
                data.extend(self.parse_old_df(pdf[0], df))

        return data

    def parse_new_df(self, year, df):
        df = df.rename(columns={str(year): "month"})
        df = df[["month"] + list(self.new_map.keys())]
        df = df.rename(columns=self.new_map)
        df = df[df["month"] != "TOTAL"]
        df["month"] = pd.to_datetime(df["month"], format="%B").dt.month
        df["year"] = year
        return df.to_dict("records")

    def parse_old_df(self, year, df):
        if list(df.columns)[0] in ["Crime", "Crime/Month", str(year)]:
            df = df.rename(columns={df.columns[0]: "crime"})
        if "Sept" in df.columns:
            df = df.rename(columns={"Sept": "Sep"})
        df = df.set_index("crime").T.reset_index().rename(columns={"index": "month"})
        df = df[["month"] + list(self.old_map.keys())]
        df = df.rename(columns=self.old_map)
        df = df[~df["month"].isin(["Total", "Grand Total"])]
        df["month"] = df["month"].apply(lambda s: self.month_format(s))
        df["year"] = year
        return df.to_dict("records")

    @staticmethod
    def month_format(s):
        try:
            return dt.strptime(s, "%b").month
        except ValueError:
            return dt.strptime(s, "%B").month


CA0302400().run()
