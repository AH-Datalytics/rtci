import pandas as pd
import sys

sys.path.append("../../utils")
from super import Scraper


class NY0270100(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["NY0270100"]
        self.url = (
            "https://hub.arcgis.com/api/v3/datasets/74c62e65e3b347e289a07d02d4b8c899_3/downloads/data?format"
            "=csv&spatialRefId=2262&where=1%3D1"
        )
        self.mapping = {
            "Murder": "murder",
            "Non-Negligent Manslaughter": "murder",
            "Robbery": "robbery",
            "Aggravated Assault": "aggravated_assault",
            "Burglary": "burglary",
            "Larceny": "theft",
            "Motor Vehicle Theft": "motor_vehicle_theft",
        }

    def scrape(self):
        df = pd.read_csv(self.url)[["Reported_Timestamp", "Statute_Text"]]
        df["Reported_Timestamp"] = pd.to_datetime(df["Reported_Timestamp"])
        df["year"] = df["Reported_Timestamp"].dt.year
        df["month"] = df["Reported_Timestamp"].dt.month
        df["crime"] = df["Statute_Text"].map(self.mapping)
        df = df[df["crime"].notna()]

        df = (
            df.groupby(["year", "month"])["crime"]
            .value_counts()
            .reset_index()
            .pivot(
                index=["year", "month"],
                columns="crime",
                values="count",
            )
            .reset_index()
        ).fillna(0.0)

        return df.to_dict("records")


NY0270100().run()
