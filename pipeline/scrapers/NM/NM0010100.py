import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS

sys.path.append("../../utils")
from super import Scraper


class NM0010100(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["NM0010100"]
        self.url = "https://www.cabq.gov/police/crime-statistics/homicide-statistics"

    def scrape(self):
        data = list()

        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        month_years = soup.find_all("h4", string=re.compile(r".{3,9} \d{4}"))

        for month_year in month_years:
            year = int(month_year.text.strip().split(" ", 1)[-1])
            month = month_year.text.strip().split(" ", 1)[0]
            if month.endswith("."):
                month = pd.to_datetime(month.rstrip("."), format="%b").month
            else:
                month = pd.to_datetime(month, format="%B").month
            counts = month_year.find_next_sibling("p").text.strip()
            count = int(
                re.match(r"\d+ Cases, (\d+) victims \(\d+ solved\)", counts).group(1)
            )
            data.append({"year": year, "month": month, "murder": count})

        return data


NM0010100().run()
