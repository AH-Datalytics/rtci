from os import environ

from pydantic import SecretStr

from rtci.model import Credentials, BotException


def create_credentials() -> Credentials:
    aws_access_key_id = environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = environ.get("AWS_SECRET_ACCESS_KEY")
    if not aws_access_key_id or not aws_secret_access_key:
        raise BotException(status_code=500, detail="AWS credentials not configured.")
    aws_region = environ.get("AWS_REGION_NAME", "us-east-1")
    return Credentials(
        aws_access_key_id=SecretStr(aws_access_key_id),
        aws_secret_access_key=SecretStr(aws_secret_access_key),
        aws_region=aws_region,
    )
