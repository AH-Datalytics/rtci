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
        self.years = list(range(2020, self.last.year + 1))

    def scrape(self):
        # get url to grab nc form info value and initial asp params
        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        nc = soup.find("input", {"name": "__ncforminfo"})["value"]
        states = self.get_states(soup)

        for year in self.years:
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

            # update asp params from year results page
            states = self.get_states(soup)

            print(headers)
            print(rows[0])

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
