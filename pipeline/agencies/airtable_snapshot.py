import sys

sys.path.append("../utils")
from airtable import get_records_from_sheet
from aws import snapshot_json
from logger import create_logger
from time import time


"""
The AirtableSnapshot class below saves a JSON snapshot of all records
currently in Airtable to AWS S3 as `rtci/airtable/{timestamp}`.
"""


class AirtableSnapshot:
    def __init__(self):
        self.logger = create_logger()

    def run(self):
        """
        get records from Airtable and save them to AWS
        """
        records = get_records_from_sheet(self.logger, "Metadata")
        self.logger.info(f"sample record: {records[0]}")

        snapshot_json(
            logger=self.logger,
            json_data=records,
            path="airtable/",
            timestamp=int(time()),
        )


if __name__ == "__main__":
    AirtableSnapshot().run()
