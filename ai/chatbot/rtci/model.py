import json
from datetime import datetime
from typing import Optional, List, Annotated, Any

import pandasai as pai
import us
from langgraph.graph import add_messages
from pydantic import BaseModel, SecretStr
from typing_extensions import TypedDict


class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime

    @property
    def prompt_content(self):
        format_start = self.start_date.strftime('%Y-%m-%d')
        format_end = self.end_date.strftime('%Y-%m-%d')
        return f"{format_start} to {format_end}"

    def __str__(self):
        return self.model_dump_json()


class LocationDocument(BaseModel):
    id: Optional[str] = None
    city_state: Optional[str] = None
    state: Optional[str] = None
    reporting_agency: Optional[str] = None

    @classmethod
    def read_library(cls, csv_reader) -> list:
        from rtci.util.collections import get_first_header_index
        header = next(csv_reader)
        column_indexes = {}
        column_indexes['id'] = get_first_header_index(header, ['id', 'city_state_id'])
        column_indexes['city_state'] = get_first_header_index(header, ['City State', 'City_State', 'Agency State', 'Agency_State'])
        column_indexes['state'] = get_first_header_index(header, ['State'])
        column_indexes['reporting_agency'] = get_first_header_index(header, ['Agency_Name', 'Agency Name'])
        list = []
        for row in csv_reader:
            list.append(LocationDocument(
                id=row[column_indexes['id']],
                city_state=row[column_indexes['city_state']],
                state=row[column_indexes['state']],
                reporting_agency=row[column_indexes['reporting_agency']]
            ))
        return list

    @property
    def label(self):
        if self.city_state:
            return self.city_state
        if self.reporting_agency:
            return self.reporting_agency
        if self.state:
            state_obj = us.states.lookup(self.state)
            return state_obj.name if state_obj else self.state
        return self.id

    @property
    def metadata(self):
        return {"id": self.id, "state": self.state}

    @property
    def page_content(self):
        return f"{self.city_state}\n{self.reporting_agency}\n{self.state}\n{us.states.lookup(self.state)}".strip()

    @property
    def prompt_content(self):
        data = self.model_dump(exclude_none=True, exclude={"id"})
        if self.city_state or self.reporting_agency:
            if data.get('state'):
                data.pop('state')
        return json.dumps(data)

    def __str__(self):
        return self.model_dump_json(exclude_none=True, exclude={"id"})


class CrimeCategory(BaseModel):
    crime: str
    category: Optional[str] = None


class CrimeData(BaseModel):
    data_frame: dict[str, list[Any]] = []

    @property
    def size(self):
        if not self.data_frame:
            return 0
        return len(self.data_frame[next(iter(self.data_frame))])

    def to_pandas(self) -> pai.DataFrame:
        return pai.DataFrame(self.data_frame)

    def to_csv(self) -> str:
        import pandas as pd
        df = pd.DataFrame(self.data_frame)
        return df.to_csv(header=True, index=False)


class CrimeBotState(TypedDict, total=False):
    """State for the crime data assistant graph."""
    # Input query from the user
    query: str
    # Extracted locations from the query
    locations: List[LocationDocument]
    # Extracted date range from the query
    date_range: Optional[DateRange]
    # Extracted crime categories the user is discussion
    crime_categories: Optional[list[CrimeCategory]]
    # Retrieved crime documents
    data_context: Optional[list[dict]]
    # Flag to indicate if data needs to be retrieved
    needs_data: Optional[bool]
    # Chat history for the conversation
    messages: Annotated[List, add_messages]


class QueryRequest(BaseModel):
    query: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500


class QueryResponse(BaseModel):
    message: str
    info: Optional[str] = None
    start_time: Optional[str | datetime] = None
    finish_time: Optional[str | datetime] = None
    success: Optional[bool] = None


class Credentials(BaseModel):
    aws_access_key_id: SecretStr
    aws_secret_access_key: SecretStr
    aws_region: str


class BotException(Exception):

    def __init__(self, detail: str, status_code: int = 500):
        self.status_code = status_code
        self.detail = detail
