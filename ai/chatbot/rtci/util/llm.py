import boto3
from langchain_aws import ChatBedrockConverse
from langchain_core.language_models import BaseChatModel
from pandasai_litellm import LiteLLM

from rtci.model import Credentials
from rtci.util.credentials import create_credentials

model_name = "anthropic.claude-3-haiku-20240307-v1:0"  # "anthropic.claude-3-5-haiku-20241022-v1:0"


def create_llm() -> BaseChatModel:
    creds: Credentials = create_credentials()
    return ChatBedrockConverse(
        model=model_name,
        aws_access_key_id=creds.aws_access_key_id,
        aws_secret_access_key=creds.aws_secret_access_key,
        region_name=creds.aws_region,
        temperature=0.0,
        max_tokens=4000
    )


def create_lite_llm() -> LiteLLM:
    creds: Credentials = create_credentials()
    bedrock_runtime_client = boto3.client(
        'bedrock-runtime',
        aws_access_key_id=creds.aws_access_key_id.get_secret_value(),
        aws_secret_access_key=creds.aws_secret_access_key.get_secret_value(),
        region_name=creds.aws_region
    )
    return LiteLLM(
        model=f"bedrock/{model_name}",
        temperature=0.0
    )
