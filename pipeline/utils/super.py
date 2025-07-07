import argparse
import inspect
import os
import pandas as pd
import sys
import us

from datetime import datetime as dt
from datetime import timedelta as td
from dateutil.relativedelta import relativedelta
from pathlib import Path
from time import time

sys.path.append("../utils")
import crosswalks

from logger import create_logger
from airtable import insert_to_airtable_sheet
from aws import snapshot_json
from crimes import rtci_to_nibrs


parser = argparse.ArgumentParser()
parser.add_argument(
    "-t",
    "--test",
    action="store_true",
    help="""If specified, no interactions with AWS S3 or Airtable will take place.""",
)
parser.add_argument(
    "-f",
    "--first",
    type=str,
    nargs="?",
    const="2017-01",
    default=None,
    help="""
    Start date from which to collect monthly data 
    (defaults to '2017-01' in format '%Y-%m').
    """,
)
parser.add_argument(
    "-v",
    "--visible",
    default=False,
    action="store_true",
    help="""
    If specified, selenium driver will produce a visible browser window (this can only be used locally for 
    testing, since the Docker environment on the remote server does not have a screen).
    """,
)


class Scraper:
    def __init__(self):
        self.args = parser.parse_args()
        self.logger = create_logger()
        self.run_time = int(time())
        self.crimes = rtci_to_nibrs
        self.crosswalks = crosswalks
        self.state = str(Path.cwd()).split("/")[-1]
        self.state_full_name = us.states.lookup(self.state).name
        self.oris = []
        self.first = self.set_first()
        self.last = (
            dt.now().replace(day=1, hour=23, minute=59, second=59, microsecond=999999)
            - td(days=1)
        ).replace(day=1) - td(
            days=1
        )  # last day of month before last
        self.logger.info(f"collecting data from {self.first} to {self.last}")
        self.collected_earliest = None
        self.collected_latest = None

    def set_first(self):
        if self.args.first:
            return dt.strptime(self.args.first, "%Y-%m")

        # if no specified first date arg, retrieve the most recent ledger of
        # earliest and latest collected data dates
        most_recent_run = pd.read_csv(
            "https://rtci.s3.us-east-1.amazonaws.com/crosswalks/most_recent_run.csv"
        )

        # get the name of the file from which the scrape is running
        child_class = type(self)
        child_module = inspect.getmodule(child_class)
        child_file_path = child_module.__file__
        scraper = os.path.basename(child_file_path)[:-3]

        # if the latest data date has already been documented, start from 12 months prior
        if len(most_recent_run) > 0 and scraper in most_recent_run["scraper"].unique():
            rows = most_recent_run[most_recent_run["scraper"] == scraper]
            assert len(rows["data_to"].unique()) == 1
            data_to = rows["data_to"].unique()[0]
            if isinstance(data_to, str) and data_to != "":
                return (
                    dt.strptime(data_to, "%Y-%m")
                    - td(days=365)
                    + relativedelta(months=1)
                )

        # if no data default to earliest
        return dt(2017, 1, 1, 0, 0)

    @staticmethod
    def scrape():
        return []

    @staticmethod
    def check_for_comma(s):
        if isinstance(s, str):
            return float(str(s).replace(",", ""))
        elif isinstance(s, int):
            return float(s)
        else:
            return s

    def process(self, data):
        # assert data is a non-empty list and every record has a date
        assert isinstance(data, list)
        assert len(data) > 0

        df = pd.DataFrame(data)

        # ensure dates are valid, no data goes beyond last day of month before last
        if "date" not in df.columns and "year" in df.columns and "month" in df.columns:
            df["date"] = pd.to_datetime(df[["year", "month"]].assign(DAY=1))
        df = df[(df["date"] >= self.first) & (df["date"] <= self.last)]

        # ensure ori is present in standalone cases
        if "ori" not in df.columns and len(self.oris) == 1:
            df["ori"] = self.oris[0]
        else:
            assert "ori" in df.columns and len(df[df["ori"].isna()]) == 0

        # fill out placeholder columns for missing crimes
        for crime in self.crimes:
            if crime in df.columns:
                df[crime] = df[crime].apply(lambda s: self.check_for_comma(s))
            else:
                df[crime] = None
            if f"{crime}_cleared" in df.columns:
                df[f"{crime}_cleared"] = df[f"{crime}_cleared"].apply(
                    lambda s: self.check_for_comma(s)
                )
            else:
                df[f"{crime}_cleared"] = None

            # produce 12-month rolling sums per crime
            # df[f"{crime}_mvs_12mo"] = (
            #     df.sort_values(by=["ori", "date"])
            #     .groupby("ori")[crime]
            #     .transform(lambda g: g.rolling(window=12).sum())
            # )

        self.collected_earliest = dt.strftime(df["date"].min().date(), "%Y-%m")
        self.collected_latest = dt.strftime(df["date"].max().date(), "%Y-%m")

        # extract year and month from data
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        del df["date"]

        # add run time metadata field
        df["last_updated"] = self.run_time

        # check on column counts
        assert len(df.keys()) == 18
        return df.to_dict("records")

    def run(self):
        # collect and process data
        data = self.scrape()
        processed = self.process(data)
        self.logger.info(f"sample record: {processed[0]}")

        # export data
        if not self.args.test:
            self.logger.info("exporting to aws s3 and airtable...")
            self.export(processed)

        self.logger.info(f"earliest data: {self.collected_earliest}")
        self.logger.info(f"latest data: {self.collected_latest}")
        self.logger.info(f"completed oris: {self.oris}")

    def export(self, processed):
        airtable_meta = list()

        for ori in self.oris:
            # subset to data for the specified ori and push to aws s3
            agency_data = [d for d in processed if d["ori"] == ori]
            snapshot_json(
                logger=self.logger,
                json_data=agency_data,
                path=f"scrapes/{self.state}/{ori}/",
                timestamp=self.run_time,
            )

            # update airtable with status and attempt/success times
            # TODO: does not currently take into account last_attempt...
            # TODO: ...move this into bash script?
            airtable_meta.append(
                {
                    "fields": {
                        "ori": ori,
                        "status": "Good",
                        "last_attempt": dt.strftime(
                            dt.fromtimestamp(self.run_time), "%Y-%m-%d %H:%M:%S"
                        ),
                        "last_success": dt.strftime(
                            dt.fromtimestamp(self.run_time), "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                }
            )

        insert_to_airtable_sheet(
            logger=self.logger,
            sheet_name="Metadata",
            to_insert=airtable_meta,
            upsert=True,
            keys=["ori"],
        )
