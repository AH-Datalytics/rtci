import pandas as pd
import sys

sys.path.append("../../utils")
from super import Scraper


class DCMPD0000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["DCMPD0000"]
        self.format = "https://hub.arcgis.com/api/v3/datasets/{}/downloads/data?format=csv&spatialRefId=26985&where=1%3D1"
        self.urls = {
            k: self.format.format(v)
            for k, v in {
                2017: "6af5cb8dc38e4bcbac8168b27ee104aa_38",
                2018: "38ba41dd74354563bce28a359b59324e_0",
                2019: "f08294e5286141c293e9202fcd3e8b57_1",
                2020: "f516e0dd7b614b088ad781b0c4002331_2",
                2021: "619c5bd17ca2411db0689bb0a211783c_3",
                2022: "f9cc541fc8c04106a05a1a4f1e7e813c_4",
                2023: "89561a4f02ba46cca3c42333425d1b87_5",
                2024: "c5a9f33ffca546babbd91de1969e742d_6",
                2025: "74d924ddc3374e3b977e6f002478cb9b_7",
            }.items()
        }
        self.map = {
            "HOMICIDE": "murder",
            "SEX ABUSE": "rape",
            "ASSAULT W/DANGEROUS WEAPON": "aggravated_assault",
            "BURGLARY": "burglary",
            "ROBBERY": "robbery",
            "MOTOR VEHICLE THEFT": "motor_vehicle_theft",
            "THEFT/OTHER": "theft",
            "THEFT F/AUTO": "theft",
        }
        self.records = list()

    def scrape(self):
        for year, url in self.urls.items():
            df = pd.read_csv(url)[["REPORT_DAT", "OFFENSE"]]
            df["REPORT_DAT"] = pd.to_datetime(df["REPORT_DAT"])
            df["year"] = df["REPORT_DAT"].dt.year
            df["month"] = df["REPORT_DAT"].dt.month
            del df["REPORT_DAT"]
            df = df[df["OFFENSE"].isin(self.map)]
            df["OFFENSE"] = df["OFFENSE"].map(self.map)
            df = (
                df.groupby(["year", "month"])["OFFENSE"]
                .value_counts()
                .reset_index()
                .pivot(index=["year", "month"], columns="OFFENSE", values="count")
            ).reset_index()
            self.records.append(df)

        self.records = pd.concat(self.records)
        self.records = self.records.groupby(["year", "month"]).sum().reset_index()
        return self.records.to_dict("records")


DCMPD0000().run()
