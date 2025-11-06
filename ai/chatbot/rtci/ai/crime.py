import csv
import io
from datetime import datetime
from decimal import Decimal
from typing import Self, Any

import pandas as pd
from langchain_core.documents import Document
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import BaseMessage, HumanMessage, ChatMessage
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.prompt_values import PromptValue
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePick
from pandasai import Agent
from pandasai.core.response import StringResponse, NumberResponse, DataFrameResponse, ErrorResponse, ChartResponse

from rtci.ai.location import get_location_list
from rtci.model import CrimeData, DateRange, LocationDocument, CrimeCategory, CrimeCategoryResponse, Location
from rtci.rtci import RealTimeCrime
from rtci.util.collections import convert_structured_document_to_json
from rtci.util.data import create_database, database_date_range, remove_trailing_decimals
from rtci.util.database import CrimeDatabase
from rtci.util.llm import create_llm
from rtci.util.log import logger


class CrimeCategoryResolver:

    @classmethod
    def create(cls):
        parser = PydanticOutputParser(pydantic_object=CrimeCategoryResponse)
        tool_prompt = RealTimeCrime.prompt_library.find_prompt("crime_hint")
        llm = create_llm()
        chain = (
                RunnablePick(["query", "question", "format_instructions"])
                | tool_prompt
                | llm
                | parser
        )
        return CrimeCategoryResolver(chain, parser)

    def __init__(self, chain: Runnable, parser: PydanticOutputParser):
        self.chain = chain
        self.parser = parser

    async def resolve_categories(self, query: str) -> list[CrimeCategory]:
        try:
            category_response: CrimeCategoryResponse = await self.chain.ainvoke({
                "query": query,
                "format_instructions": self.parser.get_format_instructions()
            })
            if not category_response:
                return []
            return self.__filter_categories(category_response.crime_list)
        except OutputParserException as ex:
            logger().error(f"Error parsing category response: {query}.", ex)
            return []

    def __filter_categories(self, category_list: list[CrimeCategory]):
        if not category_list:
            return []
        # flatten list to handle use case for crime types with grouped categories
        flattened_list = []
        for crime_category in category_list:
            if not crime_category.crime_name.lower() in ['crime', 'none']:
                if isinstance(crime_category.matched_category, (list, set)):
                    for item in crime_category.matched_category:
                        flattened_list.append(CrimeCategory(
                            crime_name=crime_category.crime_name,
                            matched_category=item))
                else:
                    flattened_list.append(crime_category)
        # cleanup list to remove none/na/empty categories
        for crime_category in flattened_list:
            if crime_category.matched_category is None or crime_category.matched_category.lower() in ["none", "null", "empty"]:
                crime_category.matched_category = None
        return sorted(
            flattened_list,
            key=lambda x: (x.crime_name, x.matched_category or "unknown")
        )


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


async def validate_query(query: str,
                         messages: list[BaseMessage] = None) -> str:
    conversation_context = ""
    if messages:
        # Only include the last few messages to keep the context manageable
        num_messages = 10
        recent_messages = messages[-num_messages:] if len(messages) > num_messages else messages
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                conversation_context += f"User: {msg.content}\n"
            elif isinstance(msg, ChatMessage):
                conversation_context += f"{msg.role}: {msg.content}\n"

    # create a prompt for the LLM to validate
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", RealTimeCrime.prompt_library.find_text("assistant_profile")),
        ("human", RealTimeCrime.prompt_library.find_text("assistant_validate")),
    ])
    chain = (prompt_template |
             create_llm() |
             StrOutputParser())
    return await chain.ainvoke({
        "original_query": query,
        "conversation_context": conversation_context,
        "current_date": datetime.now().strftime("%Y-%m-%d")
    })


