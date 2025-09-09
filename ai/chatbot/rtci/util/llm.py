from langchain_aws import ChatBedrockConverse
from langchain_core.language_models import BaseChatModel

from rtci.model import Credentials
from rtci.util.credentials import create_credentials


def create_llm() -> BaseChatModel:
    creds: Credentials = create_credentials()
    # model_name = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    model_name = "anthropic.claude-3-haiku-20240307-v1:0"
    return ChatBedrockConverse(
        model=model_name,
        aws_access_key_id=creds.aws_access_key_id,
        aws_secret_access_key=creds.aws_secret_access_key,
        region_name=creds.aws_region,
        temperature=0,
        max_tokens=3000
    )
