import argparse
import pandas as pd
import sys
import us

from datetime import datetime as dt
from datetime import timedelta as td
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
        self.first = dt(2017, 1, 1, 0, 0, 0, 000000)
        self.last = (
            dt.now().replace(day=1, hour=23, minute=59, second=59, microsecond=999999)
            - td(days=1)
        ).replace(day=1) - td(
            days=1
        )  # last day of month before last
        self.logger.info(f"collecting data from {self.first} to {self.last}")

    @staticmethod
    def scrape():
        return []

    def process(self, data):
        # assert data is a non-empty list and every record has a date
        assert isinstance(data, list)
        assert len(data) > 0

        df = pd.DataFrame(data)

        # ensure dates are valid, no data goes beyond last day of month before last
        if "date" not in df.columns and "year" in df.columns and "month" in df.columns:
            df["date"] = pd.to_datetime(df[["year", "month"]].assign(DAY=1))
        df = df[df["date"] <= self.last]

        # ensure ori is present in standalone cases
        if "ori" not in df.columns and len(self.oris) == 1:
            df["ori"] = self.oris[0]
        else:
            assert "ori" in df.columns and len(df[df["ori"].isna()]) == 0

        # produce 12-month rolling sums per crime
        for crime in self.crimes:
            df[f"{crime}_mvs_12mo"] = (
                df.sort_values(by=["ori", "date"])
                .groupby("ori")[crime]
                .transform(lambda g: g.rolling(window=12).sum())
            )

        # extract year and month from data
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        del df["date"]

        # add run time metadata field
        df["last_updated"] = self.run_time

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
