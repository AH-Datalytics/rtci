import csv
import io
import re
import time
import uuid
from datetime import datetime
from os import environ
from pathlib import Path

from rtci.rtci import RealTimeCrime
from rtci.util.collections import get_first_header_index
from rtci.util.database import CrimeDatabase
from rtci.util.log import logger
from rtci.util.s3 import create_s3_client

database_key = f"database-{str(uuid.uuid4())}"


def create_database() -> CrimeDatabase:
    csv_content = RealTimeCrime.file_cache.get(key=database_key)
    if not csv_content:
        s3_bucket = environ.get("AWS_S3_BUCKET", "rtci")
        s3_key_name = environ.get("AWS_S3_DATASET_KEY", "rtci/final_sample.csv")
        csv_content = load_csv_to_memory(s3_bucket, s3_key_name)
        csv_content = transform_csv_to_file_cache(csv_content)
    return CrimeDatabase.from_csv(csv_content)


def load_csv_to_memory(s3_bucket_name: str,
                       s3_key_name: str) -> str:
    # read CSV file from S3 bucket
    logger().info(f"Retrieving CSV file from S3 bucket: {s3_bucket_name}, key: {s3_key_name} ...")
    s3_client = create_s3_client()
    s3_response = s3_client.get_object(Bucket=s3_bucket_name, Key=s3_key_name)
    csv_content = s3_response['Body'].read().decode('utf-8')
    if not csv_content:
        raise Exception("No CSV content found in S3 object.")
    return csv_content


def transform_csv_to_file_cache(csv_content: str) -> str:
    # prase CSV content and map columns to indexes
    csv_reader = csv.reader(io.StringIO(csv_content))
    header = next(csv_reader)
    column_indexes = {}
    column_indexes['date'] = get_first_header_index(header, ['Date'])
    column_indexes['month'] = get_first_header_index(header, ['Month'])
    column_indexes['year'] = get_first_header_index(header, ['Year'])
    column_indexes['reporting_agency'] = get_first_header_index(header, ['Agency', 'Location'])
    column_indexes['city_state'] = get_first_header_index(header, ['Agency State', 'Agency_State', 'city_state'])
    column_indexes['state'] = get_first_header_index(header, ['State'])
    column_indexes['murder'] = get_first_header_index(header, ['Murder'])
    column_indexes['rape'] = get_first_header_index(header, ['Rape'])
    column_indexes['robbery'] = get_first_header_index(header, ['Robbery'])
    column_indexes['aggravated_assault'] = get_first_header_index(header, ['Aggravated Assault', 'aggravated_assault'])
    column_indexes['burglary'] = get_first_header_index(header, ['Burglary'])
    column_indexes['theft'] = get_first_header_index(header, ['Theft'])
    column_indexes['motor_vehicle_theft'] = get_first_header_index(header, ['Motor Vehicle Theft', 'motor_vehicle_theft'])
    column_indexes['property_crime'] = get_first_header_index(header, ['Property Crime', 'property_crime'])

    # create a new CSV in memory with only the required columns
    output = io.StringIO()
    csv_writer = csv.writer(output)
    csv_writer.writerow(column_indexes.keys())

    # process each row and extract only the required columns
    for row in csv_reader:
        if not filter_full_sample_rows(row, column_indexes):
            # print(f"Filtered out row: {row}.")
            continue
        new_row = []
        year = int(row[column_indexes['year']])
        month = int(row[column_indexes['month']])
        for col_name, col_index in column_indexes.items():
            if col_name == "date":
                new_row.append(datetime(year=year, month=month, day=1).strftime("%Y-%m-%d"))
            elif col_index is not None:
                value = row[col_index]
                if value == 'NA' or value == '' or value == 'N/A' or value == 'NONE':
                    new_row.append(None)
                else:
                    new_row.append(row[col_index])
        csv_writer.writerow(new_row)

    # prepare filtered CSV content and write to file store
    ttl_min = 60 * 24
    csv_content = output.getvalue()
    RealTimeCrime.file_cache.set(key=database_key,
                                 value=csv_content,
                                 ttl=ttl_min * 60)
    return csv_content


def filter_full_sample_rows(row, column_indexes):
    # remove full sample rolled-up data
    full_sample_pattern = re.compile(r'full\s*sample', re.IGNORECASE)
    if (column_indexes['reporting_agency'] is not None and
            full_sample_pattern.search(row[column_indexes['reporting_agency']])):
        return False
    if (column_indexes['city_state'] is not None and
            full_sample_pattern.search(row[column_indexes['city_state']])):
        return False

    # remove nation-wide data
    if (column_indexes['state'] is not None and
            row[column_indexes['state']].lower() == 'nationwide'):
        return False

    # keep the row if neither condition is met
    return True


def execute_redshift_query(redshift_data,
                           redshift_workgroup_name: str,
                           redshift_dbname: str,
                           query: str,
                           error_message: str = None,
                           sleep_time_sec: int = 2):
    response = redshift_data.execute_statement(
        WorkgroupName=redshift_workgroup_name,
        Database=redshift_dbname,
        Sql=query
    )
    query_id = response['Id']
    if not query_id:
        raise Exception("Unable to determine query ID. Please check your query and try again.")
    while True:
        status_response = redshift_data.describe_statement(Id=query_id)
        status = status_response['Status']
        if status == 'FINISHED':
            return status_response
        elif status in ['FAILED', 'ABORTED']:
            if error_message:
                if 'Error' in status_response:
                    raise Exception(f"{error_message} with error: {status_response['Error']}")
                else:
                    raise Exception(f"{error_message} with status: {status}")
            else:
                print(f"Query failed with status: {status_response}.")
                return status_response
        time.sleep(sleep_time_sec)


def map_headers_to_columns(header):
    int_columns = ['year', 'month', 'murder', 'rape', 'robbery', 'aggravated_assault', 'burglary', 'theft', 'motor_vehicle_theft', 'property_crime']
    date_columns = ['date', 'last_modified', 'last_updated']
    definitions = []
    for col in header:
        if col in int_columns:
            definitions.append(f'"{col}" INT NULL')
        elif col in date_columns:
            definitions.append(f'"{col}" DATE')
        else:
            definitions.append(f'"{col}" VARCHAR(255) NULL')
    return definitions


def cleanup_old_files(target_dir: str | Path,
                      file_pattern='.*\.png',
                      hours=24):
    # Ensure the directory exists
    if not target_dir.exists() or not target_dir.is_dir():
        return 0

    pattern = re.compile(file_pattern)
    current_time = time.time()
    max_age_seconds = hours * 3600
    deleted_count = 0

    # Iterate through all files in the directory
    for item in target_dir.glob('**/*'):
        if item.is_file():
            # Check if the filename matches the pattern
            if pattern.search(item.name):
                file_age = current_time - item.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        item.unlink()
                        deleted_count += 1
                        logger().debug(f"Deleted old file: {item}.")
                    except Exception as e:
                        logger().error(f"Failed to delete {item}.", e)
    return deleted_count
