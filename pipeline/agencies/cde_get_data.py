import json
import pandas as pd
import requests
import sys
import urllib3

from collections import defaultdict
from datetime import datetime as dt
from datetime import timedelta as td
from time import time
from urllib3.exceptions import InsecureRequestWarning

sys.path.append("../utils")
from aws import snapshot_df
from logger import create_logger
from requests_configs import mount_session


"""
The CdeGetData class below uses a filtered set of ORIs
obtained by the `rtci/agencies/cde_filter_oris.py` python script
from the FBI's Crime Data Explorer API
( https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/docApi )
and stored as `rtci/fbi/cde_filtered_oris.csv` on AWS.

For each ORI-crime combination, it obtains monthly counts and clearances,
and saves this dataset to AWS as `rtci/fbi/cde_data_since_1985.csv`,
where `self.args.first` is specified as an arg (defaulting to "01-1985")
and `self.last` is the previous month.
"""


class CdeGetData:
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
        self.session = mount_session()

        # Suppress the specific InsecureRequestWarning
        urllib3.disable_warnings(InsecureRequestWarning)

    def scrape(self):
        """
        primary method, gets list of ORIs, queries each ORI for all crimes,
        processes results per-ORI to limit memory usage, and saves to AWS
        """
        # get set of filtered ORIs from AWS
        df = pd.read_csv(
            "https://rtci.s3.us-east-1.amazonaws.com/fbi/cde_filtered_oris.csv"
        )
        oris = df.to_dict("records")
        ori_columns = list(df.columns)
        self.logger.info(f"filtered oris: {len(oris)}")

        # process one ORI at a time to limit memory usage
        all_dfs = []
        for i, ori in enumerate(oris):
            try:
                ori_df = self.process_ori(ori, ori_columns)
                if ori_df is not None:
                    all_dfs.append(ori_df)
            except Exception as e:
                self.logger.warning(f"failed {ori['ori']}: {e}")

            if (i + 1) % 100 == 0:
                self.logger.info(f"processed {i + 1}/{len(oris)} oris")

        self.logger.info(f"processed {len(oris)}/{len(oris)} oris")

        # concatenate all ORI dataframes
        df = pd.concat(all_dfs, ignore_index=True)
        df = df.sort_values(by=["state", "ori", "year", "month"])
        df["last_updated"] = int(time())

        # save results to AWS
        self.logger.info(f"sample record: {df.to_dict('records')[0]}")
        if not self.args.test:
            snapshot_df(
                logger=self.logger,
                df=df,
                path="fbi/",
                filename=f"cde_data_since_{dt.strptime(self.args.first,'%m-%Y').year}",
            )

    def process_ori(self, ori, ori_columns):
        """
        queries all crimes for a single ORI and returns a merged dataframe
        """
        results = []
        for crime in self.crimes:
            url = self.url.format(ori["ori"], crime, self.args.first, self.last)
            data = json.loads(self.session.get(url, verify=False).text)["offenses"][
                "actuals"
            ]
            assert len(data.keys()) == 2

            # retrieve and format crime counts and clearances
            counts = data[[key for key in data if not key.endswith(" Clearances")][0]]
            clearances = data[[key for key in data if key.endswith(" Clearances")][0]]

            for k, v in counts.items():
                results.append({
                    "year": int(k.split("-", 1)[1]),
                    "month": int(k.split("-", 1)[0]),
                    self.crimes[crime]: v,
                })
            for k, v in clearances.items():
                results.append({
                    "year": int(k.split("-", 1)[1]),
                    "month": int(k.split("-", 1)[0]),
                    self.crimes[crime] + "_clearance": v,
                })

        # merge all crime results for this ORI
        merged = self.merge_dicts(results, ["year", "month"])
        df = pd.DataFrame(merged)

        # add ORI metadata columns
        for col in ori_columns:
            df[col] = ori[col]

        return df

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
        help="""If specified, no interactions with AWS S3 or sheets will take place.""",
    )
    parser.add_argument(
        "-f",
        "--first",
        type=str,
        default="01-1985",
        help="""Specify a start month/year in the format MM-YYYY (e.g., default "01-1985")""",
    )
    args = parser.parse_args()

    CdeGetData().scrape()
