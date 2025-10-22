import pandas as pd
import requests
import sys

from bs4 import BeautifulSoup as bS
from io import StringIO

sys.path.append("../../utils")
from super import Scraper


class MD0160400(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["MD0160400"]
        self.url = (
            "https://data.montgomerycountymd.gov/api/v3/views/icn6-v9z3/query.json"
        )

    def scrape(self):
        data = (
            '{"clientContext":{"clientContextVariables":[]},"query":"SELECT\n  `date`,\n  `start_date`,\n  `end_date`,'
            '\n  `nibrs_code`,\n  `victims`\nWHERE\n  `start_date`\n    BETWEEN "2025-10-01T00:00:00" :: '
            'floating_timestamp\n    AND "2025-10-21T01:03:54" :: floating_timestamp\n  AND caseless_one_of('
            '`nibrs_code`, "09B", "09C", "13A", "120")\nORDER BY `start_date` DESC NULL FIRST",'
            '"page":{"pageNumber":1,"pageSize":100},"parameters":{}}'
        )
        r = requests.get(
            self.url,
            data=data,
            headers={"X-App-Token": "U29jcmF0YS0td2VraWNrYXNz0"},
        )
        print(r.text)
        df = pd.read_csv(StringIO(r.decode("utf-8")))


MD0160400().run()
