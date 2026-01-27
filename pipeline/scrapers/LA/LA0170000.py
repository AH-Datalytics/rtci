import json
import pandas as pd
import requests
import sys

from bs4 import BeautifulSoup as bS

sys.path.append("../../utils")
from crimes import rtci_to_nibrs
from super import Scraper


class LA0170000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["LA0170000"]
        self.url = "https://data.brla.gov/Public-Safety/EBR-Sheriff-s-Office-Crime-Incidents/7y8j-nrht/explore/"
        self.post_url = "https://data.brla.gov/api/v3/views/7y8j-nrht/query.json"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/143.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-App-Token": "U29jcmF0YS0td2VraWNrYXNz0",
        }
        self.limit = 1_000_000
        self.map = {
            k: v
            for e in [
                {d["Offense Code"]: crime for d in rtci_to_nibrs[crime]}
                for crime in rtci_to_nibrs
            ]
            for k, v in e.items()
        }

    def scrape(self):
        r = requests.get(self.url)
        s = bS(r.text, "lxml")
        csrf = s.find("meta", {"name": "csrf-token"})["content"]
        self.headers["X-Csrf-Token"] = csrf

        data = json.dumps(
            {
                "clientContext": {
                    "clientContextVariables": [],
                },
                "page": {
                    "pageNumber": 1,
                    "pageSize": self.limit,
                },
                "parameters": {},
                "query": "SELECT\n  `report_date`,\n  `nibrs_code`\nORDER BY `report_date` DESC NULL FIRST",
            }
        )
        p = requests.post(self.post_url, data=data, headers=self.headers)

        j = json.loads(p.text)
        assert len(j) < self.limit
        df = pd.DataFrame(j)[["report_date", "nibrs_code"]]

        df["report_date"] = pd.to_datetime(df["report_date"])
        df["year"] = df["report_date"].dt.year
        df["month"] = df["report_date"].dt.month
        del df["report_date"]

        df = df[df["nibrs_code"].isin(self.map)]
        df["nibrs_code"] = df["nibrs_code"].map(self.map)
        df = (
            df.groupby(["year", "month", "nibrs_code"])
            .size()
            .reset_index()
            .rename(columns={0: "count"})
        )
        df = (
            df.groupby(["year", "month", "nibrs_code"])["count"]
            .sum()
            .reset_index()
            .pivot(index=["year", "month"], columns="nibrs_code", values="count")
        ).reset_index()

        return df.to_dict("records")


LA0170000().run()
