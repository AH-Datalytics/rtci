import boto3
import json
import os

from botocore.client import Config
from dotenv import load_dotenv
from pympler import asizeof


load_dotenv()


aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET = "rtci"


def get_s3_client():
    config = Config(connect_timeout=60 * 10, retries={"max_attempts": 5})
    return boto3.client(
        "s3",
        config=config,
        region_name="us-east-1",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )


def list_files(prefix=""):
    s3_client = get_s3_client()
    filenames = list()
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(
        Bucket=BUCKET, Prefix=prefix, PaginationConfig={"PageSize": 1000}
    )
    for page in pages:
        if page.get("Contents"):
            filenames.extend([file["Key"] for file in page.get("Contents")])
    return filenames


def list_directories(prefix="", pagesize=1000):
    s3_client = get_s3_client()
    directories = list()
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(
        Bucket=BUCKET,
        Prefix=prefix,
        Delimiter="/",
        PaginationConfig={"PageSize": pagesize},
    )
    for page in pages:
        for common_prefix in page.get("CommonPrefixes", []):
            directories.append(common_prefix["Prefix"])
    return directories


def snapshot_json(logger, json_data, path, timestamp=None, filename=None):
    if timestamp and not filename:
        path += str(timestamp)
    elif filename and not timestamp:
        path += str(filename)
    else:
        path += f"{timestamp}/{filename}"
    s3_client = get_s3_client()
    s3_client.put_object(
        Body=bytes(json.dumps(json_data, indent=2, default=str).encode("utf-8")),
        ContentType="application/json",
        Bucket=BUCKET,
        Key=path + ".json",
    )
    logger.info(f"transfer size: {asizeof.asizeof(json_data)} bytes")


def snapshot_pdf(logger, src_filename, path, timestamp=None, filename=None):
    if timestamp and not filename:
        path += str(timestamp)
    elif filename and not timestamp:
        path += str(filename)
    else:
        path += f"{timestamp}/{filename}"
    s3_client = get_s3_client()
    with open(src_filename, "rb") as file_data:
        s3_client.put_object(
            Body=file_data,
            Bucket=BUCKET,
            Key=path + ".pdf",
            ContentType="application/pdf",
        )
        logger.info(f"transfer size: {asizeof.asizeof(file_data)} bytes")


def snapshot_df(logger, df, path, timestamp=None, filename=None):
    if timestamp and not filename:
        path += str(timestamp)
    elif filename and not timestamp:
        path += str(filename)
    else:
        path += f"{timestamp}/{filename}"
    s3_client = get_s3_client()
    s3_client.put_object(
        Body=df.to_csv(index=False),
        Bucket=BUCKET,
        Key=path + ".csv",
    )
    logger.info(f"transfer size: {asizeof.asizeof(df)} bytes")


def snapshot_fig(logger, fig, path, timestamp=None, filename=None):
    html = fig.to_html(full_html=False, include_plotlyjs="cdn").encode("utf-8")
    if timestamp and not filename:
        path += str(timestamp)
    elif filename and not timestamp:
        path += str(filename)
    else:
        path += f"{timestamp}/{filename}"
    s3_client = get_s3_client()
    s3_client.put_object(
        Body=html, Bucket=BUCKET, Key=path + ".html", ContentType="text/html"
    )
    logger.info(f"transfer size: {asizeof.asizeof(fig)} bytes")
