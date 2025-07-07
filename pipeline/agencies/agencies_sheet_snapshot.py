import sys

sys.path.append("../utils")
from google_configs import gc_files, pull_sheet
from aws import snapshot_json
from logger import create_logger
from time import time


"""
The AgenciesSheetSnapshot class below saves a JSON snapshot of all records
currently in sheet to AWS S3 as `rtci/snapshots/{timestamp}/sample`, 
`rtci/snapshots/{timestamp}/archive and `rtci/snapshots/{timestamp}/scraping`.
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
        for tab in ["sample", "archive", "scraping"]:
            sheet = pull_sheet(
                sheet=tab,
                url=gc_files["agencies"],
            ).to_dict("records")

            self.logger.info(f"sample record: {tab[0]}")
            if not self.args.test:
                snapshot_json(
                    logger=self.logger,
                    json_data=sheet,
                    path="snapshots/",
                    timestamp=self.snapshot_time,
                    filename=tab,
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
