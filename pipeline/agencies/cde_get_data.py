import json
import pandas as pd
import requests
import sys

from collections import defaultdict
from datetime import datetime as dt
from datetime import timedelta as td

sys.path.append("../utils")
from aws import snapshot_df
from logger import create_logger
from parallelize import thread


"""
The FbiCdeGetData class below uses a filtered set of ORIs
obtained by the `rtci/agencies/cde_filter_oris.py` python script 
from the FBI's Crime Data Explorer API
( https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/docApi )
and stored as `rtci/fbi/cde_filtered_oris.csv` on AWS.

For each ORI-crime combination, it obtains monthly counts and clearances,
and saves this dataset to AWS as `rtci/fbi/cde_data_since_1985.csv`,
where `self.args.first` is specified as an arg (defaulting to "01-1985")
and `self.last` is the previous month.
"""


class FbiCdeGetData:
    def __init__(self):
        self.args = parser.parse_args()
        self.logger = create_logger()
        self.last = dt.strftime(
            dt.now().replace(day=1, hour=23, minute=59, second=59, microsecond=999999)
            - td(days=1),
            "%m-%Y",
        )  # previous month
        self.crimes = {
            "HOM": "murder",
            "RPE": "rape",
            "ROB": "robbery",
            "ASS": "aggravated_assault",
            "BUR": "burglary",
            "LAR": "theft",
            "MVT": "motor_vehicle_theft",
        }
        self.url = "https://cde.ucr.cjis.gov/LATEST/summarized/agency/{}/{}?from={}&to={}&type=counts"

    def scrape(self):
        """
        primary method, gets list of ORIs, queries each ORI-crime combo
        for monthly counts and clearances data in specified timeframe,
        and saves to AWS
        """
        queries = list()

        # get set of filtered ORIs from AWS
        df = pd.read_csv(
            "https://rtci.s3.us-east-1.amazonaws.com/fbi/cde_filtered_oris.csv"
        )
        oris = df.to_dict("records")
        self.logger.info(f"filtered oris: {len(oris)}")

        # create one query for each ori-crime combination
        for crime in self.crimes:
            for ori in oris:
                queries.append({**ori, "crime": crime})
        self.logger.info(f"queries to run: {len(queries)}")

        # thread through to retrieve and format data
        results = thread(self.query, queries)
        results = [{k: v for k, v in d.items() if k != "crime"} for d in results]
        results = self.merge_dicts(results, list(df.columns) + ["year", "month"])
        df = pd.DataFrame(results).sort_values(by=["state", "ori", "year", "month"])

        # save results to AWS
        self.logger.info(f"sample record: {results[0]}")
        if not self.args.test:
            snapshot_df(
                logger=self.logger,
                df=df,
                path="fbi/",
                filename=f"cde_data_since_{dt.strptime(self.args.first,'%m-%Y').year}",
            )

    def query(self, q):
        """
        for a given ORI, crime and date range, retrieves monthly counts and clearances
        """
        url = self.url.format(q["ori"], q["crime"], self.args.first, self.last)
        data = json.loads(requests.get(url).text)["offenses"]["actuals"]
        assert len(data.keys()) == 2

        # retrieve and format crime counts and clearances
        counts = data[[key for key in data if not key.endswith(" Clearances")][0]]
        clearances = data[[key for key in data if key.endswith(" Clearances")][0]]
        counts = [
            {
                **q,
                "year": int(k.split("-", 1)[1]),
                "month": int(k.split("-", 1)[0]),
                self.crimes[q["crime"]]: v,
            }
            for k, v in counts.items()
        ]
        clearances = [
            {
                **q,
                "year": int(k.split("-", 1)[1]),
                "month": int(k.split("-", 1)[0]),
                self.crimes[q["crime"]] + "_clearance": v,
            }
            for k, v in clearances.items()
        ]
        return counts + clearances

    @staticmethod
    def merge_dicts(results, keys):
        """
        groups a list of dictionaries by multiple keys
        """
        merged_dict = defaultdict(list)

        for d in results:
            key = tuple(d[k] for k in keys)
            merged_dict[key].append(d)

        result = []
        for key, values in merged_dict.items():
            merged_values = {}
            for d in values:
                merged_values.update({k: v for k, v in d.items() if k not in keys})
            result.append(dict(zip(keys, key)) | merged_values)

        return result


if __name__ == "__main__":
    import argparse

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
        default="01-1985",
        help="""Specify a start month/year in the format MM-YYYY (e.g., default "01-1985)""",
    )
    args = parser.parse_args()

    FbiCdeGetData().scrape()
