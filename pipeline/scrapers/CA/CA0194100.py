import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS
from datetime import datetime as dt

sys.path.append("../../utils")
from pdfs import parse_pdf
from super import Scraper


class CA0194100(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["CA0194100"]
        self.url = "https://www.longbeach.gov/police/crime-info/crime-statistics/"
        self.url = "https://www.longbeach.gov/police/crime-info/crime-statistics/crime-statistics-archive/"
        self.nibrs_mapping = {
            "Murder": "murder",
            "Rape / Sexual Assault": "rape",
            "Aggravated Assault": "aggravated_assault",
            "Robbery": "robbery",
            "Residential": "burglary",
            "Garage": "burglary",
            "Commercial": "burglary",
            "Other": "burglary",
            "Auto Burglary": "theft",
            "Grand Theft": "theft",
            "Petty Theft < $950": "theft",
            "Bike Theft": "theft",
            "Motor Vehicle Theft": "motor_vehicle_theft",
        }
        self.ucr_mapping = {
            "Murder": "murder",
            "Rape": "rape",
            "Robbery": "robbery",
            "Agg Assault": "aggravated_assault",
            "Res Burg": "burglary",
            "Garage Burg": "burglary",
            "Comm Burg": "burglary",
            "Auto Burg": "theft",
            "Grand Theft": "theft",
            "Petty Theft >$50": "theft",
            "Petty Theft <$50": "theft",
            "Bike Theft": "theft",
            "GTA": "motor_vehicle_theft",
        }

    def scrape(self):
        r = requests.get(self.url, verify=True)
        soup = bS(r.text, "lxml")

        # get post-2022 nibrs pdfs
        nibrs = soup.find("h3", string=re.compile(r"NIBRS Monthly Crime Statistics"))
        nibrs = self.href_extract(nibrs, ["p", "div"], "hr")
        nibrs = [
            n
            for n in nibrs
            if int(re.match(r".*(\d{4}).*", n).group(1)) >= self.first.year
        ]

        # get pre-2023 ucr pdfs
        ucr = soup.find("h3", string=re.compile(r"PREVIOUS YEAR TO CURRENT YEAR"))
        ucr = self.href_extract(ucr, ["p", "div"], "hr")
        ucr = [u for u in ucr if "2016" not in u]

        data = list()
        for pdf in nibrs:
            data.extend(self.parse_nibrs(pdf))
        for pdf in ucr:
            data.extend(self.parse_ucr(pdf))
        return data

    def parse_ucr(self, pdf):
        doc = parse_pdf(self, pdf, verify=True, pages=1)
        assert len(doc.pages) == 1
        page = doc.pages[0]

        date = None
        for line in page.lines:
            if re.match(r"^([A-Za-z]+\s\d{4})$", line.text.strip()):
                date = re.match(r"^([A-Za-z]+\s\d{4})$", line.text.strip()).group(1)
        month, year = date.capitalize().split()
        self.logger.info(f"date found: {year} {month}")

        rows = list()
        for t in page.tables:
            rows.extend([[cell.text.strip() for cell in row.cells] for row in t.rows])
        assert "YTD" in rows[0] and "#" in rows[1]
        df = (
            pd.DataFrame(rows[2:], columns=rows[1])
            .iloc[:, 1:3]
            .rename(columns={"": "crime", str(year): "count"})
        )
        df = df[df["crime"].isin(self.ucr_mapping)]
        df["crime"] = df["crime"].map(self.ucr_mapping)
        df["count"] = df["count"].apply(lambda s: int(s.replace(",", "")))
        df = df.groupby("crime")["count"].sum().reset_index()
        df = df.set_index("crime").T
        df["year"] = int(year)
        df["month"] = dt.strptime(f"{year}/{month.capitalize()}", "%Y/%B").month
        return df.to_dict("records")

    def parse_nibrs(self, pdf):
        doc = parse_pdf(self, pdf, verify=True, pages=1)
        assert len(doc.pages) == 1
        page = doc.pages[0]
        date = re.match(
            r".*\sCRIME\sCATEGORY\s([A-Za-z]+\s\d{4})\sYTD\s.*",
            " ".join(page.text.split("\n")),
        ).group(1)
        month, year = date.split()
        self.logger.info(f"date found: {year} {month}")

        rows = list()

        for t in page.tables:
            rows.extend([[cell.text.strip() for cell in row.cells] for row in t.rows])
        df = (
            pd.DataFrame(rows[2:], columns=rows[1])
            .iloc[:, 1:3]
            .rename(columns={"": "crime", str(year): "count"})
        )
        df = df[df["crime"].isin(self.nibrs_mapping)]
        df["crime"] = df["crime"].map(self.nibrs_mapping)
        df["count"] = df["count"].astype(int)
        df = df.groupby("crime")["count"].sum().reset_index()
        df = df.set_index("crime").T
        df["year"] = int(year)
        df["month"] = dt.strptime(f"{year}/{month.capitalize()}", "%Y/%B").month

        return df.to_dict("records")

    @staticmethod
    def href_extract(tag, sibling_tags, break_tag):
        siblings = list()
        for sibling in tag.next_siblings:
            if sibling.name == break_tag:
                break
            elif sibling.name in sibling_tags:
                siblings.append(sibling)
        hrefs = [
            element["href"]
            for sublist in [sibling.find_all("a") for sibling in siblings]
            for element in sublist
        ]
        for idx, href in enumerate(hrefs):
            if href.startswith("/"):
                hrefs[idx] = "https://www.longbeach.gov" + href
            elif href.startswith("http://"):
                hrefs[idx] = href.replace("http://", "https://www.")
            else:
                hrefs[idx] = "https://www.longbeach.gov/" + href
        return hrefs


CA0194100().run()
