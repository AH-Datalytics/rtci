import glob
import os
import pandas as pd
import requests
import sys

from functools import reduce
from pathlib import Path
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


class Connecticut(Scraper):
    def __init__(self):
        super().__init__()
        self.url = "https://ct.beyond2020.com/ct_public/Dim/dimension.aspx"
        self.download_dir = f"{Path.cwd()}"
        self.driver = chrome_driver(self)
        self.years = list(range(self.first.year, self.last.year + 1))
        self.batch_size = 13
        self.records = list()
        self.exclude_oris = []
        self.agencies = self.get_agencies(self.exclude_oris)
        self.oris = list(self.agencies.values())
        self.map = {
            "Murder and Nonnegligent Homicide": "murder",
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

        # get to report config page
        click_element(self, "img", "title", "Expand all")
        click_element(
            self, "a", "text", "SRS Index Offense Count by Town with Year Slicer"
        )

        # config measures
        click_element(self, "span", "text", "Measures")
        click_element(self, "img", "title", "Clear all members")
        hide_element(self, "//div[@id='HighLightDiv']")
        click_element_previous(
            self, "span", "text", "Number of Actual Offenses", "input", 1
        )
        click_element_previous(
            self, "span", "text", "Total Offenses Cleared", "input", 1
        )
        click_element(self, "span", "id", "H_5_ClearSelection")

        # config jurisdictions
        click_element(self, "a", "text", "Jurisdiction by Type")
        click_element_next(self, "span", "text", "Local Police Department", "input", 1)

        # config months
        click_element(self, "a", "text", "Summary Month")
        click_element_next(self, "span", "text", "All Summary Months", "input", 1)

        # config offenses
        click_element(self, "a", "text", "Summary Offense")
        click_element_next(self, "span", "text", "All Summary Offenses", "input", 1)
        click_element_next(self, "span", "text", "All Summary Offenses", "input", 2)
        click_element_previous(
            self, "span", "text", "Murder and Nonnegligent Homicide", "input", 1
        )
        click_element_previous(self, "span", "text", "Forcible Rape Total", "input", 1)
        click_element_previous(self, "span", "text", "Robbery Total", "input", 1)
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

        # config years
        click_element(self, "a", "text", "Summary Date")
        click_element(
            self, "input", "title", "Clear group and all members below it in hierarchy"
        )

        for year in self.years:
            if check_for_element(self, "span", "text", str(year)):
                click_element_previous(self, "span", "text", year, "input", 1)

                # for CT only, scroll the report button into view
                button = self.driver.find_element(
                    By.XPATH, "//input[@name='ShowUpdatedReportButton']"
                )
                self.driver.execute_script("arguments[0].scrollIntoView();", button)

                # gen report
                click_element(self, "input", "name", "ShowUpdatedReportButton")

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
                df = pd.read_csv(fns[0], index_col=0, skiprows=4, thousands=",")
                idx = df.columns.get_loc("Human Trafficking Offenses")
                df = df.iloc[:, :idx]
                idx = df.columns.get_loc("Forcible Rape Total")
                dfs = self.split_dataframe_into_batches(df, batch_size=idx)

                year_dfs = list()
                for df in dfs:
                    year_dfs.append(self.format_one_crime(df, year))

                year_df = reduce(
                    lambda left, right: pd.merge(
                        left, right, on=["ori", "year", "month"], how="left"
                    ),
                    year_dfs,
                )

                self.records.extend(year_df.to_dict("records"))

                # remove any existing csvs in local dir
                for fn in glob.glob(self.download_dir + "/" + "*.csv"):
                    os.remove(fn)

                # click back to update year
                click_element(self, "span", "text", "Summary Date")
                click_element(
                    self,
                    "input",
                    "title",
                    "Clear group and all members below it in hierarchy",
                )

        self.records = pd.DataFrame(self.records)
        self.records = self.records[self.records["ori"].isin(self.agencies)]
        self.records["ori"] = self.records["ori"].map(self.agencies)

        # wait, quit driver and return
        sleep(5)
        self.driver.quit()
        return self.records.to_dict("records")

    @staticmethod
    def split_dataframe_into_batches(df, batch_size):
        batches = list()
        num_columns = df.shape[1]
        for i in range(0, num_columns, batch_size):
            batch = df.iloc[:, i : i + batch_size]
            batches.append(batch)
        return batches

    def format_one_crime(self, df, year):
        crime = self.map[list(df.columns)[0]]
        df = df.rename(columns=df.iloc[0])
        df = df.iloc[1:]
        dfs = self.split_dataframe_into_batches(df, batch_size=self.batch_size)[1:]

        out = list()
        for df in dfs:
            agency = list(df.columns)[0]
            df.columns = df.iloc[0]
            df = (
                df.iloc[2:-1, 1:]
                .rename_axis(None, axis=1)
                .T.reset_index()
                .rename(
                    columns={
                        "Number of Actual Offenses": crime,
                        "Total Offenses Cleared": f"{crime}_cleared",
                        "index": "month",
                    }
                )
                .rename_axis(None, axis=1)
            )
            df["month"] = pd.to_datetime(df["month"], format="%B").dt.month
            df["year"] = year
            df["ori"] = agency

            out.extend(df.to_dict("records"))

        return pd.DataFrame(out)


Connecticut().run()
