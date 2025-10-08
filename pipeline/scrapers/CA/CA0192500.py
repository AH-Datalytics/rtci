import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS
from datetime import datetime as dt
from datetime import timedelta as td

sys.path.append("../../utils")
from pdfs import parse_pdf
from super import Scraper


class CA0192500(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["CA0192500"]
        self.url = "https://www.glendaleca.gov/government/departments/police-department/community-outreach-resources-and-engagement-c-o-r-e/crime-prevention-programs-resources/crime-statistics-booking-logs"
        self.mapping = {
            "HOMICIDE": "murder",
            "RAPE": "rape",
            "ROBBERY": "robbery",
            "AGGRAVATED ASSAULT": "aggravated_assault",
            "BURGLARY": "burglary",
            "LARCENY / THEFT": "theft",
            "GRAND THEFT AUTO": "motor_vehicle_theft",
        }
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        }
        # self.headers = {
        #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        # }

    @staticmethod
    def get_proxies(use_isp=False):
        """
        your ip must be authorized to use the proxy.
        go here to set it up: https://proxymesh.com/account/edit_ips/
        use like this: requests.get(url, proxies=self.get_proxies())
        """
        import random

        proxies = [
            "http://45.32.231.36:31280",
            "http://207.148.86.251:31280",
            "http://45.32.86.6:31280",
            "http://45.32.231.36:31280",
            "http://66.23.205.218:31280",
            "http://216.173.113.135:31280",
            "http://191.96.166.60:31280",
            "http://23.108.55.79:31280",
            "http://64.20.49.25:31280",
            "http://154.127.54.142:31280",
        ]

        if use_isp:
            return {
                "http": "http://154.127.54.142:31280",
                "https": "http://154.127.54.142:31280",
            }

        return {"http": random.choice(proxies), "https": random.choice(proxies)}

    def scrape(self):
        r = requests.get(
            self.url,
            headers=self.headers,
            allow_redirects=True,
            # verify=False,
            proxies=self.get_proxies(),
        )
        soup = bS(r.text, "lxml")
        print(soup)
        url = soup.find("a", string=re.compile(r"NIBRS Crime Data"))
        print(url)


CA0192500().run()
