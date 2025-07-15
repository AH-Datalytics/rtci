import pandas as pd
import sys

sys.path.append("../../utils")
from super import Scraper


class AZ0100300(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["AZ0100300"]
        self.url = (
            "https://hub.arcgis.com/api/v3/datasets/982a2698677d4f6e8ef310171f7b4d9f_8/downloads/data?format"
            "=csv&spatialRefId=3857&where=1%3D1"
        )
        self.mapping = {
            "03 - ROBBERY": "robbery",
            "06 - LARCENY": "theft",
            "04 - ASSAULT, AGGRAVATED": "aggravated_assault",
            "01 - HOMICIDE": "murder",
            "07 - GTA": "motor_vehicle_theft",
            "05 - BURGLARY": "burglary",
            "02 - SEXUAL ASSAULT": "rape",
        }

    def scrape(self):
        df = pd.read_csv(self.url)[["Year", "Month", "UCRDescription"]]
        df = df[df["UCRDescription"].isin(self.mapping)]
        df["UCRDescription"] = df["UCRDescription"].map(self.mapping)
        df = df.rename(
            columns={"Year": "year", "Month": "month", "UCRDescription": "crime"}
        )
        df["month"] = pd.to_datetime(df["month"], format="%B").dt.month
        df = (
            (df.groupby(["year", "month"])["crime"].value_counts().reset_index())
            .pivot(index=["year", "month"], columns="crime", values="count")
            .reset_index()
        )
        return df.to_dict("records")


AZ0100300().run()
