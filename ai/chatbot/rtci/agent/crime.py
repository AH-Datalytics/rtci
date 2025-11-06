from typing import Any

import deepcompare
from langgraph.config import get_stream_writer

from rtci.ai.crime import CrimeRetriever, CrimeCategoryResolver
from rtci.model import CrimeBotState, CrimeData, CrimeCategory, DateRange
from rtci.util.data import create_database
from rtci.util.log import logger


def all_crime_categories() -> list[CrimeCategory]:
    items = [
        'murder', 'rape', 'robbery', 'aggravated_assault', 'burglary', 'theft', 'motor_vehicle_theft'
    ]
    return list(map(lambda x: CrimeCategory(crime_name=x, matched_category=x), items))


async def extract_crime_categories(state: CrimeBotState) -> dict[str, Any]:
    """Extract any crime categories context and add it to the state."""

    query = state["query"]
    resolver = CrimeCategoryResolver.create()
    writer = get_stream_writer()

    last_category_list = state.get("crime_categories", [])
    crime_categories: list[CrimeCategory] = await resolver.resolve_categories(query)
    if crime_categories is None:
        crime_categories = []
    if not crime_categories and last_category_list:
        writer(f"Expanding query to include all crime categories.")
        return {
            "crime_categories": [],
            "crime_categories_updated": True
        }
    if deepcompare.compare(last_category_list, crime_categories):
        return {}

    valid_categories: list[str] = list(map(lambda x: x.label, filter(lambda x: x.matched_category, crime_categories)))
    unknown_categories: list[str] = list(map(lambda x: x.crime_name, filter(lambda x: x.matched_category is None, crime_categories)))
    if valid_categories:
        writer(f"Looks like you are asking about reporting on {', '.join(valid_categories)}.")
    if unknown_categories:
        writer(f"I don't know about {', '.join(unknown_categories)}.")
    return {
        "crime_categories": crime_categories,
        "crime_categories_updated": True
    }


async def retrieve_crime_data(state: CrimeBotState) -> CrimeBotState:
    """Retrieve crime data based on locations and date range."""
    locations = state.get("locations", [])
    crime_categories = state.get("crime_categories", [])
    date_range: DateRange = state.get("date_range")
    database = create_database()
    retriever = CrimeRetriever(database)
    writer = get_stream_writer()

    # Bound the user date range query to available data
    if date_range is None:
        date_range = database.determine_availability()
        writer(f"I don't see any information about what date range you are interested in.  I'll default to what data I have available - {date_range.strftime('%B %Y')}.")
    else:
        available_dates = database.determine_availability_by_location(locations) if locations else database.determine_availability()
        if available_dates:
            if not available_dates.contains(date_range):
                if available_dates.intersects(date_range):
                    date_range = available_dates.intersection(date_range)
                    writer(f"I only have data for {date_range.strftime('%B %Y')} so I'll limit my response to that range.")
                else:
                    writer(f"I don't have any data for the dates you seem to be interested in.  My data is limited to {available_dates.strftime('%B %Y')}.")
                    return {}

    try:
        writer("Querying relevant crime statistics ...")
        documents: CrimeData = await retriever.retrieve_crime_data(
            locations=locations,
            date_range=date_range,
            crime_categories=crime_categories
        )
        new_state = state.copy()
        new_state["data_context"] = documents
        new_state["date_range"] = date_range
        new_state["needs_data"] = False
        return new_state
    except Exception as ex:
        writer({"error": "Unable to determine a response for this query."})
        logger().warning("Unable to retrieve crime data from knowledge base.", ex)  # ValidationException
        new_state = state.copy()
        new_state["data_context"] = None
        return new_state
