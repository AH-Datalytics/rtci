import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS

sys.path.append("../../utils")
from pdfs import parse_pdf
from super import Scraper


class WI0710300(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["WI0710300"]
        self.url = "https://www.oshkoshpd.com/MonthlyCrimeStats/Default.aspx"
        self.mapping = {
            "Homicide": "murder",
            "Sex Offenses": "rape",
            "Aggravated Assault": "aggravated_assault",
            "Robbery": "robbery",
            "Burglary": "burglary",
            "Theft": "theft",
            "Motor Vehicle Theft": "motor_vehicle_theft",
        }

    def scrape(self):
        data = list()

        # get list of pdf urls
        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        hrefs = [
            "https://www.oshkoshpd.com/MonthlyCrimeStats/" + a["href"]
            for a in soup.find("div", {"id": "rightContent"}).find_all(
                "a", href=re.compile(r"CrimeStats.*\.pdf")
            )
        ]

        for href in hrefs:
            # extract year and month from pdf url
            year_month = re.match(r".*CrimeStats(.{3,9}\d{4})\.pdf", href).group(1)
            month = pd.to_datetime(year_month[:-4], format="%B").month
            year = int(year_month[-4:])
            d = {"year": year, "month": month}

            # parse pdf to get crime counts
            doc = parse_pdf(self, href, verify=True)
            assert len(doc.pages) == 1
            page = doc.pages[0]
            tables = page.tables
            assert len(tables) == 1
            table = tables[0]
            for row in table.rows[1:]:
                crime, count = row.cells[0].text.strip().rsplit(" ", 1)
                if crime.replace(".", "") in self.mapping:
                    crime = self.mapping[crime.replace(".", "")]
                    count = int(count.replace("o", "0"))
                    d.update({crime: count})
            data.append(d)

        return data


WI0710300().run()
