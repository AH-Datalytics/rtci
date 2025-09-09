from pathlib import Path
from typing import TypeVar, Generic, List, Type, Dict, Any, Optional

from langchain_community.document_loaders import CSVLoader
from langchain_core.documents import Document
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class PydanticCSVLoader(Generic[T]):
    """
    A generic CSV loader that converts CSV data into Pydantic model instances.

    Type parameter T must be a Pydantic BaseModel subclass.
    """

    def __init__(
            self,
            model_class: Type[T],
            file_path: Path,
            encoding: str = "utf-8",
            csv_args: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the loader with a Pydantic model class and CSV file path.
        
        Args:
            model_class: The Pydantic model class to convert rows into
            file_path: Path to the CSV file
            encoding: Character encoding of the CSV file
            csv_args: Arguments to pass to the CSV reader
        """
        self.model_class = model_class
        self.file_path = file_path
        self.encoding = encoding
        self.csv_args = csv_args or {
            "delimiter": ",",
            "quotechar": '"',
        }

        # Initialize the LangChain CSVLoader
        self.loader = CSVLoader(
            file_path=str(file_path),
            encoding=encoding,
            csv_args=self.csv_args
        )

    def load(self) -> List[T]:
        documents = self.loader.load()
        models = []
        for doc in documents:
            model_instance = self.__process_document(doc)
            if model_instance:
                models.append(model_instance)
        return models

    def __process_document(self, doc: Document):
        if doc.page_content:
            content_lines = doc.page_content.strip().split('\n')
            parsed_data = {}
            for line in content_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    parsed_data[key.strip().lower()] = value.strip()
            if parsed_data:
                model_instance = self.load_document(parsed_data)
                if model_instance:
                    return model_instance
        if doc.metadata:
            model_instance = self.model_class(**doc.metadata)
            if model_instance:
                return model_instance
        return None

    def load_document(self, data: dict):
        return self.model_class(data)
