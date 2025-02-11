import glob
import os
import pandas as pd
import requests
import sys

from pathlib import Path
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep

sys.path.append("../../utils")
from selenium_configs import firefox_driver
from super import Scraper


class Tops(Scraper):
    def __init__(self):
        super().__init__()
        self.download_dir = f"{Path.cwd()}"
        self.driver = firefox_driver(self)
        self.wait = WebDriverWait(self.driver, 20)
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
        self.years = list(range(self.first.year, self.last.year + 1))
        self.config_clicks = {
            "[click] Measures": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[1]/div/div/div/table/tbody/tr[2]/td/div/div/ul/li[1]/div/a",
            "[xmark] All": '//*[@id="AllClearImage"]',
            "[checkbox] Number of Actual Offenses": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[3]/div/div/table[3]/tbody/tr[3]/td/div[2]/div[1]/div[2]/div/ul/li[3]/div/label/input",
            "[click] Jurisdiction by Type": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[1]/div/div/div/table/tbody/tr[2]/td/div/div/ul/li[4]/div/a",
            "[checkmark] Local Police Department": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[3]/div/div/table[3]/tbody/tr[3]/td/div[2]/div[1]/div[2]/div/ul/li/ul/li[3]/div/label/input[2]",
            "[click] Summary by Month": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[1]/div/div/div/table/tbody/tr[2]/td/div/div/ul/li[6]/div/a",
            "[checkmark] All Summary Months": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[3]/div/div/table[3]/tbody/tr[3]/td/div[2]/div[1]/div[2]/div/ul/li/div/label/input[2]",
            "[click] Summary Offense": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[1]/div/div/div/table/tbody/tr[2]/td/div/div/ul/li[7]/div/a",
            "[checkmark] All Summary Offenses": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[3]/div/div/table[3]/tbody/tr[3]/td/div[2]/div[1]/div[2]/div/ul/li/div/label/input[2]",
            "[uncheck] Criminal Homicide": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[3]/div/div/table[3]/tbody/tr[3]/td/div[2]/div[1]/div[2]/div/ul/li/ul/li[1]/div/label/input[1]",
            "[uncheck] Manslaughter by Negligence": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[3]/div/div/table[3]/tbody/tr[3]/td/div[2]/div[1]/div[2]/div/ul/li/ul/li[1]/ul/li[2]/div/label/input",
            "[uncheck] Assault Total": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[3]/div/div/table[3]/tbody/tr[3]/td/div[2]/div[1]/div[2]/div/ul/li/ul/li[4]/div/label/input[1]",
            "[uncheck] Other Assaults - Simple, Not Aggravated": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[3]/div/div/table[3]/tbody/tr[3]/td/div[2]/div[1]/div[2]/div/ul/li/ul/li[4]/ul/li[2]/div/label/input",
        }
        self.year_config_clicks = {
            "[click] Summary Date": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[1]/div/div/div/table/tbody/tr[2]/td/div/div/ul/li[5]/div/a",
            "[xmark] All": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[3]/div/div/table[3]/tbody/tr[3]/td/div[2]/div[1]/div[2]/div/ul/li/div/label/input[3]",
        }
        self.show_clicks = {
            "[click] Show report": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[3]/div/div/table[3]/tbody/tr[2]/td/table/tbody/tr/td[4]/input[1]",
        }
        self.download_clicks = {
            "[click] Download icon": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[3]/div/div/table[2]/tbody/tr[1]/td[1]/table/tbody/tr/td[1]/div/div/div/div/ul/li[8]/a/span/span/span/img",
            "[click] OK": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[3]/div/div/table[1]/tbody/tr/td/div/table/tbody/tr[9]/td/input[1]",
        }

        self.entry_clicks = [
            "SRS Crimes and Clearances by Offense Type",
            "Crime Overview Trend (Combined)",
            "Number of Crimes by Offense Type",
            "Crime Rates by Individual Jurisdictions",
        ]
        self.config_clicks = [
            ("span", "text", "Measures"),
            ("img", "id", "AllClearImage"),
        ]

    def scrape(self):
        self.driver.get(self.url)

        # quit driver in case of server errors
        if "Welcome" not in self.driver.page_source:
            self.driver.quit()
            r = requests.get(self.url)
            raise Exception(f"bad response ({r.status_code})")

        # expand all in case not automatic
        self.click_elements(("img", "title", "Expand all"))

        # get every scrape to the same report-building page
        report_title = None
        for text in self.entry_clicks:
            if text in self.driver.page_source:
                report_title = text
                break
        self.click_elements(("a", "text", report_title))
        sleep(1)

        # CT is a special case requiring an additional click
        if not self.driver.find_element(By.XPATH, "//td[text()='Report contents']"):
            self.click_elements(("span", "text", "Measures"))

        # run through report configuration clicks
        self.click_elements(self.config_clicks)

        #
        sleep(3)
        self.driver.quit()

        # self.click_elements(self.config_clicks)
        #
        # year_dfs = list()
        #
        # for year in self.years:
        #     self.click_elements(self.year_config_clicks)
        #     self.click_elements(
        #         elements={
        #             "[checkbox] {year}": f"//span[text()='{year}']//preceding-sibling::*"
        #         },
        #         year=year,
        #     )
        #     self.click_elements(self.show_clicks)
        #     self.click_elements(
        #         elements={
        #             "[dropdown] Summary Date": "/html/body/table/tbody/tr[3]/td[2]/form/div[3]/div/div/table/tbody/tr/td[3]/div/div/div[1]/div[1]/div/div/div/ul/li[5]/a/span/span/span/span[2]",
        #             "[click] {year}": f"//nobr[text()='{year}']",
        #         },
        #         year=year,
        #     )
        #
        #     # remove any existing csv in the cwd
        #     for fn in glob.glob(self.download_dir + "/" + "*.csv"):
        #         os.remove(fn)
        #
        #     self.click_elements(self.download_clicks)
        #
        #     # check for downloaded csv and load into df
        #     while len(glob.glob(self.download_dir + "/" + "*.csv")) == 0:
        #         sleep(1)
        #     sleep(3)
        #
        #     fns = glob.glob(self.download_dir + "/" + "*.csv")
        #     assert len(fns) == 1
        #     df = pd.read_csv(fns[0], index_col=0, skiprows=6)
        #
        #     # break out individual dfs per agency
        #     dfs = self.split_dataframe_into_batches(df)[1:-1]
        #
        #     # format each agency df
        #     formatted_dfs = list()
        #     for df in dfs:
        #         agency = list(df.columns)[0].replace(" Police Department", "")
        #         agency = agency.replace(" Metropolitan", "")
        #         df = df.rename(columns=df.iloc[0])
        #         df = df.iloc[3:-3, 1:].T
        #         df = (
        #             df.rename(columns=self.map)
        #             .reset_index()
        #             .rename(columns={"index": "month"})
        #             .rename_axis(None, axis=1)
        #         )
        #         df["month"] = pd.to_datetime(df["month"], format="%B").dt.month
        #         df["agency"] = agency
        #         formatted_dfs.append(df)
        #     df = pd.concat(formatted_dfs)
        #     df["year"] = year
        #     year_dfs.append(df)
        #
        # self.driver.quit()
        #
        # df = pd.concat(year_dfs)
        # df.to_csv("test_mo.csv", index=False)
        #
        # print(df.head())
        # print(df.tail())

    # def click_elements(self, elements, year=None):
    #     # run through dict of actions and their x paths
    #     for key, value in elements.items():
    #         if year:
    #             key = key.replace("{year}", str(year))
    #         self.logger.info(key)
    #         self.wait.until(
    #             ec.visibility_of_element_located(
    #                 (
    #                     By.XPATH,
    #                     value,
    #                 )
    #             )
    #         ).click()
    #         sleep(1)

    def click_elements(self, elements):
        if not isinstance(elements, list):
            elements = [elements]

        for element in elements:
            tag, feature, element = element
            xpath = f"//{tag}[@{feature}='{element}']"
            if feature == "text":
                xpath = f"//{tag}[{feature}()='{element}']"

            try:
                self.wait.until(
                    ec.visibility_of_element_located((By.XPATH, xpath))
                ).click()
                self.logger.info(f'[click] "{element}"')
                sleep(1)
                return
            except TimeoutException:
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    assert element
                    self.logger.error(
                        f'unresolved issue while retrieving element: "{element}"'
                    )
                except NoSuchElementException:
                    pass

    # def split_dataframe_into_batches(self, df):
    #     batches = list()
    #     num_columns = df.shape[1]
    #     for i in range(0, num_columns, self.batch_size):
    #         batch = df.iloc[:, i : i + self.batch_size]
    #         batches.append(batch)
    #     return batches
