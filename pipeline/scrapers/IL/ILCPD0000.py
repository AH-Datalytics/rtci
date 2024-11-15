import pandas as pd
import requests
import sys

from datetime import datetime as dt
from io import StringIO

sys.path.append("../../utils")
from super import Scraper


class ILCPD0000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["ILCPD0000"]
        self.stem = "https://data.cityofchicago.org/api/views/ijzp-q8t2/rows.csv?query="
        self.crosswalk = {
            d["IUCR"].zfill(4): d["ACTIVE"].lower().replace(" ", "_")
            for d in pd.read_csv(self.crosswalks.ILCPD0000).to_dict("records")
        }

    def scrape(self):
        # get df from csv request against chicago open data
        r = requests.get(
            self.stem + "SELECT"  # 'SELECT'
            "%0A%20%20%60date%60%2C"  # '\n  `date`,'
            "%0A%20%20%60iucr%60"  # '\n  `iucr`'
            "%0AWHERE%20%60date%60"  # '\nWHERE `date`'
            "%0A%20%20%20%20BETWEEN%20"  # '\n    BETWEEN '
            f"%22{dt.strftime(self.first, '%Y-%m-%d')}T00%3A00%3A00%22"  # '"{self.start}T00:00:00"'
            "%20%3A%3A%20floating_timestamp"  # ' :: floating_timestamp'
            "%0A%20%20%20%20AND%20"  # '\n    AND '
            f"%22{dt.strftime(self.last, '%Y-%m-%d')}T23%3A59%3A59%22"  # '"{self.last}T23:59:59"'
            "%20%3A%3A%20floating_timestamp"  # ' :: floating_timestamp'
            "%0AORDER%20BY%20%60date%60%20DESC%20NULL%20FIRST"  # '\nORDER BY `date` DESC NULL FIRST'
            "&fourfour=ijzp-q8t2"
            "&read_from_nbe=true"
            "&version=2.1"
            "&accessType=DOWNLOAD"
        )

        df = pd.read_csv(StringIO(r.text), sep=",", engine="python")
        self.logger.info(f"found {len(df)} results")

        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y %I:%M:%S %p")

        # map IUCR values to crimes from crosswalk source
        df["crime"] = df["IUCR"].map(self.crosswalk)
        df = df[df["crime"].notna()]

        # format df
        df["year"] = pd.to_datetime(df["Date"]).dt.year
        df["month"] = pd.to_datetime(df["Date"]).dt.month
        df = df.groupby(["year", "month"])["crime"].value_counts().reset_index()
        df = df.pivot(
            index=["year", "month"], columns=["crime"], values="count"
        ).reset_index()
        df.index.name = None

        return df.to_dict("records")


ILCPD0000().run()
