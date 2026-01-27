import json
import pandas as pd
import requests
import sys

from datetime import datetime as dt

sys.path.append("../../utils")
from crimes import rtci_to_nibrs
from super import Scraper


class LA0170200(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["LA0170200"]
        self.stem = "https://data.brla.gov/resource/pbin-pcm7.json?$query="
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
        r = requests.get(
            self.stem + "SELECT"  # 'SELECT'
            "%0A%20%20%60report_date%60%2C"  # '\n  `report_date`,'
            "%0A%20%20%60nibrs_code%60"  # '\n  `nibrs_code`'
            "%0AWHERE"  # '\nWHERE'
            "%0A%20%20caseless_one_of("  # '\n  caseless_one_of('
            "%0A%20%20%20%20%60nibrs_code%60%2C"  # '\n    `nibrs_code`,'
            "%0A%20%20%20%20%2209A%22%2C"  # '\n    "O9A",'
            "%0A%20%20%20%20%2211A%22%2C"  # '\n    "11A",'
            "%0A%20%20%20%20%2213A%22%2C"  # '\n    "13A",'
            "%0A%20%20%20%20%22120%22%2C"  # '\n    "120",'
            "%0A%20%20%20%20%22220%22%2C"  # '\n    "220",'
            "%0A%20%20%20%20%22240%22%2C"  # '\n    "240",'
            "%0A%20%20%20%20%2223A%22%2C"  # '\n    "23A",'
            "%0A%20%20%20%20%2223B%22%2C"  # '\n    "23B",'
            "%0A%20%20%20%20%2223C%22%2C"  # '\n    "23C",'
            "%0A%20%20%20%20%2223D%22%2C"  # '\n    "23D",'
            "%0A%20%20%20%20%2223E%22%2C"  # '\n    "23E",'
            "%0A%20%20%20%20%2223F%22%2C"  # '\n    "23F",'
            "%0A%20%20%20%20%2223G%22%2C"  # '\n    "23G",'
            "%0A%20%20%20%20%2223H%22%2C"  # '\n    "23H",'
            "%0A%20%20%20%20%2211B%22%2C"  # '\n    "11B",'
            "%0A%20%20%20%20%2211C%22"  # '\n    "11C"'
            "%0A%20%20)"  # '\n  )'
            "%0A%20%20AND%20("  # '\n  AND ('
            f"%60report_date%60%20%3E%20"  # '`report_date` > '
            f"%22{dt.strftime(self.first, '%Y-%m-%d')}T00%3A00%3A00%22"  # '"{self.first}T00:00:00"'
            "%20%3A%3A%20floating_timestamp)"  # ' :: floating_timestamp)'
            "%0AORDER%20BY%20%60report_date%60%20"  # '\nORDER BY `report_date` '
            "DESC%20NULL%20FIRST"  # 'DESC NULL FIRST'
            f"%0ALIMIT%20{self.limit}"  # '\nLIMIT {self.limit}'
            "%0AOFFSET%200"  # '\nOFFSET 0'
        )

        j = json.loads(r.text)
        assert len(j) < self.limit
        df = pd.DataFrame(j)

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


LA0170200().run()
