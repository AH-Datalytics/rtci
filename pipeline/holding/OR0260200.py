import pandas as pd
import sys

sys.path.append("../utils")
from super import Scraper


class OR0260200(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["OR0260200"]
        self.url = "https://public.tableau.com/views/PPBOpenDataDownloads/CrimeData-{}.csv?:showVizHome=no"
        self.mapping = {
            "Murder and Non-negligent Manslaughter": "murder",
            "Rape": "rape",
            "Sodomy": "rape",
            "Robbery": "robbery",
            "Aggravated Assault": "aggravated_assault",
            "Burglary": "burglary",
            "Pocket-Picking": "theft",
            "Purse-Snatching": "theft",
            "Shoplifting": "theft",
            "Theft From Building": "theft",
            "Theft From Coin-Operated Machine or Device": "theft",
            "Theft From Motor Vehicle": "theft",
            "Theft of Motor Vehicle Parts or Accessories": "theft",
            "All Other Larceny": "theft",
            "Motor Vehicle Theft": "motor_vehicle_theft",
        }

    def scrape(self):
        dfs = list()

        for y in list(range(self.first.year, self.last.year + 1)):
            self.logger.info(f"collecting {y}...")
            url = self.url.format(y)
            df = pd.read_csv(url)[
                [
                    "ReportDate",
                    "OffenseType",
                    "OffenseCount",
                ]
            ]
            df["ReportDate"] = pd.to_datetime(df["ReportDate"])
            df["year"] = df["ReportDate"].dt.year
            df["month"] = df["ReportDate"].dt.month
            df["OffenseType"] = df["OffenseType"].map(self.mapping)
            df = df[df["OffenseType"].notna()]

            df = (
                df.groupby(["year", "month", "OffenseType"])["OffenseCount"]
                .sum()
                .reset_index()
                .pivot(
                    index=["year", "month"],
                    columns="OffenseType",
                    values="OffenseCount",
                )
                .reset_index()
                .rename_axis(None, axis=1)
            ).fillna(0)

            dfs.append(df)

        df = pd.concat(dfs)
        return df.to_dict("records")


OR0260200().run()
