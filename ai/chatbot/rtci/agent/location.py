# Update the extract_locations function to preserve the state
from typing import Any

from langgraph.config import get_stream_writer

from rtci.ai.location import LocationResolver
from rtci.model import CrimeBotState, LocationDocument, QueryRequest


def should_extract_locations(state: CrimeBotState) -> bool:
    """Check if locations need to be extracted."""
    return "locations" not in state or not state.get("locations")


async def extract_locations(state: CrimeBotState) -> dict[str, Any]:
    """Extract locations from the query and add them to the state."""
    if not should_extract_locations(state):
        return {"locations": state["locations"]}

    query_request = QueryRequest(query=state["query"])
    resolver = LocationResolver.create()
    writer = get_stream_writer()

    locations: list[LocationDocument] = await resolver.resolve_locations(query_request)
    if not locations:
        return {"locations": state["locations"]}
    first_location = locations[0]
    if len(locations) > 2:
        writer(f"Looks like you are asking about {first_location.label} and ({len(locations) - 1}) other locations.")
    if len(locations) == 2:
        second_location = locations[1]
        writer(f"Looks like you are asking about {first_location.label} and {second_location.label}.")
    else:
        writer(f"Looks like you are asking about {first_location.label}.")
    return {"locations": locations}
