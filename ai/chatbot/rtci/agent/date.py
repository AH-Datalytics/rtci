from typing import Any

from langgraph.config import get_stream_writer

from rtci.ai.date import DateResolver
from rtci.model import CrimeBotState
from rtci.util.data import database_date_range


async def extract_date_range(state: CrimeBotState) -> dict[str, Any]:
    """Extract date range from the query and add it to the state."""
    query = state["query"]
    resolver = DateResolver.create()
    writer = get_stream_writer()

    last_date_range = state.get("date_range")
    extracted_date_range = await resolver.resolve_dates(query)
    if not extracted_date_range and not last_date_range:
        return {}
    if not extracted_date_range:
        extracted_date_range = database_date_range()
    dates_updated = False
    if not last_date_range:
        dates_updated = True
    else:
        # compare only date components (year, month, day) ignoring time components
        start_date_changed = last_date_range.start_date.date() != extracted_date_range.start_date.date()
        end_date_changed = last_date_range.end_date.date() != extracted_date_range.end_date.date()
        dates_updated = start_date_changed or end_date_changed
    if not dates_updated:
        return {}

    writer(f"Looks like you are asking about data from {extracted_date_range.strftime('%B %Y')}.")
    return {
        "date_range": extracted_date_range,
        "date_range_updated": True
    }
