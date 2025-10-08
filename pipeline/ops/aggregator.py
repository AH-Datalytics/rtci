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


class Aggregator:
    def __init__(self, arguments):
        self.logger = create_logger()
        self.args = arguments
        self.crimes = rtci_to_nibrs

        # get first and last dates (2017 to last day of last month)
        self.first = dt(2017, 1, 1, 0, 0)
        self.last = dt.now().replace(
            day=1, hour=23, minute=59, second=59, microsecond=999999
        ) - td(days=1)

        # pull in google sheet, existing aggregated csv, and fbi data
        self.bucket_url = "https://rtci.s3.us-east-1.amazonaws.com/"
        self.sheet = pull_sheet(sheet="sample", url=gc_files["agencies"])
        self.agg = self.get_agg_data()
        self.fbi = self.get_fbi_data()

    def run(self):
        dfs = list()

        fns = self.get_files()

        for fn in fns:
            self.logger.info(f"reading {fn}...")
            df = pd.read_json(self.bucket_url + fn)
            assert df["year"].dtype == "int"
            assert df["month"].dtype == "int"
            df = df.sort_values(by=["year", "month"])
            ori = list(df["ori"].unique())
            assert len(ori) == 1
            ori = ori[0]

            # add in state, agency name, type (city/county)
            df["state"] = fn.split("/")[-3]
            agency = self.sheet[self.sheet["ori"] == fn.split("/")[2]]
            assert len(agency) <= 1
            name = agency.iloc[0]["name"]
            df["name"] = name
            city_county = agency.iloc[0]["type"]
            df["type"] = city_county

            # subset agg and fbi to the appropriate ori
            agg = self.agg[self.agg["ori"] == ori]
            fbi = self.fbi[self.fbi["ori"] == ori]
            assert len(fbi) > 0

            # if this is a new agency (not yet in the aggregated csv),
            # insert into aggregated csv, otherwise upsert
            if len(agg) == 0:
                out = df
            else:
                out = self.incorporate_new(agg, df)

            # logger checks to see if latest month incremented
            self.logger.info(
                f"previous range: "
                f"{str(agg[agg['year'] == agg['year'].min()]['month'].min()).zfill(2)}/{agg['year'].min()} "
                f"to {str(agg[agg['year'] == agg['year'].max()]['month'].max()).zfill(2)}/{agg['year'].max()}"
            )
            self.logger.info(
                f"update range: "
                f"{str(out[out['year'] == out['year'].min()]['month'].min()).zfill(2)}/{out['year'].min()} "
                f"to {str(out[out['year'] == out['year'].max()]['month'].max()).zfill(2)}/{out['year'].max()} "
            )

            # merge in fbi data
            out = pd.merge(
                out,
                fbi,
                how="outer",
                on=["ori", "year", "month"],
            ).sort_values(by=["ori", "year", "month"])

            # adjust data for crimes, clearances, and last updated date
            for crime in self.crimes:
                out[crime] = np.where(
                    out[crime].isna(),
                    out[f"fbi_{crime}"],
                    out[crime],
                )
                out[f"{crime}_cleared"] = np.where(
                    out[f"{crime}_cleared"].isna(),
                    out[f"fbi_{crime}_clearance"],
                    out[f"{crime}_cleared"],
                )

            out["last_updated"] = np.where(
                out["last_updated"].isna(),
                out["fbi_last_updated"],
                out["last_updated"],
            )

            # remove fbi cols and clean up
            out = out.loc[:, ~out.columns.str.startswith("fbi_")]

            # add in state, agency name, type (city/county), again...
            out["state"] = fn.split("/")[-3]
            out["name"] = name
            out["type"] = city_county
            out["last_updated"] = out["last_updated"].astype(int)

            for col in ["year", "month", "last_updated"]:
                assert out[col].dtype == "int"

            dfs.append(out)

        # stitch back together all dfs into one for export
        df = pd.concat(dfs)
        df = df.sort_values(by=["ori", "year", "month"])
        df = df[
            [
                "ori",
                "state",
                "name",
                "type",
                "year",
                "month",
                *self.crimes,
                *[f"{crime}_cleared" for crime in self.crimes],
                "last_updated",
            ]
        ]

        self.logger.info(f"sample record: {df.to_dict('records')[0]}")
        if not self.args.test:
            snapshot_df(
                logger=self.logger,
                df=df,
                path="data/",
                filename=f"aggregated",
            )

    @staticmethod
    def get_files():
        """
        returns a list of aws s3 filepaths
        for each ori's latest scraped json data file
        """
        fns = list()

        # get list of state directories from s3
        states = list_directories(prefix=f"scrapes/")
        assert len(states) > 0

        # get list of ori directories for a given state
        for state in states:
            dirs = list_directories(prefix=f"{state}")
            assert len(dirs) > 0

            # get latest json file for each ori
            for d in dirs:
                files = list_files(prefix=f"{d}")
                assert len(files) > 0
                fns.append(files[-1])

        return fns

    def get_agg_data(self):
        """
        reads in existing `aggregated.csv` file
        """
        agg = pd.read_csv(self.bucket_url + "data/aggregated.csv")
        assert agg["year"].dtype == "int"
        assert agg["month"].dtype == "int"
        agg[["year", "month"]] = agg[["year", "month"]].astype(int)
        for col in agg.columns:
            if "source" in col:
                agg = agg.drop(columns=[col])
        self.logger.info(f"agg data: {agg['year'].min()} to {agg['year'].max()}")
        return agg

    def get_fbi_data(self):
        """
        reads in fbi cde api data from 1985 on and subsets
        from first year (2017) to last month with non-missing data
        """
        fbi = pd.read_csv(self.bucket_url + "fbi/cde_data_since_1985.csv")
        fbi = fbi[
            fbi[
                list(self.crimes.keys())
                + [f"{crime}_clearance" for crime in self.crimes.keys()]
            ]
            .isnull()
            .sum(axis=1)
            == 0
        ]
        fbi = fbi.add_prefix("fbi_")
        assert fbi["fbi_year"].dtype == "int"
        assert fbi["fbi_month"].dtype == "int"
        fbi[["fbi_year", "fbi_month"]] = fbi[["fbi_year", "fbi_month"]].astype(int)
        fbi = fbi[fbi["fbi_year"] >= self.first.year]
        for col in fbi.columns:
            if "source" in col:
                fbi = fbi.drop(columns=[col])
        self.logger.info(
            f"fbi data: {fbi['fbi_year'].min()} to {fbi['fbi_year'].max()}"
        )
        fbi = fbi.rename(
            columns={
                "fbi_ori": "ori",
                "fbi_year": "year",
                "fbi_month": "month",
            }
        )
        return fbi

    @staticmethod
    def incorporate_new(agg, df):
        """
        takes new data for a given ori and merges it into the existing aggregated data
        """
        new = df[
            (df["year"] == agg["year"].max())
            & (df["month"] > agg[agg["year"] == agg["year"].max()]["month"].max())
        ]
        agg = agg.set_index(["ori", "year", "month"])
        df = df.set_index(["ori", "year", "month"])
        agg.update(df)
        agg = agg.reset_index()
        agg = pd.concat([agg, new])
        return agg


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="""If flagged, do not interact with sheet.""",
    )
    args = parser.parse_args()

    Aggregator(args).run()
