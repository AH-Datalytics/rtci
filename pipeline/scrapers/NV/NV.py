import glob
import os
import pandas as pd
import requests
import sys

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


class Nevada(Scraper):
    def __init__(self):
        super().__init__()
        self.url = "https://nevadacrimestats.nv.gov/public/View/dispview.aspx"
        self.download_dir = f"{Path.cwd()}"
        self.driver = chrome_driver(self)
        self.years = list(range(self.first.year, self.last.year + 1))
        self.map = {
            "Murder and Nonnegligent Homicide": "murder",
            "Forcible Rape Total": "rape",
            "Robbery Total": "robbery",
            "Aggravated Assault Total": "aggravated_assault",
            "Burglary Total": "burglary",
            "Larceny - Theft Total": "theft",
            "Motor Vehicle Theft Total": "motor_vehicle_theft",
        }
        self.batch_size = 13
        self.records = list()
        self.exclude_oris = ["NV0020100"]
        self.agencies = self.get_agencies(self.exclude_oris)
        self.oris = list(self.agencies.values())

    def scrape(self):
        self.driver.get(self.url)

        # quit driver in case of server errors
        if "Welcome" not in self.driver.page_source:
            self.driver.quit()
            r = requests.get(self.url)
            raise Exception(f"bad response ({r.status_code})")

        # get to report config page
        click_element(self, "img", "title", "Expand all")
        click_element(self, "a", "text", "SRS Crimes and Clearances by Offense Type")

        # config measures
        click_element(self, "a", "text", "Measures")
        click_element(self, "img", "title", "Clear all members")
        hide_element(self, "//div[@id='HighLightDiv']")
        click_element_previous(
            self, "span", "text", "Number of Actual Offenses", "input", 1
        )
        click_element(self, "span", "id", "H_5_ClearSelection")

        # config jurisdictions
        click_element(self, "a", "text", "Jurisdiction by Type")
        click_element_next(self, "span", "text", "Sheriff's Office", "input", 1)
        click_element_next(self, "span", "text", "Local Police Department", "input", 1)

        # config years
        click_element(self, "a", "text", "Summary Date")
        click_element(
            self, "input", "title", "Clear group and all members below it in hierarchy"
        )

        for year in self.years:
            if check_for_element(self, "span", "text", str(year)):
                click_element_previous(self, "span", "text", year, "input", 1)

        # config months
        click_element(self, "a", "text", "Summary Month")
        click_element_next(self, "span", "text", "All Summary Months", "input", 1)

        # config offenses
        click_element(self, "a", "text", "Summary Offense")
        click_element_next(self, "span", "text", "All Summary Offenses", "input", 2)
        click_element_next(self, "span", "text", "Criminal Homicide", "input", 1)
        click_element_next(self, "span", "text", "Criminal Homicide", "input", 2)
        click_element_previous(
            self, "span", "text", "Murder and Nonnegligent Homicide", "input", 1
        )
        click_element_previous(self, "span", "text", "Forcible Rape Total", "input", 1)
        click_element_previous(self, "span", "text", "Robbery Total", "input", 1)
        click_element_next(self, "span", "text", "Assault Total", "input", 1)
        click_element_next(self, "span", "text", "Assault Total", "input", 2)
        click_element_previous(
            self, "span", "text", "Aggravated Assault Total", "input", 1
        )
        click_element_previous(self, "span", "text", "Burglary Total", "input", 1)
        click_element_previous(
            self, "span", "text", "Larceny - Theft Total", "input", 1
        )
        click_element_previous(
            self, "span", "text", "Motor Vehicle Theft Total", "input", 1
        )

        # gen report
        click_element(self, "input", "name", "ShowUpdatedReportButton")

        # click dropdown and select each year one by one
        for year in self.years:
            click_element_by_index(self, "span", "class", "rtbChoiceArrow", -1)
            click_element(self, "nobr", "text", str(year))

            # remove any existing csvs in local dir
            for fn in glob.glob(self.download_dir + "/" + "*.csv"):
                os.remove(fn)

            # download report
            click_element(self, "img", "title", "Download report data")
            click_element(self, "input", "name", "DownloadReportGo")

            # check for downloaded csv and load into df
            while len(glob.glob(self.download_dir + "/" + "*.csv")) == 0:
                sleep(1)
            sleep(3)
            fns = glob.glob(self.download_dir + "/" + "*.csv")
            assert len(fns) == 1
            df = pd.read_csv(fns[0], index_col=0, skiprows=5, thousands=",")

            # break out individual dfs per year-agency and format
            dfs = self.split_dataframe_into_batches(df)[1:]
            for df in dfs:
                self.records.extend(self.format_one_year_agency(year, df))

            # remove any existing csvs in local dir
            for fn in glob.glob(self.download_dir + "/" + "*.csv"):
                os.remove(fn)

        self.records = pd.DataFrame(self.records)
        self.records = self.records[self.records["ori"].isin(self.agencies)]
        self.records["ori"] = self.records["ori"].map(self.agencies)

        # wait, quit driver and return
        sleep(5)
        self.driver.quit()
        return self.records.to_dict("records")

    def split_dataframe_into_batches(self, df):
        batches = list()
        num_columns = df.shape[1]
        for i in range(0, num_columns, self.batch_size):
            batch = df.iloc[:, i : i + self.batch_size]
            batches.append(batch)
        return batches

    def format_one_year_agency(self, year, df):
        agency = list(df.columns)[0]
        agency = agency.replace(
            " Metro Police Department",
            " Metropolitan Police Department Police Department",
        )
        df = df.rename(columns=df.iloc[0])
        df = df.iloc[2:].reset_index()
        df = df.rename(columns=self.map)
        df["crime"] = df["Jurisdiction by Type"].map(self.map)
        df = df.drop(columns=["Jurisdiction by Type"])
        df = (
            df[list(df.columns.difference({"All Summary Months"}))]
            .set_index("crime")
            .T.reset_index()
            .rename(columns={"index": "month"})
            .rename_axis(None, axis=1)
        )
        df["month"] = pd.to_datetime(df["month"], format="%B").dt.month
        df["year"] = year
        df["ori"] = agency
        return df.to_dict("records")


Nevada().run()
