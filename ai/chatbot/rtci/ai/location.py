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
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePick, Runnable
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from us.states import State

from rtci.model import QueryRequest, LocationDocument
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
        print(documents)
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


def build_location_retriever() -> LocationRetriever:
    global _location_list
    global _location_retriever
    if _location_retriever:
        return _location_retriever
    # read locations from s3 file
    s3_client = create_s3_client()
    s3_bucket = environ.get("AWS_S3_BUCKET", "rtci")
    s3_key_name = environ.get("AWS_S3_LOCATIONS_KEY", "rtci/sample_cities.csv")
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
        hint_prompt = RealTimeCrime.prompt_library.find_prompt("location_hint")
        tool_prompt = RealTimeCrime.prompt_library.find_prompt("location_retrieve")
        llm = create_llm()
        tool_chain = create_stuff_documents_chain(
            llm=llm,
            prompt=tool_prompt,
            document_separator="\n",
            document_variable_name="locations")
        hint_chain = (
                RunnablePick(["query", "question"])
                | hint_prompt
                | llm
                | StrOutputParser()
        )
        retriever = build_location_retriever()
        return LocationResolver(tool_chain, hint_chain, retriever)

    def __init__(self, tool_chain: Runnable, hint_chain: Runnable, retriever: LocationRetriever):
        self.tool_chain = tool_chain
        self.hint_chain = hint_chain
        self.retriever = retriever

    async def resolve_locations(self, question: QueryRequest) -> List[LocationDocument]:
        location_hint_list = await self.hint_chain.ainvoke({"query": question.query})
        if not location_hint_list:
            return []
        if location_hint_list.lower() == "none" or location_hint_list.lower() == "empty":
            return []
        possible_locations: list[LocationDocument] = []
        unknown_locations: list[str] = []
        for location_hint in location_hint_list.split("\n"):
            location_hint = location_hint.strip()
            if location_hint:
                state: State = us.states.lookup(location_hint)
                if state:
                    possible_locations.append(LocationDocument(state=state.abbr))
                else:
                    unknown_locations.append(location_hint)
        if unknown_locations:
            location_docs = await self.retriever.retrieve_locations_for_query("\n".join(unknown_locations))
            city_state_list = await self.tool_chain.ainvoke({
                "query": question.query,
                "locations": location_docs
            })
            if not city_state_list:
                return possible_locations
            if city_state_list.lower() == "none" or city_state_list.lower() == "empty":
                return possible_locations
            mapped_locations = {}
            for location_doc in location_docs:
                if location_doc.id:
                    mapped_locations[location_doc.id] = location_doc
                if location_doc.city_state:
                    mapped_locations[location_doc.city_state] = location_doc
            for city_state in city_state_list.split("\n"):
                available_location = mapped_locations.get(city_state)
                if available_location:
                    possible_locations.append(available_location)
        return possible_locations
