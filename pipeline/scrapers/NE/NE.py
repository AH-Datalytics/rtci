import calendar
import glob
import os
import pandas as pd
import requests
import sys

from pathlib import Path
from time import sleep

sys.path.append("../../utils")
from airtable import get_records_from_sheet
from selenium_actions import (
    check_for_element,
    click_element,
    click_element_by_index,
    click_element_next,
    click_element_previous,
    drag_element,
    hide_element,
)
from selenium_configs import firefox_driver
from super import Scraper


from selenium.webdriver.support.ui import Select


class Colorado(Scraper):
    def __init__(self):
        super().__init__()
        self.url = "https://crimestats.ne.gov/public/View/RSReport.aspx?ReportId=1082"
        self.download_dir = f"{Path.cwd()}"
        self.driver = firefox_driver(self)
        self.years = list(range(self.first.year, self.last.year + 1))
        # self.batch_size = 13
        # self.records = list()
        # get list of agencies in state from airtable
        self.exclude_oris = []
        self.agencies = {
            d["agency_rtci"]: d["ori"]
            for d in get_records_from_sheet(
                self.logger,
                "Metadata",
                # formula=f"{{state}}='{self.state_full_name}'"
                # note: this includes agencies that are not included
                # in the existing RTCI sample (audited out for missing data, etc.);
                # to include only those matching the `final_sample.csv` file, use:
                #
                formula=f"AND({{state}}='{self.state_full_name}',NOT({{agency_rtci}}=''))",
            )
            if d["ori"] not in self.exclude_oris
        }
        # specify self.oris for super class
        self.oris = list(self.agencies.values())
        self.map = {
            "Murder and Nonnegligent Manslaughter": "murder",
            "Forcible Rape Total": "rape",
            "Robbery Total": "robbery",
            "Aggravated Assault Total": "aggravated_assault",
            "Burglary Total": "burglary",
            "Larceny - Theft Total": "theft",
            "Motor Vehicle Theft Total": "motor_vehicle_theft",
        }

    def scrape(self):
        self.driver.get(self.url)

        # quit driver in case of server errors
        if "Welcome" not in self.driver.page_source:
            self.driver.quit()
            r = requests.get(self.url)
            raise Exception(f"bad response ({r.status_code})")

        for year in self.years:
            for month in list(calendar.month_abbr)[1:]:
                s = f"{month}&nbsp;{year}"
                ss = f"{month} {year}"

                from selenium import webdriver
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC

                wait = WebDriverWait(self.driver, 20)
                select_id = "ctl00_MainContent_RptViewer_ctl08_ctl05_ddValue"

                break
            break

        # # get to report config page
        # click_element(self, "img", "title", "Expand all")
        # click_element(self, "a", "text", "Crime Rates by Individual Jurisdictions")
        #
        # # config measures
        # click_element(self, "a", "text", "Measures")
        # click_element(self, "img", "title", "Clear all members")
        # hide_element(self, "//div[@id='HighLightDiv']")
        # click_element_previous(self, "span", "text", "Number of Crimes", "input", 1)
        # click_element(self, "span", "id", "H_9_ClearSelection")
        #
        # # config jurisdictions
        # click_element(self, "a", "text", "Jurisdiction by Type")
        # click_element_next(self, "span", "text", "Local Police Department", "input", 1)
        #
        # # config months
        # click_element(self, "a", "text", "Incident Month")
        # click_element_next(self, "span", "text", "All Incident Months", "input", 1)
        #
        # # config offenses
        # click_element(self, "a", "text", "Offense Type")
        # click_element_next(self, "span", "text", "All Offense Types", "input", 1)
        # click_element_next(self, "span", "text", "All Offense Types", "input", 2)
        # click_element_previous(
        #     self, "span", "text", "Murder and Nonnegligent Manslaughter", "input", 1
        # )
        # click_element_previous(self, "span", "text", "All Rape", "input", 1)
        # click_element_previous(self, "span", "text", "Aggravated Assault", "input", 1)
        # click_element_previous(
        #     self, "span", "text", "Burglary/Breaking & Entering", "input", 1
        # )
        # click_element_previous(self, "span", "text", "Robbery", "input", 1)
        # click_element_previous(self, "span", "text", "Pocket-picking", "input", 1)
        # click_element_previous(self, "span", "text", "Purse-snatching", "input", 1)
        # click_element_previous(self, "span", "text", "Shoplifting", "input", 1)
        # click_element_previous(self, "span", "text", "Theft From Building", "input", 1)
        # click_element_previous(
        #     self,
        #     "span",
        #     "text",
        #     "Theft From Coin Operated Machine or Device",
        #     "input",
        #     1,
        # )
        # click_element_previous(
        #     self, "span", "text", "Theft From Motor Vehicle", "input", 1
        # )
        # click_element_previous(
        #     self, "span", "text", "Theft of Motor Vehicle Parts/Accessories", "input", 1
        # )
        # click_element_previous(self, "span", "text", "All Other Larceny", "input", 1)
        # click_element_previous(self, "span", "text", "Motor Vehicle Theft", "input", 1)
        #
        # # config years
        # for year in self.years:
        #     click_element(self, "a", "text", "Incident Date")
        #     click_element(
        #         self,
        #         "input",
        #         "title",
        #         "Clear group and all members below it in hierarchy",
        #     )
        #     if check_for_element(self, "span", "text", str(year)):
        #         click_element_previous(self, "span", "text", year, "input", 1)
        #
        #     # gen report
        #     click_element(self, "input", "name", "ShowUpdatedReportButton")
        #
        #     # remove any existing csvs in local dir
        #     for fn in glob.glob(self.download_dir + "/" + "*.csv"):
        #         os.remove(fn)
        #
        #     # download report
        #     click_element(self, "img", "title", "Download report data")
        #     click_element(self, "input", "name", "DownloadReportGo")
        #
        #     # check for downloaded csv and load into df
        #     while len(glob.glob(self.download_dir + "/" + "*.csv")) == 0:
        #         sleep(1)
        #     sleep(3)
        #
        #     fns = glob.glob(self.download_dir + "/" + "*.csv")
        #     assert len(fns) == 1
        #     df = pd.read_csv(fns[0], index_col=0, skiprows=4, thousands=",")
        #     idx = df.columns.get_loc("January")
        #     dfs = self.split_dataframe_into_batches(df, batch_size=idx)[1:]
        #
        #     for df in dfs:
        #         self.records.extend(self.format_one_month(df, year))
        #
        #     # remove any existing csvs in local dir
        #     for fn in glob.glob(self.download_dir + "/" + "*.csv"):
        #         os.remove(fn)
        #
        # self.records = pd.DataFrame(self.records)
        # self.records = self.records[self.records["ori"].isin(self.agencies)]
        # self.records["ori"] = self.records["ori"].map(self.agencies)
        #
        # # wait, quit driver and return
        # sleep(5)
        # self.driver.quit()
        # return self.records.to_dict("records")

    @staticmethod
    def split_dataframe_into_batches(df, batch_size):
        batches = list()
        num_columns = df.shape[1]
        for i in range(0, num_columns, batch_size):
            batch = df.iloc[:, i : i + batch_size]
            batches.append(batch)
        return batches

    def format_one_month(self, df, year):
        month = list(df.columns)[0]
        df = df.rename(columns=df.iloc[0])

        out = list()
        dfs = self.split_dataframe_into_batches(df, batch_size=14)[1:]
        for df in dfs:
            agency = list(df.columns)[0].replace(" Police Department", "")
            agency = agency.replace(" Department of Public Safety", "")
            df.columns = df.iloc[1]
            df = df.rename_axis(None, axis=1).T
            df = df.reset_index()[["Offense Type", str(year)]].rename_axis(None, axis=1)
            df = df.rename(columns={str(year): "count", "Offense Type": "crime"})
            df["crime"] = df["crime"].map(self.map)
            df["count"] = df["count"].apply(lambda s: self.check_for_comma(s))
            df = df.groupby("crime")["count"].sum().reset_index()
            df["year"] = year
            df["month"] = month
            df["month"] = pd.to_datetime(df["month"], format="%B").dt.month
            df["ori"] = agency
            out.extend(
                df.pivot(
                    index=["year", "month", "ori"],
                    columns="crime",
                    values="count",
                )
                .reset_index()
                .rename_axis(None, axis=1)
                .to_dict("records")
            )

        return out


Colorado().run()
