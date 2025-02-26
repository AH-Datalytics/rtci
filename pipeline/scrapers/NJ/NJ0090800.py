import json
import requests
import sys

from datetime import datetime as dt

sys.path.append("../../utils")
from super import Scraper


class NJ0090800(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["NJ0090800"]
        self.url = "https://www.northbergenpolice.com/report/datasets/_scripts/Crime-Statistics.json"
        self.mapping = {
            "Homicide": "murder",
            "Rape": "rape",
            "Robbery": "robbery",
            "Aggression Assault": "aggravated_assault",
            "Burglary": "burglary",
            "Larceny": "theft",
            "Auto Theft": "motor_vehicle_theft",
        }

    def scrape(self):
        r = requests.get(self.url)
        r.encoding = "utf-8-sig"
        data = json.loads(r.text)

        records = list()
        for d in data:
            y = d["Year"]
            rows = d["DataMonths"]
            for r in rows:
                m = dt.strptime(r["Month"], "%B").month
                dat = {
                    self.mapping[k]: v
                    for k, v in r["Data"].items()
                    if k in self.mapping
                }
                dat.update({"year": y, "month": m})
                records.append(dat)

        return records


NJ0090800().run()
