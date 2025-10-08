import numpy as np
import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS

sys.path.append("../../utils")
from pdfs import parse_pdf
from super import Scraper


class NM0260100(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["NM0260100"]
        self.url = "https://santafenm.gov/police/police-criminal-investigations/police-crime-analyst"
        self.mapping = {
            "Homicide Offenses": "murder",
            "Robbery": "robbery",
            "Motor Vehicle Theft": "motor_vehicle_theft",
            "Burglary/Breaking & Entering": "burglary",
            "Larceny/Theft Offenses": "theft",
        }

    def scrape(self):
        records = list()

        # get the most recent pdf
        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        urls = [
            soup.find("a", string=re.compile(r"Crime Statistics for .{3,9} \d{4}"))[
                "href"
            ]
        ]

        # check for any previous end-of-year pdfs
        urls.extend(
            [
                a["href"]
                for a in soup.find_all(
                    "a", string=re.compile(r"Crime Statistics \d{4}")
                )
            ]
        )
        urls = list(set(urls))

        # run through pdfs and grab data
        for url in urls:
            doc = parse_pdf(self, url, verify=True)
            pages = doc.pages
            assert len(pages) == 1
            page = pages[0]
            table = page.tables[0]
            year = int(table.rows[0].cells[0].text.strip())
            headers = [cell.text.strip() for cell in table.rows[0].cells[:-1]]
            rows = [
                [cell.text.strip() for cell in row.cells[:-1]] for row in table.rows[1:]
            ]
            df = pd.DataFrame(rows, columns=headers).rename(
                columns={str(year): "crime"}
            )
            df = df[df["crime"].isin(self.mapping)]
            df["crime"] = df["crime"].map(self.mapping)
            df = (
                df.set_index("crime").T.reset_index().rename(columns={"index": "month"})
            )
            df["month"] = pd.to_datetime(df["month"], format="%b").dt.month
            df = df.replace("", np.nan)
            df = df.astype(float)
            records.extend([{"year": year, **d} for d in df.to_dict("records")])

        return records


NM0260100().run()
