import pandas as pd
import requests
import sys

from io import StringIO

sys.path.append("../../utils")
from super import Scraper


class PAPPD0000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["PAPPD0000"]
        self.url = ""

    def scrape(self):
        pass


PAPPD0000().run()
