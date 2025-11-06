import litellm
import pandasai as pai
from langchain.globals import set_debug
from langchain_core.messages import AIMessage, ChatMessage
from langgraph.graph import StateGraph
from pandasai.exceptions import NoCodeFoundError, InvalidOutputValueMismatch

from rtci.agent.crime import retrieve_crime_data, extract_crime_categories
from rtci.agent.date import extract_date_range
from rtci.agent.location import extract_locations
from rtci.ai.crime import chat_query, validate_query, assist_query, summarize_query_and_conversation
from rtci.model import CrimeBotState, CrimeData, DateRange, CrimeCategory, Location
from rtci.util.llm import create_lite_llm
from rtci.util.log import logger


async def process_query(state: CrimeBotState) -> CrimeBotState:
    """Process the user query with retrieved documents and generate a response."""
    query = state["query"]
    validation_state = state.get("validated_state", '')
    locations: list[Location] = state.get("locations", [])
    crime_categories: list[CrimeCategory] = state.get("crime_categories", [])
    date_range: DateRange = state.get("date_range")
    data_context: CrimeData = state.get("data_context")

    if validation_state.lower() == 'help':
        original_query = state.get("original_query", query)
        helpful_response: str = await assist_query(query=original_query)
        if helpful_response:
            return {'messages': [AIMessage(content=helpful_response, example=True)]}
    elif validation_state.lower() in ['inappropriate', 'political']:
        return {'messages': [AIMessage(content="I'm sorry, I am not able to answer that question.  I'm focused on crime data and analysis.", example=True)]}
    elif validation_state.lower() in ['not-crime', 'invalid']:
        return {'messages': [AIMessage(content="I'm sorry, I am only able to answer questions related to crime statistics which are available to me.\n\nYou may want to review the types of data available and learn about this effort at our site [RTCI](https://realtimecrimeindex.com/data/#glossary).", example=True)]}

    if crime_categories:
        for crime_category in crime_categories:
            if not crime_category.matched_category:
                return {'messages': [AIMessage(content=f"I'm sorry, I didn't have data on '{crime_category.crime_name}.'\n\nFor more information on the categories of crime data available, review our site [RTCI](https://realtimecrimeindex.com/data/#glossary)", example=True)]}

    valid_locations: list[Location] = []
    if locations:
        for location in locations:
            if location.matching_city_state or location.matching_reporting_agency or location.matching_state:
                valid_locations.append(location)
            else:
                return {'messages': [AIMessage(content=f"I'm sorry, I didn't have data reported from '{location.location_name}.'\n\nFor more information on locations we have reported data, review our site [RTCI](https://realtimecrimeindex.com/data/#glossary)", example=True)]}

    try:
        query_response = await chat_query(query=query,
                                          locations=valid_locations,
                                          crime_categories=crime_categories,
                                          date_range=date_range,
                                          data_context=data_context)
        if not query_response:
            return {}
        return {
            "messages": [AIMessage(content=query_response)]
        }
    except (InvalidOutputValueMismatch, NoCodeFoundError) as ex:
        logger().error(f"Error in pandasAI agent: {query}.", ex)
        return {
            "messages": [AIMessage(content="I was unable to process this query. Please try again or rephrase your question.")]
        }


async def validate_query_and_conversation(state: CrimeBotState) -> CrimeBotState:
    """
    Validate the query and conversation to determine if we are processing data or handling another type of request.
    """
    messages = state.get("messages")
    last_summary_query = state.get("summarized_query")
    messages_to_summarize = []
    if messages:
        messages_to_summarize.extend(messages)
    if last_summary_query:
        messages_to_summarize.append(ChatMessage(role='Assistant', content=last_summary_query))
    original_query = state.get("original_query", "")
    if not original_query:
        original_query = state.get("query", "")
    validated_state = await validate_query(query=original_query,
                                           messages=messages_to_summarize)

    return {
        "validated_state": validated_state
    }


async def summarize_and_sanitize_conversation(state: CrimeBotState) -> CrimeBotState:
    """
    Summarize the conversation context from CrimeBotState into a single comprehensive query.
    This node combines user query, locations, date range, and crime categories.
    """
    messages = state.get("messages")
    original_query = state.get("original_query", "")
    if not original_query:
        original_query = state.get("query", "")
    locations = state.get("locations", [])
    date_range = state.get("date_range")
    crime_categories = state.get("crime_categories", [])
    last_summary_query = state.get("summarized_query")
    messages_to_summarize = []
    if messages:
        messages_to_summarize.extend(messages)
    if last_summary_query:
        messages_to_summarize.append(ChatMessage(role='Assistant', content=last_summary_query))
    summarized_query = await summarize_query_and_conversation(query=original_query,
                                                              messages=messages_to_summarize,
                                                              locations=locations,
                                                              date_range=date_range,
                                                              crime_categories=crime_categories)

    return {
        "query": summarized_query,
        "summarized_query": summarized_query,
        "original_query": original_query
    }


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
    graph.add_node("validate_conversation", validate_query_and_conversation)
    graph.add_node("summarize_and_sanitize_conversation", summarize_and_sanitize_conversation)
    graph.add_node("validate_data", validate_data)
    graph.add_node("process_query", process_query)
    graph.add_node("extract_locations", extract_locations)
    graph.add_node("extract_date_range", extract_date_range)
    graph.add_node("extract_crime_categories", extract_crime_categories)
    graph.add_node("retrieve_crime_data", retrieve_crime_data)
    graph.set_entry_point("validate_conversation")

    # Define conditional edges
    graph.add_conditional_edges(
        "validate_data", should_retrieve_crime_data, {
            True: "retrieve_crime_data",
            False: "process_query"
        })
    graph.add_conditional_edges(
        "validate_conversation",
        lambda state: state.get("validated_state") in ['valid'],
        {
            True: "summarize_and_sanitize_conversation",
            False: "process_query"
        }
    )

    # Define know return/processing edges
    graph.add_edge("summarize_and_sanitize_conversation", "extract_locations")
    graph.add_edge("summarize_and_sanitize_conversation", "extract_date_range")
    graph.add_edge("summarize_and_sanitize_conversation", "extract_crime_categories")
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
