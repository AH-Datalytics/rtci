import boto3
import json

from botocore.client import Config
from pympler import asizeof


BUCKET = "sample-rtci"


def get_s3_client():
    config = Config(connect_timeout=60 * 10, retries={"max_attempts": 5})
    return boto3.client("s3", config=config, region_name="us-east-1")


def list_files(prefix=None):
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


def list_directories(prefix=None, pagesize=1000):
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
