import pandas as pd
import requests
import sys

from io import StringIO

sys.path.append("../../utils")
from super import Scraper


class CA0331300(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["CA0331300"]
        self.url = (
            "https://www.riversideca.gov/transparency/data/dataset/csv/27/Crime_Reports"
        )
        self.mapping = {
            # murder
            "HOMICIDE: MURDER & NON-NEGLIGENT MANSLAUGHTER": "murder",
            "MURDER AND NON-NEGLIGENT MANSLAUGHTER": "murder",
            # rape
            # robbery
            "ROBBERY": "robbery",
            "ROBBERY: FIREARM": "robbery",
            "ROBBERY: KNIFE OR CUTTING INSTRUMENT": "robbery",
            "ROBBERY: OTHER DANGEROUS WEAPON": "robbery",
            "ROBBERY: STRONG-ARM": "robbery",
            # aggravated_assault
            "AGGRAVATED ASSAULT": "aggravated_assault",
            "ASSAULT: FIREARM": "aggravated_assault",
            "ASSAULT: KNIFE OR CUTTING INSTRUMENT": "aggravated_assault",
            "ASSAULT: OTHER ASSAULTS": "aggravated_assault",
            "ASSAULT: OTHER DANGEROUS WEAPON": "aggravated_assault",
            "ASSAULT: STRONG-ARM": "aggravated_assault",
            # burglary
            "BURGLARY/BREAKING AND ENTERING": "burglary",
            "BURGLARY: ATTEMPTED FORCIBLE ENTRY": "burglary",
            "BURGLARY: FORCIBLE ENTRY": "burglary",
            "BURGLARY: UNLAWFUL ENTRY - NO FORCE": "burglary",
            # theft
            "ALL OTHER LARCENY": "theft",
            "POCKET-PICKING": "theft",
            "PURSE-SNATCHING": "theft",
            "SHOPLIFTING": "theft",
            "THEFT FROM BUILDING": "theft",
            "THEFT FROM COIN-OPERATED MACHINE OR DEVICE": "theft",
            "THEFT FROM MOTOR VEHICLE": "theft",
            "THEFT OF MOTOR VEHICLE PARTS OR ACCESSORIES": "theft",
            "THEFT: ALL OTHER LARCENY": "theft",
            "THEFT: POCKET PICKING": "theft",
            "THEFT: PURSE SNATCHING": "theft",
            "THEFT: SHOPLIFTING": "theft",
            "THEFT: THEFT FROM BUILDINGS": "theft",
            "THEFT: THEFT FROM COIN-OPERATED MACHINE OR DEVICE": "theft",
            "THEFT: THEFT FROM MOTOR VEHICLE": "theft",
            "THEFT: THEFT OF BICYCLES": "theft",
            "THEFT: THEFT OF MOTOR VEHICLE PARTS OR ACCESSORIES": "theft",
            # motor_vehicle_theft
            "MOTOR VEH. THEFT: AUTOS": "motor_vehicle_theft",
            "MOTOR VEH. THEFT: OTHER VEHICLES": "motor_vehicle_theft",
            "MOTOR VEH. THEFT: TRUCKS AND BUSES": "motor_vehicle_theft",
            "MOTOR VEHICLE THEFT": "motor_vehicle_theft",
        }

    def scrape(self):
        r = requests.get(self.url).content
        df = pd.read_csv(StringIO(r.decode("utf-8")))[["reportDate", "crimeType"]]

        # extract year and month
        df["reportDate"] = pd.to_datetime(df["reportDate"])
        df["year"] = df["reportDate"].dt.year
        df["month"] = df["reportDate"].dt.month
        del df["reportDate"]

        # extract crime
        df["crimeType"] = df["crimeType"].str.upper()
        df["crimeType"] = df["crimeType"].map(self.mapping)
        df = df[df["crimeType"].notna()]

        # get monthly counts and report
        df = (
            (df.groupby(["year", "month"])["crimeType"].value_counts().reset_index())
            .pivot(index=["year", "month"], columns="crimeType", values="count")
            .reset_index()
        )

        # note: usually we do not fill missing values with 0s,
        # but in this case values are counts from running through
        # the full set of incidents, so if there's a systematically
        # missing field, we'll have to pick it up later in audit
        for crime in self.crimes:
            if crime in df.columns:
                df[crime] = df[crime].fillna(0).astype(int)

        return df.to_dict("records")


CA0331300().run()
