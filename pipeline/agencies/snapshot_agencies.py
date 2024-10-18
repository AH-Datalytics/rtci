import sys

sys.path.append("../utils")
from airtable import get_records_from_sheet
from aws import snapshot_json
from logger import create_logger
from time import time


logger = create_logger()


# retrieve airtable data
records = get_records_from_sheet(logger, "Metadata")


# stash as json in aws
logger.info("sample record:")
logger.info(f"{records[0]}")
snapshot_json(
    logger=logger,
    json_data=records,
    path="airtable/",
    timestamp=int(time()),
)
