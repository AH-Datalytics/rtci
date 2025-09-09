from datetime import datetime
from os import environ
from typing import Self, Dict, Any

from langchain_aws import AmazonKnowledgeBasesRetriever
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnablePick, RunnablePassthrough

from rtci.model import Credentials, QueryRequest, CrimeData, DateRange, LocationDocument
from rtci.rtci import RealTimeCrime
from rtci.util.collections import convert_structured_document_to_json
from rtci.util.credentials import create_credentials
from rtci.util.llm import create_llm


class CrimeRetriever:

    @classmethod
    def create(cls, knowledge_base_id: str = None) -> Self:
        rephrase_prompt = RealTimeCrime.prompt_library.find_prompt("crime_rephrase")
        store_prompt = RealTimeCrime.prompt_library.find_text("crime_retrieve")
        # use AWS knowledge base
        if not knowledge_base_id:
            knowledge_base_id = environ.get("AWS_KNOWLEDGE_BASE_ID")
        creds: Credentials = create_credentials()
        retriever = AmazonKnowledgeBasesRetriever(
            aws_access_key_id=creds.aws_access_key_id,
            aws_secret_access_key=creds.aws_secret_access_key,
            knowledge_base_id=knowledge_base_id,
            region_name=creds.aws_region
        )

        # use LLM to rephrase query
        llm = create_llm()
        rephrase_chain = (
                RunnablePick(["query", "location", "date_range", "current_date"])
                | rephrase_prompt
                | llm
                | StrOutputParser()
        )

        # route results to retriever store
        def format_retriever_input(output: Dict[str, Any]) -> str:
            rephrased_query = output["rephrased_query"]
            store_query = store_prompt.replace("{query}", rephrased_query)
            store_query = store_query.replace("{location}", output.get("location", "None"))
            store_query = store_query.replace("{date_range}", output.get("date_range", "None"))
            return store_query

        retrieval_chain = (
                {
                    "rephrased_query": rephrase_chain,
                    "query": lambda x: x["query"],
                    "location": lambda x: x.get("location"),
                    "date_range": lambda x: x.get("date_range"),
                }
                | RunnablePassthrough.assign(formatted_query=format_retriever_input)
                | {
                    "documents": lambda x: retriever.invoke(x["formatted_query"]),
                    "query": lambda x: x["query"]
                }
        )

        return CrimeRetriever(retrieval_chain)

    def __init__(self, retrieval_chain: Runnable):
        self.retrieval_chain = retrieval_chain

    async def retrieve_crime_data_for_query(self,
                                            question: QueryRequest,
                                            locations: list[LocationDocument] = None,
                                            date_range: DateRange = None) -> CrimeData:
        location_text: str = "Any location."
        if locations:
            location_json = list(map(lambda x: x.prompt_content, locations))
            location_text = "\n".join(location_json)
        date_range_text = date_range.prompt_content if date_range else "Any date range."
        result: dict = await self.retrieval_chain.ainvoke({
            "query": question.query,
            "location": location_text,
            "date_range": date_range_text,
            "current_date": datetime.now().strftime("%Y-%m-%d")
        })
        documents = result.get("documents") if result else None
        return self._convert_structured_documents_to_dataframe(list(documents))

    def _convert_structured_documents_to_dataframe(self, documents: list[Document]) -> CrimeData:
        converted_docs: list[dict] = []
        header_map: dict[str, str] = {}
        if documents:
            for doc in documents:
                for converted_doc in convert_structured_document_to_json(doc):
                    if converted_doc:
                        converted_docs.append(converted_doc)
                        for key in converted_doc.keys():
                            header_name = key.lower().replace(" ", "_")
                            if header_name not in header_map:
                                header_map[header_name] = key
        df_items: dict[str, list[Any]] = {}
        for header_name, header_key in header_map.items():
            df_col = []
            for doc in converted_docs:
                df_col.append(doc.get(header_key))
            df_items[header_name] = df_col
        return CrimeData(data_frame=df_items)
