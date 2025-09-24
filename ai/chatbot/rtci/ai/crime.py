import json
from typing import Self, Any

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnablePick

from rtci.model import QueryRequest, CrimeData, DateRange, LocationDocument, CrimeCategory, BotException
from rtci.rtci import RealTimeCrime
from rtci.util.collections import convert_structured_document_to_json
from rtci.util.data import create_database
from rtci.util.database import CrimeDatabase
from rtci.util.llm import create_llm


class CrimeCategoryResolver:

    @classmethod
    def create(cls):
        tool_prompt = RealTimeCrime.prompt_library.find_prompt("crime_hint")
        llm = create_llm()
        chain = (
                RunnablePick(["query", "question"])
                | tool_prompt
                | llm
                | StrOutputParser()
        )
        return CrimeCategoryResolver(chain)

    def __init__(self, chain: Runnable):
        self.chain = chain

    async def resolve_categories(self, question: QueryRequest) -> list[CrimeCategory]:
        category_response = await self.chain.ainvoke({
            "query": question.query
        })
        if not category_response:
            return []
        if category_response.lower() == "none" or category_response.lower() == "empty" or category_response.lower() == "null":
            return []
        while "\n\n" in category_response:
            category_response = category_response.replace("\n\n", "\n", 1)
        if category_response.startswith("["):
            category_list = []
            for item in json.loads(category_response):
                if item:
                    category_list.append(CrimeCategory.model_validate(item))
            return self.__filter_categories(category_list)
        elif category_response.startswith("{"):
            single_category = CrimeCategory.model_validate_json(category_response)
            return self.__filter_categories([single_category])
        else:
            raise BotException(f"Unable to parse category response: {category_response}.")

    def __filter_categories(self, category_list: list[CrimeCategory]):
        if not category_list:
            return []
        for crime_category in category_list:
            if crime_category.category is None or crime_category.category.lower() in ["none", "null", "empty"]:
                crime_category.category = None
        return list(category_list)


class CrimeRetriever:

    @classmethod
    def create(cls, knowledge_base_id: str = None) -> Self:
        database = create_database()
        return CrimeRetriever(database)

    def __init__(self, database: CrimeDatabase):
        self.database = database

    async def retrieve_crime_data(self,
                                  locations: list[LocationDocument] = None,
                                  crime_categories: list[CrimeCategory] = None,
                                  date_range: DateRange = None) -> CrimeData:
        return self.database.query(locations=locations,
                                   date_range=date_range,
                                   crime_categories=crime_categories)

    def _convert_structured_documents_to_dataframe(self,
                                                   documents: list[Document],
                                                   date_range: DateRange) -> CrimeData:
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
        if not df_items.get("date"):
            num_rows = len(df_items[next(iter(df_items))])
            if num_rows > 0:
                start_row_list = []
                end_row_list = []
                for i in range(num_rows):
                    start_row_list.append(date_range.start_date.strftime("%Y-%m-%d"))
                    end_row_list.append(date_range.end_date.strftime("%Y-%m-%d"))
                df_items["start_date"] = start_row_list
                df_items["end_date"] = end_row_list
        return CrimeData(data_frame=df_items)
