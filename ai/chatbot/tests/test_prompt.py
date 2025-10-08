import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from rtci.rtci import RealTimeCrime
from rtci.util.prompt import PromptResource, PromptLibrary


class TestPromptLibrary(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for test files
        RealTimeCrime.bootstrap(debug_mode=True)
        self.test_dir = tempfile.mkdtemp()

        # Set up test resources
        self.resources = [
            PromptResource(
                prompt_id="test1",
                s3_bucket_key="test-bucket/test1.txt",
                relative_file_path=os.path.join(self.test_dir, "test1.txt")
            ),
            PromptResource(
                prompt_id="test2",
                s3_bucket_key="test-bucket/test2.txt",
                relative_file_path=os.path.join(self.test_dir, "test2.txt")
            ),
        ]

        # Create the library
        self.library = PromptLibrary(self.resources, "umbrellabits")

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)

    @patch('rtci.util.s3.create_s3_client')
    def test_get_prompt_from_s3(self, mock_create_s3_client):
        # Mock the S3 client
        mock_s3 = MagicMock()
        mock_create_s3_client.return_value = mock_s3

        # Mock S3 response
        mock_body = MagicMock()
        mock_body.read.return_value = b"Test prompt from S3"
        mock_s3.get_object.return_value = {'Body': mock_body}

        # Get the prompt
        result = self.library.find_prompt("test1")

        # Assert
        self.assertEqual(result, "Test prompt from S3")
        mock_s3.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test1.txt"
        )

    @patch('rtci.util.s3.create_s3_client')
    def test_get_prompt_s3_fallback_to_local(self, mock_create_s3_client):
        # Mock the S3 client to fail
        mock_s3 = MagicMock()
        mock_create_s3_client.return_value = mock_s3

        # S3 raises NoSuchKey error
        mock_s3.get_object.side_effect = MagicMock(
            side_effect=Exception("NoSuchKey")
        )

        # Create a local file
        with open(os.path.join(self.test_dir, "test1.txt"), 'w') as f:
            f.write("Test prompt from local file")

        # Get the prompt
        result = self.library.find_prompt("test1")

        # Assert
        self.assertEqual(result, "Test prompt from local file")

        # Check that it tried to store to S3
        mock_s3.put_object.assert_called_once()

    def test_store_prompt(self):
        # Create a mock S3 client
        with patch('rtci.util.s3.create_s3_client') as mock_create_s3_client:
            mock_s3 = MagicMock()
            mock_create_s3_client.return_value = mock_s3

            # Store a prompt
            result = self.library.store_prompt("test1", "New test prompt")

            # Assert
            self.assertTrue(result)

            # Check the local file was created
            with open(os.path.join(self.test_dir, "test1.txt"), 'r') as f:
                content = f.read()
            self.assertEqual(content, "New test prompt")

            # Check S3 was called
            mock_s3.put_object.assert_called_once()

    @patch('rtci.util.s3.create_s3_client')
    def test_push_all_to_s3(self, mock_create_s3_client):
        # Mock the S3 client
        mock_s3 = MagicMock()
        mock_create_s3_client.return_value = mock_s3

        # Create local files
        with open(os.path.join(self.test_dir, "test1.txt"), 'w') as f:
            f.write("Test prompt 1")
        with open(os.path.join(self.test_dir, "test2.txt"), 'w') as f:
            f.write("Test prompt 2")

        # Push all to S3
        results = self.library.push_prompts()

        # Assert
        self.assertEqual(results, {"test1": True, "test2": True})
        self.assertEqual(mock_s3.put_object.call_count, 2)


if __name__ == '__main__':
    unittest.main()
