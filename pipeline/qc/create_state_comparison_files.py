import pandas as pd
import sys

sys.path.append("../utils")

from airtable import get_records_from_sheet
from aws import list_directories, list_files, snapshot_df
from logger import create_logger


class TestGenerator:
    def __init__(self, arguments):
        self.logger = create_logger()
        self.args = arguments
        self.stem = "https://sample-rtci.s3.us-east-1.amazonaws.com/"

    def run(self):
        for state in self.args.states:
            dfs = list()

            # get all agency subdirectories for state
            dirs = list_directories(prefix=f"scrapes/{state}/")
            assert len(dirs) > 0

            for d in dirs:
                # get latest JSON file for each agency scrape
                files = list_files(prefix=f"{d}")
                assert len(files) > 0
                fn = files[-1]
                df = pd.read_json(self.stem + fn)

                # pull RTCI agency name from Airtable
                agency = get_records_from_sheet(
                    self.logger,
                    "Metadata",
                    formula=f"AND({{ori}}='{fn.split('/')[2]}',NOT({{agency_rtci}}=''))",
                )

                assert len(agency) <= 1

                if agency:
                    agency = agency[0]["agency_rtci"]

                    # format things like the current `{}_Aggregated_Since_2017.csv` auditing files
                    df = df[[c for c in df.columns if not c.endswith("_12mo")]]
                    df = df.drop(columns=["ori", "last_updated"])
                    df.columns = df.columns.str.title()
                    df.columns = df.columns.str.replace("_", " ")
                    df["State"] = state
                    df.insert(loc=0, column="Agency Name", value=agency)
                    df = df[
                        [
                            "Agency Name",
                            "Murder",
                            "Rape",
                            "Robbery",
                            "Aggravated Assault",
                            "Burglary",
                            "Theft",
                            "Motor Vehicle Theft",
                            "Year",
                            "Month",
                            "State",
                        ]
                    ].sort_values(by=["Agency Name", "Year", "Month"])

                    dfs.append(df)

            # combine all agencies into one state df and save to s3
            df = pd.concat(dfs)

            snapshot_df(
                logger=self.logger,
                df=df,
                path="state-outputs/",
                filename=state,
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--states",
        nargs="*",
        help="""List of states for which to produce test outputs.""",
    )
    args = parser.parse_args()

    TestGenerator(args).run()
