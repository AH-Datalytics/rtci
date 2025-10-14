import pandas as pd
import requests
import sys

from io import StringIO

sys.path.append("../../utils")
from super import Scraper


class CA0190000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["CA0190000"]
        self.urls = [
            "http://shq.lasdnews.net/CrimeStats/CAASS/PART_I_AND_II_CRIMES-YTD.csv"
        ] + [
            f"http://shq.lasdnews.net/CrimeStats/CAASS/{year}-PART_I_AND_II_CRIMES.csv"
            for year in range(self.first.year, self.last.year)
        ]
        self.map = {
            "LARCENY THEFT": "theft",
            "BURGLARY": "burglary",
            "GRAND THEFT AUTO": "motor_vehicle_theft",
            "AGGRAVATED ASSAULT": "aggravated_assault",
            "ROBBERY": "robbery",
            "CRIMINAL HOMICIDE": "murder",
            "FORCIBLE RAPE": "rape",
        }

    def scrape(self):
        dfs = list()

        for url in self.urls:
            self.logger.info(f"attempting: {url}")
            r = requests.get(url).content
            df = pd.read_csv(
                StringIO(r.decode("utf-8")),
                on_bad_lines=self.fix_quotes,
                engine="python",
            )[["INCIDENT_REPORTED_DATE", "CATEGORY"]]
            df["INCIDENT_REPORTED_DATE"] = pd.to_datetime(df["INCIDENT_REPORTED_DATE"])
            df["year"] = df["INCIDENT_REPORTED_DATE"].dt.year
            df["month"] = df["INCIDENT_REPORTED_DATE"].dt.month
            del df["INCIDENT_REPORTED_DATE"]
            df = df[df["CATEGORY"].isin(self.map)]
            df["CATEGORY"] = df["CATEGORY"].map(self.map)
            dfs.append(df)

        df = pd.concat(dfs)
        df = (
            df.groupby(["year", "month"])["CATEGORY"]
            .value_counts()
            .reset_index()
            .pivot(index=["year", "month"], columns="CATEGORY", values="count")
        ).reset_index()
        return df.to_dict("records")

    @staticmethod
    def fix_quotes(line_parts):
        fixed_line = ",".join(line_parts)
        cleaned_line = fixed_line.replace('""', '"').replace('"', "")
        return cleaned_line.split(",")


CA0190000().run()
