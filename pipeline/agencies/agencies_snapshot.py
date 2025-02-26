import sys

sys.path.append("../utils")
from google_configs import gc_files, pull_sheet
from aws import snapshot_json
from logger import create_logger
from time import time


"""
The AgenciesSnapshot class below saves a JSON snapshot of all records
currently in sheet to AWS S3 as `rtci/snapshots/{timestamp}`.
"""


class AgenciesSnapshot:
    def __init__(self):
        self.logger = create_logger()

    def run(self):
        """
        get records from sheet and save them to AWS
        """
        records = pull_sheet(
            sheet=gc_files["agencies"]["sheet"],
            url=gc_files["agencies"]["url"],
        ).to_dict("records")
        self.logger.info(f"sample record: {records[0]}")

        snapshot_json(
            logger=self.logger,
            json_data=records,
            path="snapshots/",
            timestamp=int(time()),
        )


if __name__ == "__main__":
    AgenciesSnapshot().run()
