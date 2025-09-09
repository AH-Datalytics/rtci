import asyncio
import csv
import datetime
import io
import time
from os import environ

import boto3

from rtci.rtci import RealTimeCrime
from rtci.util.collections import get_first_header_index
from rtci.util.credentials import create_credentials
from rtci.util.s3 import create_s3_client, delete_s3_bucket


def load_csv_to_memory(s3_bucket_name: str,
                       s3_key_name: str) -> str:
    # read CSV file from S3 bucket
    s3_client = create_s3_client()
    print(f"Retrieving CSV file from S3 bucket: {s3_bucket_name}, key: {s3_key_name}")
    s3_response = s3_client.get_object(Bucket=s3_bucket_name, Key=s3_key_name)
    csv_content = s3_response['Body'].read().decode('utf-8')
    if not csv_content:
        raise Exception("No CSV content found in S3 object.")
    return csv_content


def transform_csv_to_s3(csv_content: str,
                        s3_bucket_name: str,
                        s3_key_name: str) -> str:
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
    # column_indexes['region'] = get_first_header_index(header, ['Region'])
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
        new_row = []
        year = int(row[column_indexes['year']])
        month = int(row[column_indexes['month']])
        for col_name, col_index in column_indexes.items():
            if col_name == "date":
                new_row.append(datetime.datetime(year=year, month=month, day=1).strftime("%Y-%m-%d"))
            elif col_index is not None:
                value = row[col_index]
                if value == 'NA' or value == '' or value == 'N/A' or value == 'NONE':
                    new_row.append(None)
                else:
                    new_row.append(row[col_index])
        csv_writer.writerow(new_row)

    # prepare filtered CSV content and write to S3 bucket
    filtered_csv_content = output.getvalue()
    s3_client = create_s3_client()
    print(f"Uploading filtered CSV to S3: s3://{s3_bucket_name}/{s3_key_name}")
    s3_client.put_object(
        Bucket=s3_bucket_name,
        Key=s3_key_name,
        Body=filtered_csv_content.encode('utf-8')
    )
    return filtered_csv_content


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


