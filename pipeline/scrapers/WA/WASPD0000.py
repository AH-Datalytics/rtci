import pandas as pd
import sys

sys.path.append("../../utils")
from super import Scraper


class WASPD0000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["WASPD0000"]
        self.url = ""
        self.mapping = {
            "09A": "murder",
            "11A": "rape",
            "11B": "rape",
            "11C": "rape",
            "120": "robbery",
            "13A": "aggravated_assault",
            "220": "burglary",
            "240": "motor_vehicle_theft",
            "23A": "theft",
            "23B": "theft",
            "23C": "theft",
            "23D": "theft",
            "23E": "theft",
            "23F": "theft",
            "23G": "theft",
            "23H": "theft",
        }

    def scrape(self):
        pass

        # df = pd.read_csv(
        #     "/Users/ojt/Downloads/SPD_Crime_Data__2008-Present_20250211.csv"
        # )[["Report DateTime", "Offense Code"]]
        #
        # df["Report DateTime"] = pd.to_datetime(df["Report DateTime"])
        # df["year"] = df["Report DateTime"].dt.year
        # df["month"] = df["Report DateTime"].dt.month
        # df["crime"] = df["Offense Code"].map(self.mapping)
        # df = df[df["crime"].notna()]
        #
        # # get monthly counts and report
        # df = (
        #     (df.groupby(["year", "month"])["crime"].value_counts().reset_index())
        #     .pivot(index=["year", "month"], columns="crime", values="count")
        #     .reset_index()
        # )
        #
        # return df.to_dict("records")


WASPD0000().run()
