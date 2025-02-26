import pandas as pd
import sys

from datetime import datetime as dt

sys.path.append("../../utils")
from super import Scraper


class NY0140100(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["NY0140100"]
        self.url = "https://data.buffalony.gov/api/views/xxu9-yrhd/rows.csv?accessType=DOWNLOAD"
        self.mapping = {
            "Homicide": "murder",
            "Rape": "rape",
            "Robbery": "robbery",
            "Assault": "aggravated_assault",
            "Burglary": "burglary",
            "Larceny": "theft",
            "Motor Vehicle Theft": "motor_vehicle_theft",
        }

    def scrape(self):
        df = pd.read_csv(self.url)
        df["Date"] = pd.to_datetime(df["Date"])
        df["Month"] = df["Date"].dt.month
        df["Type"] = df["Type"].map(self.mapping)
        df = df[df["Type"].notna()]

        df = (
            df.groupby(["Year", "Month", "Type"])["Count"]
            .sum()
            .reset_index()
            .pivot(
                index=["Year", "Month"],
                columns="Type",
                values="Count",
            )
            .reset_index()
            .rename_axis(None, axis=1)
            .rename(columns={"Year": "year", "Month": "month"})
        )

        return df.to_dict("records")


NY0140100().run()
