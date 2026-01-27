import json
import numpy as np
import pandas as pd
import requests
import sys

from datetime import datetime as dt
from datetime import timedelta as td

sys.path.append("../utils")
from aws import list_directories, list_files, snapshot_df, snapshot_json
from logger import create_logger
from parallelize import thread


class SiteCrimes:
    def __init__(self, arguments):
        pd.set_option("display.max_columns", 100)
        self.logger = create_logger()
        self.args = arguments

        # crime groupings (violent vs. property)
        self.crimes = {
            "violent": ["murder", "rape", "robbery", "aggravated_assault"],
            "property": ["burglary", "theft", "motor_vehicle_theft"],
        }
        self.map = {
            "violent": "violent",
            "murder": "murder",
            "rape": "rape",
            "robbery": "robbery",
            "aggravated_assault": "assault",
            "property": "property",
            "burglary": "burglary",
            "theft": "theft",
            "motor_vehicle_theft": "motor",
        }

        # define date range for inclusion (2017-01-01 to end of month before last)
        self.start = dt(2017, 1, 1, 0, 0)
        self.end = (
            (
                dt.now().replace(day=1, hour=23, minute=0, second=0, microsecond=0)
                - td(days=1)
            ).replace(day=1)
            - td(days=1)
        ).replace(day=1, hour=0, minute=0)
        self.logger.info(f"date range: {self.start} to {self.end}")

        # read in `data/aggregated.csv`
        self.agg = pd.read_csv(
            "https://rtci.s3.us-east-1.amazonaws.com/data/aggregated.csv"
        )

        # add in total violent and property columns
        for k, v in self.crimes.items():
            self.agg[k] = self.agg[v].sum(axis=1)
            self.agg[f"{k}_cleared"] = self.agg[[f"{el}_cleared" for el in v]].sum(
                axis=1
            )

        # rename columns per specifications
        for col in self.map:
            self.agg = self.agg.rename(
                columns={
                    col: self.map[col],
                    f"{col}_cleared": f"{self.map[col]}_cleared",
                }
            )

        # read in geographies table data produced by `db_geographies.py`
        self.geographies = pd.read_csv(
            "https://rtci.s3.us-east-1.amazonaws.com/data/site/geographies.csv"
        )

        # read in the mapping of included oris to geographies in `data/site/geographies_included.json`
        self.geographies_included = json.loads(
            requests.get(
                "https://rtci.s3.us-east-1.amazonaws.com/data/site/geographies_included.json"
            ).text
        )

        self.df = None

    def run(self):
        # merge geographic entity metadata into per-agency aggregated crime counts data
        self.df = pd.merge(
            self.agg,
            self.geographies.drop(
                columns=[
                    "name",
                    "state",
                ]
            ).rename(columns={"type": "geography_type"}),
            how="left",
            left_on="ori",
            right_on="id",
        )

        # run through geographic entities and aggregate data
        results = thread(
            self.prepare_one_geography, self.geographies_included, threads=10
        )
        results = pd.DataFrame(results)

        # reorder columns per specification
        results = results[
            [
                "id",
                "size",
                "year",
                "month",
            ]
            + [
                col
                for col in results.columns
                if col not in ["id", "size", "year", "month"]
            ]
        ]

        # only include data from 1 year post-start (2017 + 1)
        results = results[results["year"] > self.start.year]

        # replace instances of infinity (division by zero) with none
        results.replace([np.inf, -np.inf], None, inplace=True)

        self.logger.info(f"sample record: {results.to_dict('records')[0]}")
        if not self.args.test:
            snapshot_df(
                self.logger, results, "data/site/", filename="current_crime_reported"
            )

    def prepare_one_geography(self, d):
        # in the ytd percent changes there may be infinite values from division by zero
        np.seterr(divide="ignore", invalid="ignore")

        # only keep agencies that are in geographic entity and trim to specified date ranges
        tmp = self.df[self.df["ori"].isin(d["agency_list"])].copy()
        tmp.loc[:, "date"] = pd.to_datetime(tmp[["year", "month"]].assign(day=1))
        tmp = tmp[(tmp["date"] >= self.start) & (tmp["date"] <= self.end)]

        # sum crime counts across geographic entities and year-months
        tmp = (
            tmp.groupby(["year", "month"])[list(self.map.values())].sum().reset_index()
        )
        tmp["id"] = d["id"]
        tmp["size"] = d["size"]

        # get total crime counts per geography-month
        totals = self.get_totals(tmp)

        # get ytd crime count sums per geography-month and merge into totals
        ytds = self.get_ytds(tmp)
        totals = pd.merge(
            totals,
            ytds,
            how="left",
            left_on=["id", "size", "year", "month"],
            right_on=["id_ytd", "size_ytd", "year_ytd", "month_ytd"],
        ).drop(columns=["id_ytd", "size_ytd", "year_ytd", "month_ytd"])

        # get rollings 12-month crime count sums per geography-month and merge into totals
        rolls = self.get_rolls(tmp)
        totals = pd.merge(totals, rolls, how="left", on=["id", "size", "year", "month"])

        # get percent changes in crime count sums for ytd vs. lytd per geography-month and merge into totals
        totals = self.get_deltas(totals)

        return totals.to_dict("records")

    def get_totals(self, tmp):
        return tmp.rename(
            columns=lambda c: c + "_total" if c in list(self.map.values()) else c
        )

    @staticmethod
    def get_ytds(tmp):
        ytds = list()
        for year in tmp["year"].unique():
            for month in tmp[tmp["year"] == year]["month"].unique():
                ytd = tmp[(tmp["year"] == year) & (tmp["month"] <= month)]
                ytd = ytd.groupby(["id", "size"]).sum().reset_index()
                ytd["year"] = year
                ytd["month"] = month
                ytds.append(ytd)
        ytd = pd.concat(ytds)
        return ytd.add_suffix("_ytd")

    def get_rolls(self, tmp):
        roll = tmp.copy()
        roll.loc[:, "date"] = pd.to_datetime(roll[["year", "month"]].assign(day=1))
        roll = roll.set_index("date")
        for col in list(self.map.values()):
            roll[f"{col}_roll"] = roll[col].rolling(window="365D", min_periods=12).sum()
            roll = roll.drop(columns=[col])
        return roll.reset_index().drop(columns=["date"])

    def get_deltas(self, totals):
        for year in totals["year"].unique():
            for month in totals[totals["year"] == year]["month"].unique():
                cy = totals[(totals["year"] == year) & (totals["month"] == month)].iloc[
                    0
                ]
                py = totals[(totals["year"] == year - 1) & (totals["month"] == month)]
                assert len(py) <= 1

                if len(py) == 1:
                    py = py.iloc[0]
                    for v in list(self.map.values()):
                        totals.loc[
                            (totals["year"] == year) & (totals["month"] == month),
                            f"{v}_change",
                        ] = round(
                            ((cy[f"{v}_ytd"] - py[f"{v}_ytd"]) / py[f"{v}_ytd"] * 100),
                            1,
                        )
        return totals


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

    SiteCrimes(args).run()