async def summarize_query_and_conversation(query: str,
                                           messages: list[BaseMessage] = None,
                                           locations: list[Location] = None,
                                           crime_categories: list[CrimeCategory] = None,
                                           date_range: DateRange = None) -> str:
    location_context = ""
    if locations:
        location_names = [loc.page_content for loc in locations]
        location_context = "\n".join(location_names)
    if not location_context:
        location_context = "any location"

    date_context = ""
    if date_range:
        date_context = date_range.prompt_content
    if not date_context:
        all_dates = database_date_range()
        if all_dates:
            date_context = f"data available {all_dates.prompt_content}"
        else:
            date_context = "any date range"

    category_context = ""
    if crime_categories:
        categories = [cat.matched_category for cat in crime_categories if cat.matched_category]
        if categories:
            category_context = "\n".join(categories)
    if not category_context:
        category_context = "any category"

    conversation_context = ""
    if messages:
        # only include the last few messages to keep the context manageable
        num_messages = 10
        recent_messages = messages[-num_messages:] if len(messages) > num_messages else messages
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                conversation_context += f"User: {msg.content}\n"
            elif isinstance(msg, ChatMessage):
                conversation_context += f"{msg.role}: {msg.content}\n"

        # create a prompt for the LLM to summarize
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", RealTimeCrime.prompt_library.find_text("assistant_profile")),
        ("human", RealTimeCrime.prompt_library.find_text("assistant_summarize")),
    ])
    chain = (prompt_template |
             create_llm() |
             StrOutputParser())
    return await chain.ainvoke({
        "original_query": query,
        "locations": location_context,
        "date_range": date_context,
        "crime_categories": category_context,
        "conversation_context": conversation_context,
        "current_date": datetime.now().strftime("%Y-%m-%d")
    })


async def assist_query(query: str) -> str:
    # Determine available data
    database = create_database()
    date_range = database.determine_availability()

    # Create a prompt for the LLM to provide assistance
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", RealTimeCrime.prompt_library.find_text("assistant_profile")),
        ("human", RealTimeCrime.prompt_library.find_text("assistant_help")),
    ])

    # Build list of all locations
    all_locations = get_location_list()
    csv_buffer = io.StringIO()
    fieldnames = ['city_state', 'reporting_agency', 'state']
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    for location in all_locations:
        writer.writerow({
            'city_state': location.city_state,
            'reporting_agency': location.reporting_agency,
            'state': location.state
        })
    csv_string = csv_buffer.getvalue()
    csv_buffer.close()

    # Call the LLM to generate assistance
    chain = (prompt_template |
             create_llm() |
             StrOutputParser())
    return await chain.ainvoke({
        "query": query,
        "date_range_info": date_range.prompt_content if date_range else "None",
        "num_locations": len(all_locations),
        "available_locations": csv_string,
        "current_date": datetime.now().strftime("%Y-%m-%d")
    })


async def chat_query(query: str,
                     data_context: CrimeData,
                     locations: list[Location] = None,
                     crime_categories: list[CrimeCategory] = None,
                     date_range: DateRange = None) -> str:
    query_context: dict[str, Any] = {
        "query": query,
        "current_date": datetime.now().strftime("%Y-%m-%d")
    }

    crime_categories_text = "All crime categories."
    if crime_categories:
        crime_categories: list[str] = list(map(lambda x: x.matched_category, crime_categories))
        crime_categories_text = ", ".join(crime_categories)
    query_context['crime_categories'] = crime_categories_text

    # Format location information for the prompt
    location_text = "All locations."
    if locations:
        location_json = list(map(lambda x: x.prompt_content, locations))
        location_text = "\n".join(location_json)
    query_context['locations'] = location_text

    # Format date range information for the prompt
    date_text = "Any date range."
    if date_range:
        date_text = date_range.prompt_content
    query_context['date_range'] = date_text

    # Create the response using an LLM
    system_prompt: str = RealTimeCrime.prompt_library.find_text("assistant_profile")
    analyze_prompt: ChatPromptTemplate = RealTimeCrime.prompt_library.find_prompt("assistant_analyze")
    if data_context and data_context.size > 1:
        logger().trace(f"Using pandasAI agent for data analysis for query \"{query}\".")
        df = data_context.to_pandas()
        actor = Agent(dfs=df)
        actor.add_message(message=system_prompt, is_user=False)
        actor.add_message(message=analyze_prompt.format(**query_context), is_user=False)

        async def pandas_analysis(input_dict):
            if isinstance(input_dict, PromptValue):
                query_text = input_dict.to_string()
            elif isinstance(input_dict, dict):
                query_text = input_dict.get("query")
            else:
                query_text = str(input_dict)
            panda_response = actor.follow_up(query=query_text)
            if not panda_response:
                return "No response generated."
            if isinstance(panda_response, str):
                return remove_trailing_decimals(panda_response.strip())
            elif isinstance(panda_response, StringResponse):
                if panda_response.value is None:
                    return None
                return remove_trailing_decimals(str(panda_response.value))
            elif isinstance(panda_response, NumberResponse):
                if panda_response.value is None:
                    return None
                decimal_value = Decimal(panda_response.value)
                if decimal_value.is_nan() or decimal_value.is_infinite():
                    return "I do not have data to determine the answer."
                else:
                    return f"{float(panda_response.value):,.1f}".replace(".0", "")
            elif isinstance(panda_response, DataFrameResponse):
                return await format_dataframe_response(panda_response)
            elif isinstance(panda_response, ChartResponse):
                return await format_chart_response(panda_response)
            elif isinstance(panda_response, ErrorResponse):
                logger().error(f"Error response: {panda_response.value}.", panda_response.error)
                if panda_response.value:
                    return panda_response.value
                else:
                    return "An error occurred."
            logger().warning(f"Unexpected response type: {type(panda_response)}.")
            return "Unexpected response type."

        chain = (pandas_analysis |
                 StrOutputParser())
        return await chain.ainvoke(query_context)
    else:
        logger().trace(f"Using LLM for data analysis for query \"{query}\".")

        def combine_prompts(input_dict):
            return f'''
{system_prompt}
##-------------------------------------------
{analyze_prompt.format(**input_dict)}
'''

        chain = (combine_prompts |
                 create_llm() |
                 StrOutputParser())
        data_frame_text = data_context.to_csv() if data_context else None
        query_context['data_frame'] = data_frame_text
        return await chain.ainvoke(query_context)


