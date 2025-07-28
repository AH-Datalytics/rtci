import glob
import os
import pandas as pd
import requests
import sys

from functools import reduce
from pathlib import Path
from time import sleep

sys.path.append("../../utils")
from selenium_actions import (
    check_for_element,
    click_element,
    click_element_by_index,
    click_element_next,
    click_element_previous,
    drag_element,
    hide_element,
)
from selenium_configs import chrome_driver
from super import Scraper


class NorthDakota(Scraper):
    def __init__(self):
        super().__init__()
        self.url = ""

    def scrape(self):
        pass


NorthDakota().run()
