# Update the extract_locations function to preserve the state
from typing import Any

import deepcompare
from langgraph.config import get_stream_writer

from rtci.ai.location import LocationResolver
from rtci.model import CrimeBotState, LocationDocument, QueryRequest


async def extract_locations(state: CrimeBotState) -> dict[str, Any]:
    """Extract locations from the query and add them to the state."""
    query_request = QueryRequest(query=state["query"])
    resolver = LocationResolver.create()
    writer = get_stream_writer()

    last_locations = state.get("locations", [])
    extracted_locations: list[LocationDocument] = await resolver.resolve_locations(query_request)
    if not extracted_locations:
        return {}

    location_map: dict[str, LocationDocument] = {}
    if last_locations:
        for location in last_locations:
            location_map[location.page_content] = location
    for location in extracted_locations:
        location_map[location.page_content] = location
    locations = list(location_map.values())
    first_location = locations[0]
    if len(locations) > 2:
        writer(f"Looks like you are asking about {first_location.label} and ({len(locations) - 1}) other locations.")
    elif len(locations) == 2:
        second_location = locations[1]
        writer(f"Looks like you are asking about {first_location.label} and {second_location.label}.")
    else:
        writer(f"Looks like you are asking about {first_location.label}.")
    return {
        "locations": locations,
        "locations_updated": not deepcompare.compare(last_locations, locations)
    }
