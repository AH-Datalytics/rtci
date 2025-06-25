import pandas as pd
import re
import requests
import sys

from itertools import groupby
from math import prod
from operator import itemgetter
from tableauscraper import TableauScraper as tS
from time import sleep

sys.path.append("../../utils")
from airtable import get_records_from_sheet
from super import Scraper


requests.packages.urllib3.disable_warnings()


class WA0270300(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["WA0270300"]
        self.url = (
            "https://public.tableau.com/views/TacomaPoliceCrimeDashboard/CrimeDashboard-IntroPage"
            "?%3Adisplay_static_image=y&%3AbootstrapWhenNotified=true&%3Aembed=true&%3Alanguage=en-US&:embed"
            "=y&:showVizHome=n&:apiID=host0#navType=0&navSrc=Parse"
        )

    def scrape(self):
        # get list of filters to narrow down
        ts = tS(verify=False)
        ts.loads(self.url)

        # wb = ts.getWorkbook()
        #
        # for ws in wb.worksheets():
        #     print(ws)


WA0270300().run()
