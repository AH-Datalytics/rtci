import pandas as pd
import requests
import sys

from io import StringIO

sys.path.append("../../utils")
from super import Scraper


class WIMPD0000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["WIMPD0000"]
        self.url = "https://data.milwaukee.gov/dataset/e5feaad3-ee73-418c-b65d-ef810c199390/resource/87843297-a6fa-46d4-ba5d-cb342fb2d3bb/download/wibr.csv"
        self.historical_url = "https://data.milwaukee.gov/dataset/5a537f5c-10d7-40a2-9b93-3527a4c89fbd/resource/395db729-a30a-4e53-ab66-faeb5e1899c8/download/wibrarchive.csv"

    def scrape(self):
        # get current-year data
        c = requests.get(self.url).content
        c = pd.read_csv(StringIO(c.decode("utf-8")))

        # get historical data
        h = requests.get(self.historical_url).content
        h = pd.read_csv(StringIO(h.decode("utf-8")), low_memory=False)

        # [JA 2025-02-03]: "only track homicide due to a quirk in how they report"
        df = pd.concat([c, h])
        df = df[["ReportedYear", "ReportedMonth", "Homicide"]]
        df = (
            df.groupby(["ReportedYear", "ReportedMonth"])["Homicide"]
            .sum()
            .reset_index()
            .rename(
                columns={
                    "ReportedYear": "year",
                    "ReportedMonth": "month",
                    "Homicide": "murder",
                }
            )
        )

        return df.to_dict("records")


WIMPD0000().run()
