import glob
import os
import pandas as pd
import requests
import sys

from functools import reduce
from pathlib import Path
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
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


class UT0180300(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["UT0180300"]
        self.url = (
            "https://app.powerbigov.us/view?r=eyJrIjoiOGZiMGYzMWUtMDkxZC00Njg2LTlhYWItNjQ2ZGI2ZjZiNmEzIiwidCI6I"
            "jlmYTJjOTUyLWRkNTAtNGIwNi1iYTZhLTRiOWJkN2FkZGEwMyJ9"
        )
        self.download_dir = f"{Path.cwd()}"
        self.driver = chrome_driver(self)
        self.years = list(range(self.first.year, self.last.year + 1))
        self.map = {
            "Criminal Homicide": "murder",
            "Rape": "rape",
            "Motor Vehicle Theft": "motor_vehicle_theft",
        }

    def scrape(self):
        self.driver.get(self.url)

        # for year in self.years:
        for year in [2021]:
            print(year)

            try:
                click_element(self, "div", "title", year)
                element = self.driver.find_element(By.XPATH, f"//div[@title='{year}']")
                self.driver.execute_script("arguments[0].click();", element)
            except TimeoutException:
                self.logger.warning(f"no button for {year}")

            sleep(10)


UT0180300().run()
