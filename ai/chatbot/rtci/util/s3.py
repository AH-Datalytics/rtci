import boto3

from rtci.util.credentials import create_credentials


def create_s3_client():
    creds = create_credentials()
    if creds.aws_access_key_id and creds.aws_secret_access_key:
        return boto3.client(
            's3',
            region_name=creds.aws_region,
            aws_access_key_id=creds.aws_access_key_id.get_secret_value(),
            aws_secret_access_key=creds.aws_secret_access_key.get_secret_value()
        )
    else:
        return boto3.client('s3', region_name=creds.aws_region)


def delete_s3_bucket(s3_bucket_name: str,
                     s3_key_name: str):
    s3_client = create_s3_client()
    print(f"Deleting object from S3 bucket: {s3_bucket_name}, key: {s3_key_name}")
    s3_client.delete_object(
        Bucket=s3_bucket_name,
        Key=s3_key_name
    )
