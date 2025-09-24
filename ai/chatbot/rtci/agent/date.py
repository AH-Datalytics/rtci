from typing import Any

from langgraph.config import get_stream_writer

from rtci.ai.date import DateResolver
from rtci.model import CrimeBotState
from rtci.model import QueryRequest


async def extract_date_range(state: CrimeBotState) -> dict[str, Any]:
    """Extract date range from the query and add it to the state."""
    query_request = QueryRequest(query=state["query"])
    resolver = DateResolver.create()
    writer = get_stream_writer()

    last_date_range = state.get("date_range")
    extracted_date_range = await resolver.resolve_dates(query_request)
    if not extracted_date_range:
        return {}

    writer(f"Looks like you are asking about data from {extracted_date_range.strftime('%B %Y')}.")
    return {
        "date_range": extracted_date_range,
        "date_range_updated": last_date_range and (last_date_range.start_date != extracted_date_range.start_date or last_date_range.end_date != extracted_date_range.end_date)
    }
