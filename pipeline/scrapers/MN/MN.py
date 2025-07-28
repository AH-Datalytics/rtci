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
from super import Scraper


requests.packages.urllib3.disable_warnings()


class Minnesota(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = None
        self.exclude_oris = list()
        self.exclude_oris = []
        self.agencies = self.get_agencies(self.exclude_oris)
        self.oris = list(self.agencies.values())
        self.person_url = (
            "https://cde.state.mn.us/views/MNCDE-CrimesAgainstPerson/CrimesAgainstPerson?:embed=y&:showVizHome"
            "=no&:host_url=https://cde.state.mn.us/&:embed_code_version=3&:tabs=false&:toolbar=yes"
            "&:showAppBanner=false&:alerts=no&:customViews=no&:showShareOptions=false&:subscriptions=no"
            "&:display_spinner=no&:loadOrderID=0"
        )
        self.property_url = (
            "https://cde.state.mn.us/views/MNCDE-CrimesAgainstProperty/CrimesAgainstProperty?:embed=y"
            "&:showVizHome=no&:host_url=https://cde.state.mn.us/&:embed_code_version=3&:tabs=false"
            "&:toolbar=yes&:showAppBanner=false&:alerts=no&:customViews=no&:showShareOptions=false"
            "&:subscriptions=no&:display_spinner=no&:loadOrderID=0"
        )
        self.person_mapping = {
            "Aggravated Assault": "aggravated_assault",
            "Murder & Non-negligent Manslaughter": "murder",
            "Rape": "rape",
            "Sodomy": "rape",
            "Sexual Assault With An Object": "rape",
        }
        self.property_mapping = {
            "All Other Larceny": "theft",
            "Burglary/Breaking & Entering": "burglary",
            "Motor Vehicle Theft": "motor_vehicle_theft",
            "Pocket-picking": "theft",
            "Purse-snatching": "theft",
            "Shoplifting": "theft",
            "Theft From Building": "theft",
            "Theft From Coin-Operated Machine or Device": "theft",
            "Theft From Motor Vehicle": "theft",
            "Theft of Motor Vehicle Parts or Accessories": "theft",
            "Robbery": "robbery",
        }
        self.data = list()
        self.failures = list()

    def scrape(self):
        self.collect(self.person_url, self.person_mapping)
        self.collect(self.property_url, self.property_mapping)

        grouped = list()
        self.data.sort(key=itemgetter("ori", "year", "month"))
        for key, group in groupby(self.data, key=itemgetter("ori", "year", "month")):
            tmp = dict()
            for d in group:
                tmp.update(d)
            grouped.append(tmp)

        # combine crimes of same type from mapping
        df = pd.DataFrame(grouped)
        for mapping in [self.person_mapping, self.property_mapping]:
            for v in set(mapping.values()):
                cols = [k for k in mapping if mapping[k] == v]
                cols = [col for col in cols if col in df.columns]
                if cols:
                    df[v] = df[cols].sum(axis=1)
                    df = df.drop(columns=cols)

        return df.to_dict("records")

    def collect(self, url, mapping):
        # get list of filters to narrow down
        ts = tS(verify=False)
        ts.loads(url)
        o = ts.getWorksheet("Offenses")
        filters = {
            d["column"]: d["values"]
            for d in o.getFilters()
            if d["column"] in ["Agency (ORI)", "Offense", "Year"]
        }
        filters["Year"] = [v for v in filters["Year"] if int(v) >= self.first.year]
        filters["Agency (ORI)"] = [
            v
            for v in filters["Agency (ORI)"]
            if re.match(r"^.+\s\((.+)\)$", v).group(1) in self.oris
        ]
        assert len(filters["Agency (ORI)"]) == len(self.oris)
        filters["Offense"] = [v for v in filters["Offense"] if v in mapping]

        # find all filter combos with data (filtering options)
        combos = list()
        for year in filters["Year"]:
            wb = o.setFilter("Year", year, dashboardFilter=True)
            ws = wb.getWorksheet("Offenses")
            for offense in filters["Offense"]:
                wb = ws.setFilter("Offense", offense, dashboardFilter=True)
                ws = wb.getWorksheet("Offenses")
                agencies = [
                    [
                        v
                        for v in a["values"]
                        if re.match(r"^.+\s\((.+)\)$", v).group(1) in self.oris
                    ]
                    for a in ws.getFilters()
                    if a["column"] == "Agency (ORI)"
                ][0]
                combos.extend(
                    [
                        {"Year": year, "Offense": offense, "Agency (ORI)": agency}
                        for agency in agencies
                    ]
                )

        self.logger.info(
            f"{len(combos)} of {prod([len(arr) for arr in list(filters.values())])} filters have data"
        )

        for idx, combo in enumerate(combos):
            self.logger.info(f"{idx + 1}/{len(combos)}: {combo}")
            try:
                self.data.extend(self.get_combo(combo, o))
            except KeyError:
                self.logger.warning(f"retrying: {combo}")
                sleep(5)
                try:
                    self.data.extend(self.get_combo(combo, o))
                except KeyError:
                    self.logger.warning(f"failed on: {combo}")
                    self.failures.append(combo)
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"connection error; retrying: {combo}")
                sleep(5)
                ts = tS(verify=False)
                ts.loads(url)
                o = ts.getWorksheet("Offenses")
                self.data.extend(self.get_combo(combo, o))

    @staticmethod
    def get_combo(combo, ws):
        wb = None
        for k, v in combo.items():
            wb = ws.setFilter(k, v, dashboardFilter=True)
            ws = wb.getWorksheet("Offenses")
        obm = wb.getWorksheet("Offenses by Month")
        df = obm.data[["Month Name Short-value", "AGG(Offenses Decimal)-value"]].rename(
            columns={
                "Month Name Short-value": "month",
                "AGG(Offenses Decimal)-value": combo["Offense"],
            }
        )
        df["year"] = int(combo["Year"])
        df["month"] = pd.to_datetime(df["month"], format="%b").dt.month
        df["ori"] = re.match(r"^.+\s\((.+)\)$", combo["Agency (ORI)"]).group(1)
        return df.to_dict("records")


Minnesota().run()
