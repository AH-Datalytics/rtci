import sys

sys.path.append("../utils")
from google_configs import gc_files, pull_sheet
from aws import snapshot_json
from logger import create_logger
from time import time


"""
The AgenciesSheetSnapshot class below saves a JSON snapshot of all records
currently in sheet to AWS S3 as `rtci/snapshots/{timestamp}/sample` and 
`rtci/snapshots/{timestamp}/archive.
"""


class AgenciesSheetSnapshot:
    def __init__(self, arguments):
        self.logger = create_logger()
        self.args = arguments
        self.snapshot_time = int(time())

    def run(self):
        """
        get records from sheet and save them to AWS
        """
        # pull the sample tab of the sheet
        sample = pull_sheet(
            sheet="sample",
            url=gc_files["agencies"],
        ).to_dict("records")
        self.logger.info(f"sample record: {sample[0]}")

        # pull the archive tab of the sheet
        archive = pull_sheet(
            sheet="archive",
            url=gc_files["agencies"],
        ).to_dict("records")
        self.logger.info(f"sample archive record: {archive[0]}")

        # save both to json
        if not self.args.test:
            snapshot_json(
                logger=self.logger,
                json_data=sample,
                path="snapshots/",
                timestamp=self.snapshot_time,
                filename="sample",
            )
            snapshot_json(
                logger=self.logger,
                json_data=archive,
                path="snapshots/",
                timestamp=self.snapshot_time,
                filename="archive",
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="""If flagged, do not interact with S3.""",
    )
    args = parser.parse_args()

    AgenciesSheetSnapshot().run()
