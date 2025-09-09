from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph

from rtci.agent.date import extract_date_range
from rtci.agent.location import extract_locations
from rtci.ai.crime import CrimeRetriever
from rtci.model import QueryRequest, CrimeBotState, CrimeData, LocationDocument, DateRange
from rtci.rtci import RealTimeCrime
from rtci.util.llm import create_llm
from rtci.util.log import logger


# Update the retrieve_crime_data function to preserve the state
async def retrieve_crime_data(state: CrimeBotState) -> CrimeBotState:
    """Retrieve crime data based on locations and date range."""
    query_request = QueryRequest(query=state["query"])
    retriever = CrimeRetriever.create()
    writer = get_stream_writer()

    writer("Querying relevant crime statistics ...")
    try:
        documents: CrimeData = await retriever.retrieve_crime_data_for_query(
            question=query_request,
            locations=state.get("locations", []),
            date_range=state.get("date_range")
        )
        new_state = state.copy()
        new_state["data_context"] = documents
        new_state["needs_data"] = False
        return new_state
    except Exception as ex:
        writer({"error": "Unable to determine a response for this query."})
        logger().warning("Unable to retrieve crime data from knowledge base.", ex)  # ValidationException
        new_state = state.copy()
        new_state["data_frame"] = None
        new_state["data_context"] = False
        return new_state


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
    llm = create_llm()
    prompt = RealTimeCrime.prompt_library.find_prompt("assistant_analyze")
    chain = prompt | llm | StrOutputParser()

    response = await chain.ainvoke({
        "query": query,
        "location_text": location_text,
        "date_text": date_text,
        "data_frame": data_context.to_csv() if data_context else None
    })

    new_state = state.copy()
    if "messages" not in new_state:
        new_state["messages"] = []
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
    graph.add_node("retrieve_crime_data", retrieve_crime_data)
    graph.set_entry_point("entry_node")

    # Define conditional edges
    graph.add_conditional_edges("validate_data", should_retrieve_crime_data, {
        True: "retrieve_crime_data",
        False: "process_query"
    })

    # Define know return/processing edges
    graph.add_edge("entry_node", "extract_locations")
    graph.add_edge("extract_locations", "extract_date_range")
    graph.add_edge("extract_date_range", "validate_data")
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
