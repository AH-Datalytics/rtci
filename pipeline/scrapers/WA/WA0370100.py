import pandas as pd
import requests
import sys

from bs4 import BeautifulSoup as bS

sys.path.append("../../utils")
from super import Scraper


class WA0370100(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["WA0370100"]
        self.url = "https://police.cob.org/pircrimestatistics/CallsForm.aspx"
        self.years = list(range(self.first.year, self.last.year + 1))
        self.mapping = {
            "Homicide": "murder",
            # None: "rape",
            "Robbery": "robbery",
            # None: "aggravated_assault",
            "Burglary (Residential)": "burglary",
            "Theft": "theft",
            "Auto Theft": "motor_vehicle_theft",
        }

    def scrape(self):
        records = list()

        # get url to grab nc form info value and initial asp params
        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        nc = soup.find("input", {"name": "__ncforminfo"})["value"]
        states = self.get_states(soup)

        # update set of years based on what's provided on the site
        self.years = sorted(
            [
                int(option["value"])
                for option in soup.find("select", {"id": "ddlFromYear"}).find_all(
                    "option"
                )
            ]
        )
        self.years = self.years[: self.years.index(self.last.year) + 1]

        for year in self.years:
            self.logger.info(f"collecting {year}...")

            data = {
                "ddlFromYear": year,
                "ddlNeighborhood": 99,
                "btnGo": "Go",
                "__ncforminfo": nc,
            }
            data.update(states)

            # post each year to collect table
            p = requests.post(self.url, data=data)
            soup = bS(p.text, "lxml")

            table = soup.find("table", {"id": "grdTotalCallsReport"})
            headers = [td.text.strip() for td in table.find("tr").find_all("td")]
            rows = [
                [td.text.strip() for td in tr.find_all("td")]
                for tr in table.find_all("tr")[1:]
            ]
            df = pd.DataFrame([dict(zip(headers, row)) for row in rows])

            # format data
            df = (
                df[df["Reported Incidents"].isin(self.mapping)]
                .set_index("Reported Incidents")
                .transpose()
                .reset_index()
                .rename_axis(None, axis=1)
                .rename(columns={"index": "month", **self.mapping})
            )

            df["month"] = pd.to_datetime(df["month"], format="%b").dt.month
            df["year"] = year
            records.extend(df.to_dict("records"))

            # update asp params from year results page
            states = self.get_states(soup)

        return records

    @staticmethod
    def get_states(soup):
        return {
            "__VIEWSTATE": soup.find("input", {"name": "__VIEWSTATE"})["value"],
            "__VIEWSTATEGENERATOR": soup.find(
                "input", {"name": "__VIEWSTATEGENERATOR"}
            )["value"],
            "__EVENTVALIDATION": soup.find("input", {"name": "__EVENTVALIDATION"})[
                "value"
            ],
        }


WA0370100().run()
