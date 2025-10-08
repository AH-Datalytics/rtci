import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS

sys.path.append("../../utils")
from pdfs import parse_pdf
from super import Scraper


class AR0600200(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["AR0600200"]
        self.offenses = {
            "All Homicide Offenses": "murder",
            "Forcible Rape": "rape",
            "Robbery": "robbery",
            "Aggravated Assault": "aggravated_assault",
            "Burglary/B & E": "burglary",
            "Larceny": "theft",
            "Stolen Vehicle": "motor_vehicle_theft",
        }
        self.url = "https://www.littlerock.gov/residents/police-department/crime-stats/"
        self.headers = [
            "OFFENSE",
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
            "TOTAL",
        ]

    def scrape(self):
        # find most recent pdf
        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        href = (
            "https://www.littlerock.gov"
            + soup.find("a", href=re.compile(r".*/part-i-offenses-by-month-.*"))["href"]
        )
        self.logger.info(f"located url: {href}")

        # send pdf parse job to aws textract
        doc = parse_pdf(self, href, verify=True)

        # make sure page has a valid table and extract year
        records = list()
        for p, page in enumerate(doc.pages):
            if (
                page.tables
                and len(page.tables) == 1
                and "Part I" not in str(page)
                and "Part Offenses by Month" not in str(page)
            ):
                assert re.match(r"\d{4}", page.lines[0].text)
                year = page.lines[0].text

                if int(year) < self.first.year:
                    break

                # extract table from page
                table = page.tables[0]
                idx = [
                    r
                    for r, row in enumerate(table.rows)
                    if row.cells[0].text.strip() == "OFFENSE"
                ]
                assert len(idx) == 1, self.logger.error(
                    f"issue identifying row index of table headers:\n\n{page}"
                )
                idx = idx[0]
                rows = table.rows[idx:]
                assert [
                    cell.text.strip() for cell in rows[0].cells
                ] == self.headers, self.logger.error(
                    f"pattern matching error:\n\n{table}"
                )

                # extract rows from table
                dfs = list()
                for r, row in enumerate(table.rows[1:]):
                    if row.cells[0].text.strip() in self.offenses:
                        crime = self.offenses[row.cells[0].text.strip()]
                        df = pd.DataFrame(
                            [
                                {
                                    "year": year,
                                    "month": tup[0],
                                    "crime": crime,
                                    "count": tup[1],
                                }
                                for tup in list(
                                    zip(
                                        list(range(1, 13)),
                                        [cell.text.strip() for cell in row.cells[1:-1]],
                                    )
                                )
                            ]
                        )

                        dfs.append(df)

                # stitch together individual crime dataframes
                df = pd.concat(dfs)
                df = df.pivot(
                    index=["year", "month"],
                    columns="crime",
                    values="count",
                ).reset_index()
                records.append(df)

        # stitch together all years and return
        df = pd.concat(records)
        return df.to_dict("records")


AR0600200().run()
