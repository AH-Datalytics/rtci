from typing import Any

from langgraph.config import get_stream_writer

from rtci.ai.crime import CrimeRetriever, CrimeCategoryResolver
from rtci.model import CrimeBotState, QueryRequest, CrimeData, CrimeCategory
from rtci.util.log import logger


async def extract_crime_categories(state: CrimeBotState) -> dict[str, Any]:
    """Extract any crime categories context and add it to the state."""

    query_request = QueryRequest(query=state["query"])
    resolver = CrimeCategoryResolver.create()
    writer = get_stream_writer()

    crime_categories: list[CrimeCategory] = await resolver.resolve_categories(query_request)
    if not crime_categories:
        return {}
    valid_categories: list[str] = list(filter(lambda x: x, map(lambda x: x.category, crime_categories)))
    unknown_categories: list[str] = list(map(lambda x: x.crime, filter(lambda x: x.category is None, crime_categories)))
    category_hint: str = ", ".join(valid_categories)
    writer(f"Looks like you are asking about reporting on {category_hint}.")
    if unknown_categories:
        writer(f"I don't know about {', '.join(unknown_categories)}.")
    return {"crime_categories": crime_categories}


async def retrieve_crime_data(state: CrimeBotState) -> CrimeBotState:
    """Retrieve crime data based on locations and date range."""
    query_request = QueryRequest(query=state["query"])
    retriever = CrimeRetriever.create()
    writer = get_stream_writer()

    try:
        writer("Querying relevant crime statistics ...")
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
