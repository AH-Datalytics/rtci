from datetime import datetime
from typing import Any

from langgraph.config import get_stream_writer

from rtci.ai.date import DateResolver
from rtci.model import CrimeBotState, DateRange
from rtci.model import QueryRequest


def should_extract_date_range(state: CrimeBotState) -> bool:
    """Check if date range needs to be extracted."""
    return "date_range" not in state or not state.get("date_range")


async def extract_date_range(state: CrimeBotState) -> dict[str, Any]:
    """Extract date range from the query and add it to the state."""
    if not should_extract_date_range(state):
        return {"date_range": state["date_range"]}

    query_request = QueryRequest(query=state["query"])
    resolver = DateResolver.create()
    writer = get_stream_writer()

    date_range = await resolver.resolve_dates(query_request)
    if not date_range:
        today_date = datetime.now()
        first_of_the_year = datetime.strptime(f"{today_date.year}-01-01", "%Y-%m-%d")
        default_date_range = DateRange(start_date=first_of_the_year, end_date=today_date)
        writer("I don't see any information about what date range you are interested in.  I'll default to the the current year.")
        return {"date_range": default_date_range}
    else:
        writer(f"Looks like you are asking about data between {date_range.start_date.strftime('%Y-%m-%d')} and {date_range.end_date.strftime('%Y-%m-%d')}.")
        return {"date_range": date_range}
