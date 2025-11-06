import json
from datetime import datetime
from typing import Optional, List, Annotated, Any

import pandasai as pai
import us
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pandasai.data_loader.semantic_layer_schema import Column, SemanticLayerSchema, Source
from pydantic import BaseModel, SecretStr, Field
from typing_extensions import TypedDict


class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime

    @staticmethod
    def create(start: datetime | str, end: datetime | str):
        start_date = start if isinstance(start, datetime) else datetime.strptime(str(start), "%Y-%m-%d")
        end_date = start if isinstance(end, datetime) else datetime.strptime(str(end), "%Y-%m-%d")
        return DateRange(start_date=start_date, end_date=end_date)

    @property
    def prompt_content(self):
        format_start = self.start_date.strftime('%Y-%m-%d')
        format_end = self.end_date.strftime('%Y-%m-%d')
        return f"{format_start} to {format_end}"

    def contains(self, other: "DateRange") -> bool:
        # Compare only date components (year, month, day) ignoring time components
        return self.start_date.date() <= other.start_date.date() and self.end_date.date() >= other.end_date.date()

    def intersects(self, other: "DateRange") -> bool:
        # Compare only date components (year, month, day) ignoring time components
        return (self.start_date.date() < other.end_date.date()) and (self.end_date.date() > other.start_date.date())

    def intersection(self, other: "DateRange") -> Optional["DateRange"]:
        if not self.intersects(other):
            return None
        start = max(self.start_date, other.start_date)
        end = min(self.end_date, other.end_date)
        return DateRange(start_date=start, end_date=end)

    def strftime(self, strftime_format: str) -> str:
        return self.start_date.strftime(strftime_format) + " through " + self.end_date.strftime(strftime_format)

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

    def to_json(self):
        return self.model_dump_json(exclude_none=True, exclude={"id"})

    def __str__(self):
        return self.to_json()


class Location(BaseModel):
    location_name: str = Field(description="The location extracted from the user query.")
    matching_city_state: Optional[str] = Field(description="The matching 'city_state' (in format of city,state), if any.", default=None)
    matching_reporting_agency: Optional[str] = Field(description="The matching 'reporting_agency' (a city, town, or area), if any.", default=None)
    matching_state: Optional[str] = Field(description="The matching state abbreviation', if any.", default=None)

    @property
    def metadata(self):
        return {}

    @property
    def label(self):
        if self.matching_city_state:
            return self.matching_city_state
        if self.matching_reporting_agency:
            return self.matching_reporting_agency
        if self.matching_state:
            state_obj = us.states.lookup(self.matching_state)
            if state_obj:
                return state_obj.name
        return self.location_name

    @property
    def page_content(self):
        return f"{self.matching_city_state}\n{self.matching_reporting_agency}\n{self.matching_state}\n{us.states.lookup(self.matching_state)}".strip()

    @property
    def prompt_content(self):
        content: dict[str, str] = {'location_name': self.location_name}
        if self.matching_city_state:
            content['city_state'] = self.matching_city_state
        if self.matching_reporting_agency:
            content['reporting_agency'] = self.matching_reporting_agency
        if self.matching_city_state:
            content['state'] = self.matching_state
        return json.dumps(content)


class LocationResponse(BaseModel):
    location_list: List[Location] = Field(description="A list of all extracted locations the query is referencing.")


class CrimeCategory(BaseModel):
    crime_name: str = Field(description="The crime or criminal offense extracted from the query.")
    matched_category: Optional[str | list[str]] = Field(description="The matching crime category, if any.", default=None)

    @property
    def label(self):
        if not self.matched_category:
            return self.crime_name
        words = str(self.matched_category).split('_')
        return ' '.join(word.capitalize() for word in words)


class CrimeCategoryResponse(BaseModel):
    crime_list: List[CrimeCategory] = Field(description="A list of all extracted crime categories the query is referencing.")


class ReportedCrimeRecord(BaseModel):
    month: int = Field(alias="Month")
    year: int = Field(alias="Year")
    date: datetime = Field(alias="Date")
    agency: str = Field(alias="Agency")
    state: str = Field(alias="State")
    region: str = Field(alias="Region")
    agency_state: str = Field(alias="Agency_State")
    murder: int = Field(alias="Murder")
    rape: int = Field(alias="Rape")
    robbery: int = Field(alias="Robbery")
    aggravated_assault: int = Field(alias="Aggravated_Assault")
    burglary: int = Field(alias="Burglary")
    theft: int = Field(alias="Theft")
    motor_vehicle_theft: int = Field(alias="Motor_Vehicle_Theft")
    violent_crime: int = Field(alias="Violent_Crime")
    property_crime: int = Field(alias="Property_Crime")

    class Config:
        populate_by_name = True


