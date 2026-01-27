import pandas as pd
import re
import requests
import sys

from bs4 import BeautifulSoup as bS
from datetime import datetime as dt

sys.path.append("../../utils")
from super import Scraper


class CA0070400(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["CA0070400"]
        self.stem = "https://cityofconcord.org"
        self.url = self.stem + "/1281/2025-Crime-Statistics"
        self.mapping = {
            "Aggravated Assault": "aggravated_assault",
            "Burglary/Breaking & Entering": "burglary",
            "BURGLARY": "burglary",
            "Motor Vehicle Theft": "motor_vehicle_theft",
            "Murder & Nonnegligent Manslaughter": "murder",
            "Rape": "rape",
            "Sexual Assault With An Object": "rape",
            "Sodomy": "rape",
            "Robbery": "robbery",
            "Pocket-Picking": "theft",
            "Purse-Snatching": "theft",
            "Shoplifting": "theft",
            "Theft From Building": "theft",
            "Theft From Motor Vehicle": "theft",
            "Theft Of Motor Vehicle Parts": "theft",
            "THEFT OF MOTOR VEHICLE PARTS OR ACCESSORIES": "theft",
            "All Other Larceny": "theft",
        }  # 2022 has some different row label
        self.mapping = {
            k.upper(): v for k, v in self.mapping.items()
        }  # 2022 is all uppercase so complying with that

    def scrape(self):
        records = list()

        # get list of available years and urls
        r = requests.get(self.url)
        soup = bS(r.text, "lxml")
        years = [
            (int(a["href"].split("/")[-1].split("-")[0]), self.stem + a["href"])
            for a in soup.find("ol", {"id": "secondaryMenusecondaryNav"}).find_all(
                "a", href=re.compile(r".*-Crime-Statistics")
            )
        ]
        years = [year for year in years if year[0] >= self.first.year]

        # run through available years and collect data
        for year in years:
            self.logger.info(f"collecting {year[0]}...")

            r = requests.get(year[1])
            soup = bS(r.text, "lxml")
            table = soup.find("table")
            headers = [
                td.text.strip().upper() for td in table.find("tr").find_all("td")
            ]

            # account for 2024 column header update
            if headers[0] == "NIBRS CODE NAME":
                headers[0] = "NIBRS OFFENSES"

            rows = [
                [td.text.strip().upper() for td in tr.find_all("td")]
                for tr in table.find_all("tr")[1:]
            ]
            df = pd.DataFrame([dict(zip(headers, row)) for row in rows])

            # only keep relevant crimes
            df = df[df["NIBRS OFFENSES"].isin(self.mapping)]
            df[df.columns.difference({"NIBRS OFFENSES"})] = df[
                df.columns.difference({"NIBRS OFFENSES"})
            ].map(lambda s: int(s.strip("*")) if s != "" else None)
            df["NIBRS OFFENSES"] = df["NIBRS OFFENSES"].map(self.mapping)

            # workaround to deal with partially missing summed-row fields (e.g., 2022 table)
            df_stacked = df.groupby("NIBRS OFFENSES").transform(
                lambda g: None if g.isna().any() else g.sum()
            )
            df_stacked["NIBRS OFFENSES"] = df["NIBRS OFFENSES"]
            df_stacked = df_stacked.drop_duplicates("NIBRS OFFENSES")

            # reformat df
            df = (
                df_stacked.groupby("NIBRS OFFENSES")
                .sum(min_count=1)
                .reset_index()
                .set_index("NIBRS OFFENSES")
                .transpose()
                .reset_index()
                .rename(columns={"index": "date"})
                .rename_axis(None, axis=1)
            )

            # get date
            df = df[df["date"] != "TOTAL"]
            df["date"] = df["date"].apply(
                lambda s: dt.strptime(f"{s}{year[0]}", "%b%Y")
            )

            records.extend(df.to_dict("records"))

        return records


CA0070400().run()
