import litellm
import pandasai as pai
from langchain.globals import set_debug
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph

from rtci.agent.crime import retrieve_crime_data, extract_crime_categories
from rtci.agent.date import extract_date_range
from rtci.agent.location import extract_locations
from rtci.ai.crime import chat_query, summarize_query, assist_query
from rtci.model import CrimeBotState, CrimeData, LocationDocument, DateRange, CrimeCategory
from rtci.util.llm import create_lite_llm


# Update the process_query function to preserve the state
async def process_query(state: CrimeBotState) -> CrimeBotState:
    """Process the user query with retrieved documents and generate a response."""
    query = state["query"]
    locations: list[LocationDocument] = state.get("locations", [])
    crime_categories: list[CrimeCategory] = state.get("crime_categories", [])
    date_range: DateRange = state.get("date_range")
    data_context: CrimeData = state.get("data_context")

    if query == 'help':
        original_query = state.get("original_query", query)
        helpful_response: str = await assist_query(query=original_query)
        if helpful_response:
            return {'messages': [AIMessage(content=helpful_response, example=True)]}
    elif query == 'inappropriate':
        return {'messages': [AIMessage(content="I'm sorry, I am not able to answer that question.  I'm focused on crime data and analysis.", example=True)]}
    elif query == 'not-crime' or query == 'invalid':
        return {'messages': [AIMessage(content="I'm sorry, I am only able to answer questions related to crime statistics which are available to me.\n\nYou may want to review the types of data available and learn about this effort at our site [RTCI](https://realtimecrimeindex.com/data/#glossary).", example=True)]}

    is_valid = (locations or date_range) and data_context
    if crime_categories:
        for crime_category in crime_categories:
            if not crime_category.category:
                is_valid = False
                break
    if not is_valid:
        return {'messages': [AIMessage(content="I'm sorry, I didn't understand your query. Please provide location, date range, and/or potential crime categories you're interested in.\n\nFor more information on the categories of crime data available, review our site [RTCI](https://realtimecrimeindex.com/data/#glossary)", example=True)]}

    query_response = await chat_query(query=query, locations=locations, crime_categories=crime_categories, date_range=date_range, data_context=data_context)
    if not query_response:
        return {}
    return {
        "messages": [AIMessage(content=query_response)]
    }


async def summarize_and_sanitize_conversation(state: CrimeBotState) -> CrimeBotState:
    """
    Summarize the conversation context from CrimeBotState into a single comprehensive query.
    This node combines user query, locations, date range, and crime categories.
    """
    # Get existing information from state
    messages = state.get("messages", [])
    original_query = state.get("query", "")
    locations = state.get("locations", [])
    date_range = state.get("date_range")
    crime_categories = state.get("crime_categories", [])
    summarized_query = await summarize_query(query=original_query,
                                             messages=messages,
                                             locations=locations,
                                             date_range=date_range,
                                             crime_categories=crime_categories)

    # Update the state with the summarized query
    return {
        "query": summarized_query,
        "summarized_query": summarized_query,
        "original_query": original_query
    }


def fork_queries(state: CrimeBotState) -> CrimeBotState:
    return state


def validate_data(state: CrimeBotState) -> CrimeBotState:
    return state


def should_retrieve_crime_data(state: CrimeBotState) -> bool:
    """Check if crime data needs to be retrieved."""
    for updated_flag in ['locations_updated', 'date_range_updated', 'crime_categories_updated']:
        if state.get(updated_flag, False):
            return True
    if "data_context" not in state:
        return True
    return False


# Define the graph with the updated functions
def build_crime_analysis_graph(debug_mode: bool = False) -> StateGraph:
    # setup log level
    if debug_mode:
        set_debug(True)
        litellm._turn_on_debug()

    # setup pandas AI + LLM
    llm = create_lite_llm()
    pai.config.set({
        "llm": llm,
        "max_retries": 1,
        "verbose": debug_mode,
        "save_logs": debug_mode
    })

    # setup graph state + nodes
    graph = StateGraph(CrimeBotState)

    # Add nodes to the graph
    graph.add_node("summarize_and_sanitize_conversation", summarize_and_sanitize_conversation)
    graph.add_node("fork_queries", fork_queries)
    graph.add_node("validate_data", validate_data)
    graph.add_node("process_query", process_query)
    graph.add_node("extract_locations", extract_locations)
    graph.add_node("extract_date_range", extract_date_range)
    graph.add_node("extract_crime_categories", extract_crime_categories)
    graph.add_node("retrieve_crime_data", retrieve_crime_data)
    graph.set_entry_point("summarize_and_sanitize_conversation")

    # Define conditional edges
    graph.add_conditional_edges(
        "validate_data", should_retrieve_crime_data, {
            True: "retrieve_crime_data",
            False: "process_query"
        })
    graph.add_conditional_edges(
        "summarize_and_sanitize_conversation",
        lambda state: state.get("query") in ['help', 'inappropriate', 'not-crime', 'invalid'],
        {
            True: "process_query",
            False: "fork_queries"
        }
    )

    # Define know return/processing edges
    graph.add_edge("fork_queries", "extract_locations")
    graph.add_edge("fork_queries", "extract_date_range")
    graph.add_edge("fork_queries", "extract_crime_categories")
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