# Convert a chart to message response format
async def format_chart_response(response: ChartResponse):
    if response.value is None:
        return None
    image_data = response.get_base64_image()
    if not image_data:
        return None
    return f"![Chart](data:image/png;base64,{image_data})"


# Convert a data frame to a Markdown table
async def format_dataframe_response(response: DataFrameResponse):
    if response.value is None:
        return None
    df = pd.DataFrame(response.value)

    # If the dataframe has 1 or fewer rows, use the LLM to summarize it as CSV
    if len(df) <= 1:
        prompt = ChatPromptTemplate.from_messages([
            ("system", RealTimeCrime.prompt_library.find_text("assistant_profile")),
            ("human", RealTimeCrime.prompt_library.find_text("assistant_csv")),
        ])
        chain = (prompt | create_llm() | StrOutputParser())
        return await chain.ainvoke({"csv_data": df.to_csv(index=False)})

    # Replace NaN values with empty strings
    df = df.fillna('')

    # Format numeric columns to 2 decimal places
    numeric_cols = df.select_dtypes(include=['float']).columns
    for col in numeric_cols:
        df[col] = df[col].apply(lambda x: f"{float(x):,.1f}".replace(".0", "") if pd.notnull(x) else '')

    # Format date columns if specified
    for col in ['date', 'datetime', 'last_modified', 'last_updated']:
        if col in df.columns:
            df[col] = df[col].dt.strftime('%B %Y')

    # Rename hard-coded columns if specified
    rename_columns = {
        'date': "Date",
        'year': "Year",
        'month': "Month",
        'reporting_agency': "Location",
        'city_state': "City/State",
        'state': "State",
        'murder': "Murders",
        'murders': "Murders",
        'rape': 'Rape',
        'robbery': "Robbery",
        'robberies': "Robbery",
        'aggravated_assault': 'Agg. Assault',
        'burglary': 'Burglary',
        'burglaries': 'Burglary',
        'theft': 'Theft',
        'thefts': 'Theft',
        'motor_vehicle_theft': 'Motor Vehicle Theft'
    }

    # Convert all column names from snake_case to Title Case With Spaces
    for col in df.columns:
        if col not in rename_columns:
            words = col.split('_')
            if words[0].lower() in ['num', 'number', 'total', 'tot']:
                words[0] = 'Num.'
            title_case = ' '.join(word.capitalize() for word in words)
            rename_columns[col] = title_case

    # Rename the columns using the coded dictionary
    df = df.rename(columns=rename_columns)

    # Convert the DataFrame to Markdown table format
    return df.to_markdown(index=False)
