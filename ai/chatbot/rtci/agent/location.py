# Update the extract_locations function to preserve the state
from typing import Any

import deepcompare
from langgraph.config import get_stream_writer

from rtci.ai.location import LocationResolver
from rtci.model import CrimeBotState, Location


async def extract_locations(state: CrimeBotState) -> dict[str, Any]:
    """Extract locations from the query and add them to the state."""
    query = state["query"]
    resolver = LocationResolver.create()
    writer = get_stream_writer()

    last_locations = state.get("locations", [])
    current_locations: list[Location] = await resolver.resolve_locations(query)
    if current_locations is None:
        current_locations = []
    if not current_locations and last_locations:
        writer(f"Expanding query to include all locations.")
        return {
            "locations": [],
            "locations_updated": True
        }
    if deepcompare.compare(last_locations, current_locations):
        return {}
    if not current_locations:
        return {}

    first_location = current_locations[0]
    if len(current_locations) > 2:
        writer(f"Looks like you are asking about {first_location.label} and ({len(current_locations) - 1}) other locations.")
    elif len(current_locations) == 2:
        second_location = current_locations[1]
        writer(f"Looks like you are asking about {first_location.label} and {second_location.label}.")
    else:
        writer(f"Looks like you are asking about {first_location.label}.")
    return {
        "locations": current_locations,
        "locations_updated": True
    }
