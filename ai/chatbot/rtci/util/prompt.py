import glob
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

from botocore.exceptions import ClientError
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from rtci.util.log import logger
from rtci.util.s3 import create_s3_client


class PromptResource(BaseModel):
    """Represents a prompt resource with its identifiers and locations."""

    prompt_id: str
    s3_bucket_key: str
    relative_file_path: str


class PromptLibrary:
    """Manages string prompts with S3 and local file system integration."""

    @classmethod
    def create(cls,
               prompts_dir: str | Path = os.path.join('rtci', 'prompts'),
               s3_base_name: str = "prompts",
               ignore_s3: bool = False):
        s3_bucket = os.environ.get("AWS_S3_BUCKET", "rtci")
        s3_base_name = s3_base_name.rstrip('/\\')
        prompts = []
        if os.path.exists(prompts_dir):
            for file_path in glob.glob(os.path.join(prompts_dir, '*.txt')):
                filename = os.path.basename(file_path)
                prompt_id = os.path.splitext(filename)[0]
                prompt_resource = PromptResource(
                    prompt_id=prompt_id,
                    s3_bucket_key=f"{s3_base_name}/{filename}",
                    relative_file_path=str(Path(file_path))
                )
                logger().debug(f"Adding prompt resource: {prompt_resource}.")
                prompts.append(prompt_resource)
        return PromptLibrary(prompts, s3_bucket, ignore_s3)

    def __init__(self, prompt_resources: List[PromptResource], bucket_name: str, ignore_s3: bool):
        self.prompt_resources = list(prompt_resources)
        self.prompt_cache: Dict[str, str] = {}
        self.bucket_name = bucket_name
        self.ignore_s3 = ignore_s3

    def find_prompt(self, prompt_id: str) -> ChatPromptTemplate:
        prompt_text = self.find_text(prompt_id)
        return ChatPromptTemplate.from_template(prompt_text)

    def find_text(self, prompt_id: str) -> str:
        """
        Retrieve a prompt by its ID. Attempts to fetch from S3 first, then falls back to local file.
        Results are cached in memory for subsequent requests.

        Args:
            prompt_id: ID of the prompt to retrieve

        Returns:
            The prompt text content

        Raises:
            ValueError: If the prompt_id is not found in the configured resources
        """
        # Return from cache if available
        if prompt_id in self.prompt_cache:
            return self.prompt_cache[prompt_id]

        # Find the resource for the given prompt_id
        resource = self._find_resource(prompt_id)
        if not resource:
            raise ValueError(f"Prompt with ID '{prompt_id}' not found in configured resources")

        # Try to fetch from S3 first
        prompt_text = self._fetch_from_s3(resource)

        # If S3 fetch failed, try local file
        if not prompt_text:
            prompt_text = self._fetch_from_local(resource)

            # If we got the prompt from local file, update S3 as well
            if prompt_text:
                try:
                    self._store_to_s3(resource, prompt_text)
                except Exception as e:
                    logger().error(f"Warning: Failed to update S3 with local prompt '{prompt_id}'", e)

        # If we got the prompt, cache it for future use
        if prompt_text:
            self.prompt_cache[prompt_id] = prompt_text
            return prompt_text

        raise FileNotFoundError(f"Prompt '{prompt_id}' not found in S3 or local file system")

    def store_prompt(self, prompt_id: str, prompt_text: str) -> bool:
        """
        Store a prompt by its ID to both the local file system and S3.

        Args:
            prompt_id: ID of the prompt to store
            prompt_text: Text content of the prompt

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If the prompt_id is not found in the configured resources
        """
        # Find the resource for the given prompt_id
        resource = self._find_resource(prompt_id)
        if not resource:
            raise ValueError(f"Prompt with ID '{prompt_id}' not found in configured resources")

        # Store locally first
        local_success = self._store_to_local(resource, prompt_text)

        # Then store to S3
        s3_success = False
        try:
            s3_success = self._store_to_s3(resource, prompt_text)
        except Exception as e:
            logger().error(f"Warning: Failed to store prompt '{prompt_id}' to S3: {e}", e)

        # Update cache
        if local_success:
            self.prompt_cache[prompt_id] = prompt_text

        return local_success and s3_success

    def push_prompts(self) -> Dict[str, bool]:
        """
        Push all configured prompts from local files to S3.

        Returns:
            Dictionary mapping prompt_ids to success status
        """
        results = {}

        for resource in self.prompt_resources:
            try:
                # Load from local
                prompt_text = self._fetch_from_local(resource)
                if not prompt_text:
                    results[resource.prompt_id] = False
                    continue

                # Store to S3
                success = self._store_to_s3(resource, prompt_text)
                results[resource.prompt_id] = success
            except Exception as e:
                print(f"Error pushing prompt '{resource.prompt_id}' to S3: {e}")
                results[resource.prompt_id] = False

        return results

    def pull_prompts(self) -> Dict[str, bool]:
        """
        Fetch all configured prompts from S3 and save them locally.

        This method attempts to download all prompts from the S3 bucket based on
        the configured prompt resources and saves them to the local file system.

        Returns:
            Dictionary mapping prompt_ids to success status (True if successfully
            downloaded and saved locally, False otherwise)
        """
        results = {}

        for resource in self.prompt_resources:
            try:
                # Fetch from S3
                prompt_text = self._fetch_from_s3(resource)
                if not prompt_text:
                    logger().warning(f"Prompt '{resource.prompt_id}' not found in S3 bucket '{self.bucket_name}'")
                    results[resource.prompt_id] = False
                    continue

                # Store locally
                success = self._store_to_local(resource, prompt_text)

                # Update cache if successful
                if success:
                    self.prompt_cache[resource.prompt_id] = prompt_text

                results[resource.prompt_id] = success
            except Exception as e:
                logger().error(f"Error pulling prompt '{resource.prompt_id}' from S3", e)
                results[resource.prompt_id] = False

        return results

    def _find_resource(self, prompt_id: str) -> Optional[PromptResource]:
        """Find a prompt resource by its ID."""
        for resource in self.prompt_resources:
            if resource.prompt_id == prompt_id:
                return resource
        return None

    def _fetch_from_s3(self, resource: PromptResource) -> Optional[str]:
        """Fetch a prompt from S3. Returns None if not found or on error."""
        if self.ignore_s3:
            return None
        try:
            logger().info(f"Retrieving prompt from S3 bucket: {self.bucket_name}, key: {resource.s3_bucket_key} ...")
            s3_client = create_s3_client()
            response = s3_client.get_object(
                Bucket=self.bucket_name,
                Key=resource.s3_bucket_key
            )
            return response['Body'].read().decode('utf-8')
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'NoSuchKey':
                # The object does not exist
                return None
            logger().error(f"S3 error for prompt '{resource.prompt_id}' from bucket '{self.bucket_name}'.", e)
            return None
        except Exception as e:
            logger().error(f"Error fetching prompt '{resource.prompt_id}' from bucket '{self.bucket_name}'.", e)
            return None

    def _fetch_from_local(self, resource: PromptResource) -> Optional[str]:
        """Fetch a prompt from the local file system. Returns None if not found or on error."""
        try:
            file_path = os.path.abspath(resource.relative_file_path)
            if not os.path.exists(file_path):
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger().error(f"Error fetching prompt '{resource.prompt_id}' from local file", e)
            return None

    def _store_to_s3(self, resource: PromptResource, prompt_text: str) -> bool:
        """Store a prompt to S3. Returns True if successful, False otherwise.
           Only uploads if the local file is newer than the S3 version."""
        if self.ignore_s3:
            return False
        try:
            s3_client = create_s3_client()

            try:
                # Check if file exists in S3 and get its last modified timestamp
                s3_object = s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=resource.s3_bucket_key
                )
                s3_last_modified = s3_object.get('LastModified')

                # Get local file's last modified time
                local_file_path = os.path.abspath(resource.relative_file_path)
                local_last_modified = datetime.fromtimestamp(
                    os.path.getmtime(local_file_path),
                    tz=timezone.utc
                )

                # Only upload if local file is newer than S3 version
                if s3_last_modified and local_last_modified <= s3_last_modified:
                    logger().trace(f"Skipping upload for '{resource.prompt_id}' as S3 version is newer.")
                    return True

            except ClientError as e:
                # If the object doesn't exist in S3, we should upload it
                if e.response.get('Error', {}).get('Code') != 'NotFound' and e.response.get('Error', {}).get('Code') != '404':
                    raise

            # Upload the file to S3
            s3_client.put_object(
                Bucket=self.bucket_name,
                Key=resource.s3_bucket_key,
                Body=prompt_text.encode('utf-8'),
                ContentType='text/plain'
            )
            logger().info(f"Stored prompt '{resource.prompt_id}' to S3 bucket '{self.bucket_name}'.")
            return True
        except Exception as e:
            logger().error(f"Error storing prompt '{resource.prompt_id}' to S3", e)
            return False

    def _store_to_local(self, resource: PromptResource, prompt_text: str) -> bool:
        """Store a prompt to the local file system. Returns True if successful, False otherwise."""
        try:
            file_path = os.path.abspath(resource.relative_file_path)

            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(prompt_text)
            logger().debug(f"Stored prompt '{resource.prompt_id}' to local '{file_path}'.")
            return True
        except Exception as e:
            logger().error(f"Error storing prompt '{resource.prompt_id}' to local file", e)
            return False
