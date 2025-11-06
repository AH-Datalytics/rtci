import csv
import io
import tempfile
from os import environ
from pathlib import Path
from typing import List, Iterable

import us
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.runnables import RunnablePick, Runnable
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from us.states import State

from rtci.model import LocationDocument, LocationResponse, Location
from rtci.rtci import RealTimeCrime
from rtci.util.collections import get_first_value
from rtci.util.csv import PydanticCSVLoader
from rtci.util.llm import create_llm
from rtci.util.log import logger
from rtci.util.s3 import create_s3_client


class LocationRecordLoader(PydanticCSVLoader[LocationDocument]):
    @classmethod
    def create(cls, file_path: Path | str):
        return LocationRecordLoader(
            model_class=LocationDocument,
            file_path=Path(file_path),
            encoding="utf-8",
            csv_args={
                "delimiter": ",",
                "quotechar": '"',
            }
        )

    def load_document(self, data: dict):
        normalized_data = {
            "id": get_first_value(data, ["id", "city_state_id"]),
            "city_state": get_first_value(data, ["city_state"]),
            "state": get_first_value(data, ["state"]),
            "reporting_agency": get_first_value(data, ["agency_name", "agency name", "reporting_agency"])
        }
        return LocationDocument(**normalized_data)


class LocationRetriever:

    @classmethod
    def create(cls, csv_path: Path | str = None):
        if csv_path is None:
            csv_path = Path(".") / "data" / "sample_cities.csv"
        loader = LocationRecordLoader.create(
            file_path=csv_path
        )
        documents = loader.load()
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"}
        )
        vector_store = FAISS.from_documents(documents, embeddings)
        return LocationRetriever(
            documents,
            vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 5,
                    "fetch_k": 25,
                    'lambda_mult': 0.25
                }
            ))

    def __init__(self, documents: list[LocationDocument], store: VectorStoreRetriever):
        self.documents = documents
        self.store = store

    async def retrieve_locations_for_query(self, query: str) -> List[LocationDocument]:
        documents: Iterable[Document] = await self.store.ainvoke(query)
        locations = []
        for doc in documents:
            location = self.__find_location_by_id(doc.metadata.get("id"))
            if location:
                locations.append(location)
        return locations

    def __find_location_by_id(self, id: str) -> LocationDocument | None:
        for doc in self.documents:
            if doc.id == id:
                return doc
        return None


_location_list: List[LocationDocument] = []
_location_retriever: LocationRetriever = None


def get_location_list() -> list[LocationDocument]:
    global _location_list
    build_location_retriever()  # ensure data is loaded
    return _location_list


def find_location_by_name(city_or_agency: str) -> LocationDocument | None:
    global _location_list
    safe_name: str = str(city_or_agency).strip().lower()
    for loc in _location_list:
        if loc.city_state.lower() == safe_name:
            return loc
        elif loc.reporting_agency.lower() == safe_name:
            return loc
    return None


def build_location_retriever() -> LocationRetriever:
    global _location_list
    global _location_retriever
    if _location_retriever:
        return _location_retriever
    # read locations from s3 file
    s3_client = create_s3_client()
    s3_bucket = environ.get("AWS_S3_BUCKET", "rtci")
    s3_key_name = environ.get("AWS_S3_LOCATIONS_KEY", "data/sample_cities.csv")
    s3_response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key_name)
    csv_content = s3_response['Body'].read().decode('utf-8')
    if not csv_content:
        raise Exception("No CSV content found in S3 object.")
    # read each location and store in list
    csv_reader = csv.reader(io.StringIO(csv_content))
    _location_list.extend(LocationDocument.read_library(csv_reader))
    # store in tempfile cvs
    temp_file = tempfile.NamedTemporaryFile(delete=True, suffix='.csv')
    temp_file_path = temp_file.name
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    logger().debug(f"Creating location retriever from S3 {s3_key_name} ...")
    ref = LocationRetriever.create(csv_path=temp_file_path)
    _location_retriever = ref
    return ref


class LocationResolver:

    @classmethod
    def create(cls):
        parser = PydanticOutputParser(pydantic_object=LocationResponse)
        hint_prompt = RealTimeCrime.prompt_library.find_prompt("location_hint")
        tool_prompt = RealTimeCrime.prompt_library.find_prompt("location_retrieve")
        llm = create_llm()
        tool_chain = create_stuff_documents_chain(
            llm=llm,
            output_parser=parser,
            prompt=tool_prompt,
            document_variable_name="locations")
        hint_chain = (
                RunnablePick(["query", "question", "format_instructions"])
                | hint_prompt
                | llm
                | StrOutputParser()
        )
        retriever = build_location_retriever()
        return LocationResolver(tool_chain, hint_chain, retriever, parser)

    def __init__(self, tool_chain: Runnable, hint_chain: Runnable, retriever: LocationRetriever, parser: PydanticOutputParser):
        self.tool_chain = tool_chain
        self.hint_chain = hint_chain
        self.retriever = retriever
        self.parser = parser

    async def resolve_locations(self, query: str) -> List[Location]:
        location_hint_list = await self.hint_chain.ainvoke({
            "query": query,
        })
        if not location_hint_list:
            return []
        location_hint_list = str(location_hint_list).strip()
        if self.__is_empty_response(location_hint_list):
            return []
        state_locations: list[Location] = []
        unknown_locations: list[str] = []
        for location_hint in location_hint_list.split("\n"):
            location_hint = location_hint.strip()
            if location_hint:
                state: State = us.states.lookup(location_hint)
                if state:
                    state_locations.append(Location(
                        location_name=location_hint,
                        matching_state=state.abbr))
                else:
                    unknown_locations.append(location_hint)
        if not unknown_locations:
            return state_locations
        location_docs: list[LocationDocument] = []
        for unknown_location in unknown_locations:
            docs = await self.retriever.retrieve_locations_for_query(unknown_location)
            if docs:
                location_docs.extend(docs)
        try:
            location_response: LocationResponse = await self.tool_chain.ainvoke({
                "query": query,
                "locations": location_docs,
                "format_instructions": self.parser.get_format_instructions()
            })
            if not location_response or not location_response.location_list:
                return self.__sort_location_documents(state_locations)
            else:
                return self.__sort_location_documents(state_locations + location_response.location_list)
        except OutputParserException as ex:
            logger().error(f"Error parsing location response: {query}.", ex)
            return []

    def __is_empty_response(self, response: str) -> bool:
        return response.lower() == "none" or response.lower() == "empty" or response == "[]"

    def __sort_location_documents(self, locations: list[Location]) -> list[Location]:
        if not locations:
            return []
        # first validate list response
        for loc in locations:
            if loc.matching_city_state and not find_location_by_name(loc.matching_city_state):
                loc.matching_city_state = None
            if loc.matching_reporting_agency and not find_location_by_name(loc.matching_reporting_agency):
                loc.matching_reporting_agency = None
        # next build a unique list of locations and sort
        unique_locations = {}
        for loc in locations:
            key = loc.label
            existing_loc = unique_locations.get(key)
            if existing_loc:
                if not existing_loc.matching_city_state:
                    unique_locations[key] = loc
            else:
                unique_locations[key] = loc
        return sorted(unique_locations.values(), key=lambda x: x.page_content)
