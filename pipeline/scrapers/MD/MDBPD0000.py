import numpy as np
import pandas as pd
import requests
import sys

from io import StringIO

sys.path.append("../../utils")
from super import Scraper


class MDBPD0000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["MDBPD0000"]
        self.url = (
            "https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/Part1_Crime_Beta/FeatureServer"
            "/replicafilescache/Part1_Crime_Beta_5960161298247612570.csv"
        )

    def scrape(self):
        # get csv from source
        r = requests.get(self.url).content
        df = pd.read_csv(StringIO(r.decode("utf-8")), low_memory=False)  # [
        #     ["CrimeDateTime", "CrimeCode", "Description"]
        # ]

        print(df)


MDBPD0000().run()
