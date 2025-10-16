import pandas as pd
import requests
import sys

from io import StringIO

sys.path.append("../../utils")
from super import Scraper


class MI4143600(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["MI4143600"]
        self.url = ""

    def scrape(self):
        pass


MI4143600().run()
