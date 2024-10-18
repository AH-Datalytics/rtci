import json
import requests
import sys

sys.path.append("../utils")
from super import Scraper


class ILCPD0000(Scraper):
    def __init__(self):
        super().__init__()
        self.path = "il/cdp0000/"
        self.offense_ids = {
            "09A": "murder",
            "11A,11B,11C": "rape",
            "120": "robbery",
            "13A": "aggravated_assault",
            "220": "burglary",
            "23A,23B,23C,23D,23E,23F,23G,23H": "theft",
            "240": "motor_vehicle_theft",
        }
        self.api_url = (
            "https://data.cityofchicago.org/resource/ijzp-q8t2.json?year={}&fbi_code={}"
        )

    def scrape(self):
        offenses = [
            ele for sub in [s.split(",") for s in self.offense_ids] for ele in sub
        ]
        for year in range(2018, 2025):
            for offense in offenses:
                print(year, offense)
                url = self.api_url.format(year, offense)
                print(url)
                r = requests.get(url)
                data = json.loads(r.text)
                print(len(data))
                print(data[0])


ILCPD0000().run()