def load_csv_to_redshift(csv_content: str,
                         s3_bucket_name: str,
                         s3_key_name: str,
                         redshift_workgroup_name: str,
                         redshift_dbname: str,
                         redshift_table_name: str,
                         redshift_iam_role: str,
                         bedrock_iam_role: str) -> str:
    creds = create_credentials()

    # connect to boto3 clients for Redshift Data API and S3
    # ensure you set IAM roles in the serverless namespace / security section
    print(f"Connecting to Redshift cluster ...")
    redshift_data = boto3.client(
        'redshift-data',
        region_name=creds.aws_region,
        aws_access_key_id=creds.aws_access_key_id.get_secret_value(),
        aws_secret_access_key=creds.aws_secret_access_key.get_secret_value()
    )

    # Parse CSV header to generate column schema
    csv_reader = csv.reader(io.StringIO(csv_content))
    header = next(csv_reader)

    # drop the existing table if it exists
    print(f"Dropping existing table: {redshift_table_name}")
    drop_query = f"DROP TABLE IF EXISTS {redshift_table_name}"
    execute_redshift_query(redshift_data,
                           redshift_workgroup_name,
                           redshift_dbname,
                           drop_query,
                           "Failed to drop table")

    # create a new table with columns based on CSV headers
    column_definitions = ', '.join(map_headers_to_columns(header))
    create_query = f"CREATE TABLE {redshift_table_name} ({column_definitions});"
    print(f"Creating new table with schema derived from CSV: {redshift_table_name} as {create_query} ...")
    execute_redshift_query(redshift_data,
                           redshift_workgroup_name,
                           redshift_dbname,
                           create_query,
                           "Create table query failed")

    # get current account information
    client = boto3.client(
        "sts",
        aws_access_key_id=creds.aws_access_key_id.get_secret_value(),
        aws_secret_access_key=creds.aws_secret_access_key.get_secret_value())
    account_data = client.get_caller_identity()
    account_id = account_data['UserId'] or account_data['Account']
    arn_id = f"arn:aws:iam::{account_id}:role/{redshift_iam_role}"

    # ensure the IAM role has privs
    # https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-prereq-structured.html#knowledge-base-prereq-structured-service-role
    print(f"Granting role table permissions: {redshift_table_name} with {bedrock_iam_role} ...")
    schemaName = "public"
    execute_redshift_query(redshift_data,
                           redshift_workgroup_name,
                           redshift_dbname,
                           f"CREATE USER \"IAMR:{bedrock_iam_role}\" WITH NOCREATEUSER PASSWORD DISABLE;")
    # GRANT SELECT ON ALL TABLES IN SCHEMA ${schemaName} TO "IAMR:${serviceRole}";
    # GRANT SELECT ON ${schemaName}.${tableName} TO "IAMR:${serviceRole}";
    execute_redshift_query(redshift_data,
                           redshift_workgroup_name,
                           redshift_dbname,
                           f"GRANT SELECT ON ALL TABLES IN SCHEMA {schemaName} TO \"IAMR:{bedrock_iam_role}\";")
    # GRANT USAGE ON SCHEMA ${schemaName} TO "IAMR:${serviceRole}";
    execute_redshift_query(redshift_data,
                           redshift_workgroup_name,
                           redshift_dbname,
                           f"GRANT USAGE ON SCHEMA {schemaName} TO \"IAMR:{bedrock_iam_role}\";")

    # use COPY command to load data from S3 to Redshift
    print(f"Loading data from S3 to Redshift table: {redshift_table_name} ...")
    columns = ', '.join([f'"{col}"' for col in header])
    copy_query = f"""
    COPY {redshift_table_name} ({columns})
    FROM 's3://{s3_bucket_name}/{s3_key_name}'
    IAM_ROLE '{arn_id}'
    CSV
    TRUNCATECOLUMNS
    IGNOREHEADER 1
    """
    execute_redshift_query(redshift_data,
                           redshift_workgroup_name,
                           redshift_dbname,
                           copy_query,
                           "COPY command failed")

    # confirm the number of rows loaded
    count_query = f"SELECT COUNT(*) FROM {redshift_table_name}"
    response = redshift_data.execute_statement(
        WorkgroupName=redshift_workgroup_name,
        Database=redshift_dbname,
        Sql=count_query
    )
    execute_redshift_query(redshift_data,
                           redshift_workgroup_name,
                           redshift_dbname,
                           count_query,
                           "Count query failed")
    results = redshift_data.get_statement_result(Id=response['Id'])
    row_count = results['Records'][0][0]['longValue']
    print(f"Successfully loaded {row_count} rows into Redshift table: {redshift_table_name}")


async def run_import_async():
    RealTimeCrime.bootstrap()
    s3_bucket = environ.get("AWS_S3_BUCKET", "rtci")
    s3_key_name = environ.get("AWS_S3_DATASET_KEY", "rtci/final_sample.csv")
    temp_s3_key = f"rtci/tmp_{int(time.time())}.csv"
    try:
        csv_content = load_csv_to_memory(s3_bucket, s3_key_name)
        csv_content = transform_csv_to_s3(csv_content, s3_bucket, temp_s3_key)
        redshift_workgroup_name = environ.get("AWS_REDSHIFT_WORKGROUP", "default-workgroup")
        redshift_dbname = environ.get("AWS_REDSHIFT_DATABASE", "dev")
        redshift_tablename = environ.get("AWS_REDSHIFT_TABLE", "crime_data")
        redshift_iam_role = environ.get("AWS_REDSHIFT_IAM_ROLE", "AmazonRedshiftOperationsWithS3")
        bedrock_iam_role = environ.get("AWS_BEDROCK_IAM_ROLE", "AmazonBedrockExecutionRoleForKnowledgeBaseOverRedshift")
        try:
            load_csv_to_redshift(csv_content, s3_bucket, temp_s3_key,
                                 redshift_workgroup_name, redshift_dbname, redshift_tablename,
                                 redshift_iam_role, bedrock_iam_role)
        finally:
            delete_s3_bucket(s3_bucket, temp_s3_key)
    finally:
        await RealTimeCrime.shutdown()


if __name__ == "__main__":
    asyncio.run(run_import_async())