class CrimeData(BaseModel):
    data_frame: dict[str, list[Any]] = []

    @property
    def size(self):
        if not self.data_frame:
            return 0
        return len(self.data_frame[next(iter(self.data_frame))])

    def to_pandas(self) -> pai.DataFrame:
        description = "Reported Crime Data (monthly)"
        available_columns = list(self.data_frame.keys()) if self.data_frame else []
        columns: list[Column] = [
            Column(name="month", type="string", description="Month name"),
            Column(name="year", type="integer", description="Year of the crime data"),
            Column(name="date", type="datetime", description="Date of the crime record"),
            Column(name="agency", type="string", description="Reporting agency name"),
            Column(name="state", type="string", description="US state abbreviation"),
            Column(name="region", type="string", description="Geographic region"),
            Column(name="agency_state", type="string", description="Combined agency and state identifier"),
            Column(name="murder", type="integer", description="Number of murder cases reported for the month"),
            Column(name="rape", type="integer", description="Number of rape cases reported for the month"),
            Column(name="robbery", type="integer", description="Number of robbery cases reported for the month"),
            Column(name="aggravated_assault", type="integer", description="Number of aggravated assault cases reported for the month"),
            Column(name="burglary", type="integer", description="Number of burglary cases reported for the month"),
            Column(name="theft", type="integer", description="Number of theft cases reported for the month"),
            Column(name="motor_vehicle_theft", type="integer", description="Number of motor vehicle theft cases reported for the month")
        ]
        filtered_columns = [col for col in columns if col.name.lower() in [key.lower() for key in available_columns]]
        name: str = f"crime_data_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        schema: SemanticLayerSchema = SemanticLayerSchema(
            name=name,
            source=Source(type="csv", path=f"rtci/{name}"),
            description="Monthly crime statistics across different categories by location",
            columns=filtered_columns
        )
        return pai.DataFrame(data=self.data_frame, schem=schema, description=description)

    def to_csv(self) -> str:
        import pandas as pd
        df = pd.DataFrame(self.data_frame)
        return df.to_csv(header=True, index=False)


class CrimeBotSession(BaseModel):
    session_id: str
    locations: Optional[List[Location]]
    date_range: Optional[DateRange]
    crime_categories: Optional[List[CrimeCategory]]
    data_context: Optional[CrimeData]
    messages: List[BaseMessage]
    summarized_query: Optional[str]

    def to_markdown(self):
        markdown_txt = ''
        if self.date_range:
            markdown_txt += f"## Date Range\n\n- {self.date_range.prompt_content}\n\n"
        else:
            markdown_txt += "## All Dates\n\n"
        if self.locations:
            markdown_txt += "## Locations\n\n"
            for location in self.locations:
                if location.matching_city_state or location.matching_reporting_agency:
                    markdown_txt += f"- {location.label}\n"
                else:
                    markdown_txt += f"- {location.location_name} (unknown)\n"
            markdown_txt += "\n"
        else:
            markdown_txt += "## All Locations\n\n"
        if self.crime_categories:
            markdown_txt += "## Crime Categories\n\n"
            for crime in self.crime_categories:
                if crime.matched_category:
                    markdown_txt += f"- {crime.label}\n"
                else:
                    markdown_txt += f"- {crime.crime_name} (unknown)\n"
        markdown_txt += "\n"
        return markdown_txt


class CrimeBotState(TypedDict, total=False):
    """State for the crime data assistant graph."""
    # Input query from the user
    query: str
    original_query: str
    summarized_query: Optional[str]
    validated_state: str
    # Extracted locations from the query
    locations: Optional[List[Location]]
    locations_updated: Optional[bool]
    # Extracted date range from the query
    date_range: Optional[DateRange]
    date_range_updated: Optional[bool]
    # Extracted crime categories the user is discussion
    crime_categories: Optional[List[CrimeCategory]]
    crime_categories_updated: Optional[bool]
    # Retrieved crime documents
    data_context: Optional[CrimeData]
    # Chat history for the conversation
    messages: Annotated[List, add_messages]


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    message: str
    session_id: str
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
