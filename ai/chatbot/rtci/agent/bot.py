from typing import Any

import pandas as pd
import pandasai as pai
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompt_values import PromptValue
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph
from pandasai import Agent
from pandasai.core.response import StringResponse, NumberResponse, DataFrameResponse, ChartResponse

from rtci.agent.crime import retrieve_crime_data, extract_crime_categories
from rtci.agent.date import extract_date_range
from rtci.agent.location import extract_locations
from rtci.model import CrimeBotState, CrimeData, LocationDocument, DateRange, CrimeCategory
from rtci.rtci import RealTimeCrime
from rtci.util.llm import create_llm, create_lite_llm
from rtci.util.log import logger


# Convert a chart to message response format
def format_chart_response(chart: ChartResponse):
    image_data = chart.get_base64_image()
    return f"![Chart](data:image/png;base64,{image_data})"


# Convert a data frame to a markdown table
def format_dataframe_response(response: DataFrameResponse):
    if response.value is None:
        return None
    df = pd.DataFrame(response.value)

    # Format date columns if specified
    for col in ['date', 'datetime', 'last_modified', 'last_updated']:
        if col in df.columns:
            df[col] = df[col].dt.strftime('%B %Y')

    # Rename columns if specified
    rename_columns = {
        'date': "Date",
        'year': "Year",
        'month': "Month",
        'reporting_agency': "Location",
        'city_state': "City/State",
        'state': "State",
        'murders': "Murders",
        'num_murders': '# Murders',
        'robbery': "Robbery",
        'num_robbery': '# Robbery',
        'robberies': "Robberies",
        'num_robberies': '# Robberies',
    }
    df = df.rename(columns=rename_columns)

    # Convert the DataFrame to Markdown table format
    return df.to_markdown(index=False)


# Update the process_query function to preserve the state
async def process_query(state: CrimeBotState) -> CrimeBotState:
    """Process the user query with retrieved documents and generate a response."""
    query = state["query"]
    locations: list[LocationDocument] = state.get("locations", [])
    crime_categories: list[CrimeCategory] = state.get("crime_categories", [])
    date_range: DateRange = state.get("date_range")
    data_context: CrimeData = state.get("data_context")
    query_context: dict[str, Any] = {"query": query}

    is_valid = (locations or date_range) and data_context
    if crime_categories:
        for crime_category in crime_categories:
            if not crime_category.category:
                is_valid = False
                break
    if not is_valid:
        new_state = state.copy()
        if "messages" not in new_state:
            new_state["messages"] = []
        new_state["messages"] = new_state["messages"] + [
            AIMessage(content="I'm sorry, I didn't understand your query. Please provide location, date range, and/or potential crime categories you're interested in.")
        ]
        return new_state
    crime_categories_text = "All crime categories."
    if crime_categories:
        crime_categories: list[str] = list(map(lambda x: x.category, crime_categories))
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
    context_prompt: ChatPromptTemplate = RealTimeCrime.prompt_library.find_prompt("assistant_context")
    analyze_prompt: ChatPromptTemplate = RealTimeCrime.prompt_library.find_prompt("assistant_analyze")
    if data_context and data_context.size > 1:
        logger().trace(f"Using pandasAI agent for data analysis for query \"{query}\".")
        df = data_context.to_pandas()
        message_list = state.get("messages", [])
        actor = Agent(dfs=df)
        actor.add_message(message=system_prompt, is_user=True)
        actor.add_message(message=context_prompt.format(**query_context), is_user=True)
        if message_list:
            for message in message_list:
                is_user = isinstance(message, HumanMessage)
                if str(message.content).find("![Chart]") < 0:
                    logger().info(f"Adding message to actor: message={message.content}, is_user={is_user}")
                    actor.add_message(message=message.content, is_user=is_user)

        def pandas_analysis(input_dict):
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
                return panda_response.strip()
            elif isinstance(panda_response, (StringResponse, NumberResponse)):
                return str(panda_response.value)
            elif isinstance(panda_response, DataFrameResponse):
                return format_dataframe_response(panda_response)
            elif isinstance(panda_response, ChartResponse):
                return format_chart_response(panda_response)
            return str(panda_response)

        chain = (pandas_analysis |
                 StrOutputParser())
        response = await chain.ainvoke(query_context)
    else:
        logger().trace(f"Using LLM for data analysis for query \"{query}\".")

        def combine_prompts(input_dict):
            return f'''
{system_prompt}
##-------------------------------------------
{context_prompt.format(**input_dict)}
##-------------------------------------------
{analyze_prompt.format(**input_dict)}
'''

        chain = (combine_prompts |
                 create_llm() |
                 StrOutputParser())
        data_frame_text = data_context.to_csv() if data_context else None
        query_context['data_frame'] = data_frame_text
        response = await chain.ainvoke(query_context)

    new_state = state.copy()
    if "messages" not in new_state:
        new_state["messages"] = []
    if response:
        new_state["messages"] = new_state["messages"] + [
            AIMessage(content=response)
        ]
    return new_state


def entry_node(state: CrimeBotState) -> CrimeBotState:
    return state


def validate_data(state: CrimeBotState) -> CrimeBotState:
    return state


def should_retrieve_crime_data(state: CrimeBotState) -> bool:
    """Check if crime data needs to be retrieved."""
    return state.get("locations_updated", False) or state.get("date_range_updated", False) or state.get("crime_categories_updated", False) or "data_context" not in state


# Define the graph with the updated functions
def build_crime_analysis_graph() -> StateGraph:
    # setup pandas AI + LLM
    llm = create_lite_llm()
    pai.config.set({
        "llm": llm,
        "verbose": False,
        "save_logs": False
    })

    # setup graph state + nodes
    graph = StateGraph(CrimeBotState)

    # Add nodes to the graph
    graph.add_node("entry_node", entry_node)
    graph.add_node("validate_data", validate_data)
    graph.add_node("process_query", process_query)
    graph.add_node("extract_locations", extract_locations)
    graph.add_node("extract_date_range", extract_date_range)
    graph.add_node("extract_crime_categories", extract_crime_categories)
    graph.add_node("retrieve_crime_data", retrieve_crime_data)
    graph.set_entry_point("entry_node")

    # Define conditional edges
    graph.add_conditional_edges("validate_data", should_retrieve_crime_data, {
        True: "retrieve_crime_data",
        False: "process_query"
    })

    # Define know return/processing edges
    graph.add_edge("entry_node", "extract_locations")
    graph.add_edge("entry_node", "extract_date_range")
    graph.add_edge("entry_node", "extract_crime_categories")
    graph.add_edge("extract_locations", "validate_data")
    graph.add_edge("extract_date_range", "validate_data")
    graph.add_edge("extract_crime_categories", "validate_data")
    graph.add_edge("retrieve_crime_data", "process_query")
    return graph


# Example usage
async def run_crime_analysis(query: str):
    """Run the crime analysis chain with the given query."""
    graph = build_crime_analysis_graph()
    chain = graph.compile()

    # Initialize the state with the query
    initial_state: CrimeBotState = {
        "query": query
    }

    # Run the chain
    result = await chain.ainvoke(initial_state)

    # Return the last message from the conversation
    if result["messages"]:
        return result["messages"][-1].content
    else:
        return "No response generated."
