import calendar
import pandas as pd
import requests
import sys

from bs4 import BeautifulSoup as bS
from datetime import datetime as dt
from pathlib import Path
from selenium.common.exceptions import TimeoutException
from time import sleep

sys.path.append("../../utils")
from selenium_actions import (
    check_for_element,
    click_element,
    click_element_by_index,
    click_element_next,
    click_element_previous,
    click_select_element_value,
    drag_element,
    hide_element,
    wait_for_element,
)
from selenium_configs import chrome_driver
from super import Scraper


class Nebraska(Scraper):
    def __init__(self):
        super().__init__()
        self.url = "https://crimestats.ne.gov/public/View/RSReport.aspx?ReportId=1082"
        self.download_dir = f"{Path.cwd()}"
        self.driver = chrome_driver(self)
        self.years = list(range(self.first.year, self.last.year + 1))
        self.map = {}
        self.records = list()
        self.exclude_oris = ["NB0280200"]
        self.agencies = self.get_agencies(self.exclude_oris)
        self.oris = list(self.agencies.values())
        self.map = {
            "a. Murder and Nonnegligent Homicide": "murder",
            "2. Forcible Rape Total": "rape",
            "3. Robbery Total": "robbery",
            "Aggravated Assault Total": "aggravated_assault",
            "5. Burglary Total": "burglary",
            "6. Larceny - Theft Total": "theft",
            "7. Motor Vehicle Theft Total": "motor_vehicle_theft",
        }

    def scrape(self):
        self.driver.get(self.url)

        # quit driver in case of server errors
        if "Welcome" not in self.driver.page_source:
            self.driver.quit()
            r = requests.get(self.url)
            raise Exception(f"bad response ({r.status_code})")
        sleep(3)

        # get list of year, month and agency values from site
        soup = bS(self.driver.page_source, "lxml")
        months = [
            s.text
            for s in soup.find(
                "select", {"name": "ctl00$MainContent$RptViewer$ctl08$ctl05$ddValue"}
            ).find_all("option")
            if len(s.text) == 8
            and self.first
            <= dt.strptime(s.text.strip().replace("\xa0", " "), "%b %Y")
            <= self.last
        ]
        agencies = [
            s.text
            for s in soup.find(
                "select", {"name": "ctl00$MainContent$RptViewer$ctl08$ctl03$ddValue"}
            ).find_all("option")
            if s.text.strip().replace("\xa0", " ").rsplit(" - ", 1)[-1] in self.oris
        ]

        # run through agencies and year-months to generate reports and parse them
        for agency in agencies:
            self.select_agency(agency)
            for month in months:
                self.select_month(agency, month)
                self.click_report(agency, month)
                soup = bS(self.driver.page_source, "lxml")
                self.process_soup(soup, agency, month)
                sleep(1)

        # process and return records
        return self.process_records()

    def select_agency(self, agency):
        self.logger.info(f"attempting {agency}...")
        sleep(3)
        try:
            click_select_element_value(
                self,
                "select",
                "id",
                "ctl00_MainContent_RptViewer_ctl08_ctl03_ddValue",
                agency,
            )
        except (NotImplementedError, TimeoutException):
            self.logger.warning("retrying...")
            self.driver.quit()
            sleep(5)
            self.driver = chrome_driver(self)
            self.driver.get(self.url)
            click_select_element_value(
                self,
                "select",
                "id",
                "ctl00_MainContent_RptViewer_ctl08_ctl03_ddValue",
                agency,
            )

    def select_month(self, agency, month):
        self.logger.info(f"attempting {month}...")
        sleep(3)
        try:
            click_select_element_value(
                self,
                "select",
                "id",
                "ctl00_MainContent_RptViewer_ctl08_ctl05_ddValue",
                month,
            )
        except (NotImplementedError, TimeoutException):
            self.logger.warning("retrying...")
            self.driver.quit()
            sleep(5)
            self.driver = chrome_driver(self)
            self.driver.get(self.url)
            self.select_agency(agency)
            click_select_element_value(
                self,
                "select",
                "id",
                "ctl00_MainContent_RptViewer_ctl08_ctl05_ddValue",
                month,
            )

    def click_report(self, agency, month):
        sleep(3)
        try:
            click_element(
                self,
                "input",
                "id",
                "ctl00_MainContent_RptViewer_ctl08_ctl00",
            )
            wait_for_element(
                self,
                "div",
                "id",
                "VisibleReportContentctl00_MainContent_RptViewer_ctl13",
                30,
            )
            wait_for_element(self, "div", "text", "Grand Total", 30)
        except TimeoutException:
            self.logger.warning("retrying...")
            self.driver.quit()
            sleep(15)
            self.driver = chrome_driver(self)
            self.driver.get(self.url)
            self.select_agency(agency)
            self.select_month(agency, month)
            sleep(3)
            click_element(
                self,
                "input",
                "id",
                "ctl00_MainContent_RptViewer_ctl08_ctl00",
            )
            wait_for_element(
                self,
                "div",
                "id",
                "VisibleReportContentctl00_MainContent_RptViewer_ctl13",
                30,
            )
            wait_for_element(self, "div", "text", "Grand Total", 30)

    def process_soup(self, soup, agency, month):
        month, year = month.split("\xa0")
        for field in self.map:
            tds = soup.find_all("td", string=field)
            assert len(tds) == 1
            td = tds[0]
            reported = td.find_next_sibling("td").text.strip()
            if reported == "":
                reported = 0
            else:
                reported = int(reported)
            cleared = (
                td.find_next_sibling("td")
                .find_next_sibling("td")
                .find_next_sibling("td")
                .find_next_sibling("td")
                .text.strip()
            )
            if cleared == "":
                cleared = 0
            else:
                cleared = int(cleared)
            datum = {
                "field": field,
                "reported": reported,
                "cleared": cleared,
            }
            tmp = {"ori": agency, "year": int(year), "month": dt.strptime(month, "%b")}
            tmp.update(datum)
            tmp["ori"] = tmp["ori"].replace("\xa0", " ").rsplit(" - ", 1)[-1]
            self.records.append(tmp)

    def process_records(self):
        # relabel field names and sum components
        self.records = pd.DataFrame(self.records)
        self.records["field"] = self.records["field"].map(self.map)
        self.records = (
            self.records.groupby(["ori", "year", "month", "field"]).sum().reset_index()
        )

        # handle crime counts vs. clearances
        records = self.records.pivot(
            index=["ori", "year", "month"],
            columns="field",
            values="reported",
        ).reset_index()

        clearances = (
            self.records.pivot(
                index=["ori", "year", "month"],
                columns="field",
                values="cleared",
            )
            .reset_index()
            .add_suffix("_cleared")
            .rename(
                columns={
                    "ori_cleared": "ori",
                    "year_cleared": "year",
                    "month_cleared": "month",
                }
            )
        )
        self.records = pd.merge(
            records,
            clearances,
            on=["ori", "year", "month"],
        )

        # reformat month
        self.records["month"] = pd.to_datetime(
            self.records["month"], format="%b"
        ).dt.month

        # return results
        self.driver.quit()
        return self.records.to_dict("records")


Nebraska().run()
