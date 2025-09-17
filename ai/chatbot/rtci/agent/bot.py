from typing import Iterable

import pandasai as pai
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompt_values import PromptValue
from langgraph.graph import StateGraph
from pandasai.core.response import StringResponse, NumberResponse

from rtci.agent.crime import retrieve_crime_data, extract_crime_categories
from rtci.agent.date import extract_date_range
from rtci.agent.location import extract_locations
from rtci.model import CrimeBotState, CrimeData, LocationDocument, DateRange
from rtci.rtci import RealTimeCrime
from rtci.util.llm import create_llm, create_lite_llm


# Update the process_query function to preserve the state
async def process_query(state: CrimeBotState) -> CrimeBotState:
    """Process the user query with retrieved documents and generate a response."""
    query = state["query"]
    locations: list[LocationDocument] = state.get("locations", [])
    date_range: DateRange = state.get("date_range")
    data_context: CrimeData = state.get("data_context")

    # Format location information for the prompt
    location_text = "All locations."
    if locations:
        location_json = list(map(lambda x: x.prompt_content, locations))
        location_text = "\n".join(location_json)

    # Format date range information for the prompt
    date_text = "Any date range."
    if date_range:
        date_text = date_range.prompt_content

    # Create the response using an LLM
    prompt = RealTimeCrime.prompt_library.find_prompt("assistant_analyze")
    if data_context and data_context.size > 1:
        df = data_context.to_pandas()
        llm = create_lite_llm()

        def pandas_analysis(input):
            pai.config.set({
                "llm": llm
            })
            if isinstance(input, PromptValue):
                query_text = input.to_string()
            elif isinstance(input, (list, set, Iterable)):
                query_text = "\n".join(map(lambda x: x.text, input))
            else:
                query_text = str(input)
            response = df.chat(query_text)
            if not response:
                return "No response generated."
            if isinstance(response, str):
                return response.strip()
            elif isinstance(response, (StringResponse, NumberResponse)):
                return str(response.value)
            return str(response)

        chain = (prompt |
                 pandas_analysis |
                 StrOutputParser())
        response = await chain.ainvoke({
            "context": f'''
<query>
{query}
</query>
<location>
{location_text}
</location>
<date range>
{date_text}
</date range>
            '''})
    else:
        llm = create_llm()
        chain = (prompt |
                 llm |
                 StrOutputParser())
        data_frame_text = data_context.to_csv() if data_context else None
        response = await chain.ainvoke({
            "context": f'''
<query>
{query}
</query>
<location>
{location_text}
</location>
<date range>
{date_text}
</date range>
<data frame>
{data_frame_text}
</data frame>
            '''})

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
    return state.get("needs_data", True) or "data_frame" not in state


# Define the graph with the updated functions
def build_crime_analysis_graph() -> StateGraph:
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
        "query": query,
        "messages": [],
        "locations": [],
        "date_range": None,
        "data_frame": None,
        "needs_data": True
    }

    # Run the chain
    result = await chain.ainvoke(initial_state)

    # Return the last message from the conversation
    if result["messages"]:
        return result["messages"][-1].content
    else:
        return "No response generated."
