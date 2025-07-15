import numpy as np
import pandas as pd
import sys

from datetime import datetime as dt
from datetime import timedelta as td

sys.path.append("../utils")
from aws import list_directories, list_files, snapshot_df
from crimes import rtci_to_nibrs
from google_configs import gc_files, pull_sheet
from logger import create_logger


# TODO: fill in FBI CDE clearance data (in `agencies/cde_get_data.py`)
#       [note: also separate out source columns for crime (scraper vs. FBI) and clearance]
#       [and add in city vs. county]


# TODO: add in the following list of exceptions
#    Agency_State	Comment
#    Allen, TX	Inferred Jan-Mar 2022 from annual average
#    Bethlehem, PA	Inferred Dec 2019 from annual average
#    Corvallis, OR	Inferred Oct-Dec 2019 from reported state total
#    Eagan, MN	Inferred Aug 2020 from annual average
#    Midland, TX	Inferred Jul-Dec 2021 from police reported annual total
#    Mount Prospect, IL	Inferred Jan-Mar 2021 counts from annual average
#    Oak Lawn, IL	Inferred Jan 2021 counts from annual average
#    Palatine, IL	Inferred Jan-Mar 2021 counts from annual average
#    Schaumburg, IL	Inferred Jan-Mar 2021 from annual average
#    South Bend, IN	Inferred Apr-Nov 2021 from annual state total
#    Stockton, CA	Inferred Jan-Feb 2021 from annual state total


class AggregatedSince:
    def __init__(self):
        self.logger = create_logger()
        self.bucket_url = "https://rtci.s3.us-east-1.amazonaws.com/"
        self.fbi = pd.read_csv(self.bucket_url + "fbi/cde_data_since_1985.csv")
        self.fbi["source"] = "FBI"
        self.fbi = self.fbi.add_prefix("fbi_")
        self.crimes = rtci_to_nibrs
        self.first = dt(2017, 1, 1, 0, 0)
        self.last = (
            dt.now().replace(day=1, hour=23, minute=59, second=59, microsecond=999999)
            - td(days=1)
        ).replace(day=1) - td(
            days=1
        )  # last day of month before last
        self.sheet = pull_sheet(sheet="sample", url=gc_files["agencies"])

    def run(self):
        dfs = list()

        # iterate through directories to get down to files
        states = list_directories(prefix=f"scrapes/")
        assert len(states) > 0

        for s in states:
            dirs = list_directories(prefix=f"{s}")
            assert len(dirs) > 0

            for d in dirs:
                # get latest JSON file for each agency scrape
                files = list_files(prefix=f"{d}")
                assert len(files) > 0
                fn = files[-1]
                state = fn.split("/")[-3]
                self.logger.info(f"reading {fn}...")
                df = pd.read_json(self.bucket_url + fn)
                df["source"] = "Scraper"

                agency = self.sheet[self.sheet["ori"] == fn.split("/")[2]]
                assert len(agency) <= 1

                if len(agency) == 1:
                    agency = agency.iloc[0]["name"]
                    df["state"] = state
                    df.insert(loc=0, column="agency_name", value=agency)

                    if len(df.columns) == 14:
                        df = df[
                            [
                                "ori",
                                "agency_name",
                                *self.crimes,
                                "year",
                                "month",
                                "state",
                                "last_updated",
                                "source",
                            ]
                        ]
                    elif len(df.columns) == 21:
                        df = df[
                            [
                                "ori",
                                "agency_name",
                                *self.crimes,
                                *[f"{crime}_cleared" for crime in self.crimes],
                                "year",
                                "month",
                                "state",
                                "last_updated",
                                "source",
                            ]
                        ]
                    else:
                        self.logger.warning(f"issue with: {fn}")
                        pd.set_option("display.max_columns", 100)
                        raise ValueError(f"wrong number of columns in df:\n{df.head()}")

                    df = df.sort_values(by=["agency_name", "year", "month"])

                    df = pd.merge(
                        df,
                        self.fbi[self.fbi["fbi_ori"] == fn.split("/")[2]],
                        how="outer",
                        left_on=["ori", "year", "month"],
                        right_on=["fbi_ori", "fbi_year", "fbi_month"],
                    )

                    for crime in self.crimes:
                        df[crime] = np.where(
                            df[crime].isna(), df[f"fbi_{crime}"], df[crime]
                        )

                    for col in ["ori", "year", "month", "source"]:
                        df[col] = np.where(df[col].isna(), df[f"fbi_{col}"], df[col])

                    for col in ["agency_name", "state", "last_updated"]:
                        df[col] = df[col].fillna(df[col].dropna().unique()[0])

                    df = df.loc[:, ~df.columns.str.startswith("fbi_")]

                    for col in ["year", "month", "last_updated"]:
                        df[col] = df[col].astype(int)

                    df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
                    df = df[df["date"] >= self.first]
                    df = df[df["date"] <= self.last]
                    del df["date"]

                dfs.append(df)

        # combine all agencies into one state df and save to s3
        df = pd.concat(dfs)

        df.columns = [s.replace("_", " ").title() for s in df.columns]
        df = df.rename(columns={"Ori": "ORI"})

        snapshot_df(
            logger=self.logger,
            df=df,
            path="qc/",
            filename=f"aggregated_since_{self.first.year}",
        )


if __name__ == "__main__":
    AggregatedSince().run()
