import pandas as pd
import sys

from datetime import datetime as dt
from datetime import timedelta as td

sys.path.append("../utils")

from logger import create_logger


class Auditor:
    def __init__(self, arguments):
        self.logger = create_logger()
        self.args = arguments
        self.bucket_url = "https://rtci.s3.us-east-1.amazonaws.com/data/aggregated.csv"
        self.last = dt.now().replace(
            day=1, hour=23, minute=59, second=59, microsecond=999999
        ) - td(
            days=1
        )  # last day of month before last
        self.removals_1 = list()
        self.removals_2 = list()
        self.removals_3 = list()
        self.removals_4 = list()

        pd.set_option("display.max_columns", 100)

    def run(self):
        df = pd.read_csv(self.bucket_url)
        df["date"] = df["year"].astype(str) + "_" + df["month"].astype(str)

        for ori in df["ori"].unique():
            print(ori, df[df["ori"] == ori]["date"].max())
            # print(ori)
            # tmp = df[df["ori"] == ori]
            # print(tmp)
            #
            # if tmp[tmp[]]
            #
            # break


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="""If flagged, output a sample graph locally.""",
    )
    args = parser.parse_args()
    Auditor(args).run()
