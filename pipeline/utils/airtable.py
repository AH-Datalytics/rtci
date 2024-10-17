import os

from dotenv import load_dotenv
from pyairtable import Api


load_dotenv()


def get_airtable_sheet(sheet_name):
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    return Api(api_key).table(base_id, sheet_name)


def get_records_from_sheet(logger, sheet_name, formula=None):
    worker = get_airtable_sheet(sheet_name)
    records = worker.all(formula=formula)
    if not records:
        logger.warning(f"No records found in Airtable table: {sheet_name}")
    logger.info(f"Found {len(records)} records in Airtable {sheet_name}")
    return [d["fields"] for d in records]


def insert_to_airtable_sheet(logger, sheet_name, to_insert, typecast=True):
    worker = get_airtable_sheet(sheet_name)
    worker.batch_create(to_insert, typecast=typecast)
    logger.info(f"Inserted {len(to_insert)} records into Airtable {sheet_name}")
