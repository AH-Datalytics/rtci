from io import StringIO
from typing import List, Optional

import pandas as pd

from rtci.model import LocationDocument, DateRange, CrimeData, CrimeCategory


class CrimeDatabase:
    """
    Class for loading crime data from a CSV file into memory and
    providing functions to query the data.
    """

    def __init__(self, data_frame: pd.DataFrame = None):
        """
        Initialize the CrimeDatabase with optional data.

        Args:
            data_frame: Optional pandas DataFrame containing crime data
        """
        self._data_frame = data_frame if data_frame is not None else pd.DataFrame()

    @classmethod
    def from_csv(cls, csv_content: str) -> "CrimeDatabase":
        df = pd.read_csv(StringIO(csv_content), na_values=['NA', 'N/A', ''])
        df.columns = [col.replace(' ', '_') for col in df.columns]
        return cls(df)

    def determine_availability(self) -> Optional[DateRange]:
        filtered_df = self._data_frame.copy()
        date_series = pd.to_datetime(filtered_df['date'])
        min_date = date_series.min()
        max_date = date_series.max()
        if min_date and max_date:
            return DateRange(start_date=min_date, end_date=max_date)
        else:
            return None

    def determine_availability_by_location(self, locations: List[LocationDocument]) -> Optional[DateRange]:
        # Filter database by location
        filtered_db = self.filter_by_locations(locations)
        if filtered_db.size == 0 or 'date' not in filtered_db._data_frame.columns:
            return None

        # Ensure date column is in datetime format
        date_series = pd.to_datetime(filtered_db._data_frame['date'])
        min_date = date_series.min()
        max_date = date_series.max()
        if min_date and max_date:
            return DateRange(start_date=min_date, end_date=max_date)
        else:
            return None

    def filter_by_locations(self, locations: List[LocationDocument]) -> "CrimeDatabase":
        """
        Filter crime data by a set of LocationDocument items.

        Args:
            locations: List of LocationDocument objects

        Returns:
            New CrimeDatabase instance with filtered data
        """
        if not locations or self._data_frame.empty:
            return self

        # Create a filtered DataFrame
        filtered_df = self._data_frame.copy()
        mask = pd.Series(False, index=filtered_df.index)

        for location in locations:
            location_mask = pd.Series(False, index=filtered_df.index)

            # Filter by state if available
            if location.state:
                location_mask |= filtered_df['state'].str.lower() == location.state.lower()

            # Filter by reporting agency if available
            if location.reporting_agency:
                location_mask |= filtered_df['reporting_agency'].str.lower() == location.reporting_agency.lower()

            # Filter by city_state if available
            if location.city_state:
                location_mask |= filtered_df['city_state'].str.lower() == location.city_state.lower()

            mask |= location_mask

        return CrimeDatabase(filtered_df[mask])

    def filter_by_date_range(self, date_range: DateRange) -> "CrimeDatabase":
        """
        Filter crime data by a DateRange.

        Args:
            date_range: DateRange object with start_date and end_date

        Returns:
            New CrimeDatabase instance with filtered data
        """
        if self._data_frame.empty:
            return self

        # Convert the date column to datetime format
        filtered_df = self._data_frame.copy()
        filtered_df['date'] = pd.to_datetime(filtered_df['date'])

        # Filter by date range
        start_date = pd.to_datetime(date_range.start_date)
        end_date = pd.to_datetime(date_range.end_date)
        mask = (filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)
        return CrimeDatabase(filtered_df[mask])

    def filter_by_crime_categories(self, crime_categories: List[CrimeCategory]) -> "CrimeDatabase":
        """
        Filter crime data to include only columns that match the specified crime categories.

        This method filters the columns of the DataFrame to include only those columns that
        correspond to the crime types specified in the categories list.

        Args:
            crime_categories: List of CrimeCategory objects with crime names and optional categories

        Returns:
            New CrimeDatabase instance with filtered columns
        """
        if not crime_categories or self._data_frame.empty:
            return self

        # Create a copy of the DataFrame
        filtered_df = self._data_frame.copy()

        # Get the list of crime column names to keep
        # First, create a list of crime names in lowercase for case-insensitive matching
        crime_names = [cat.crime.lower().replace(' ', '_') for cat in crime_categories]

        # Create a list of columns to keep (always include metadata columns)
        metadata_columns = ['date', 'reporting_agency', 'state', 'region', 'agency_state', 'month', 'year']
        columns_to_keep = [col for col in filtered_df.columns
                           if col.lower() in crime_names or col in metadata_columns]

        # Filter the DataFrame to include only the specified columns
        result_df = filtered_df[columns_to_keep]

        return CrimeDatabase(result_df)

    def query(self,
              locations: Optional[List[LocationDocument]] = None,
              date_range: Optional[DateRange] = None,
              crime_categories: Optional[List[CrimeCategory]] = None) -> CrimeData:
        """
        Query the crime database with optional filters.

        Returns:
            CrimeData instance containing the query results
        """
        result_db = self

        # Apply filters if provided
        if locations:
            result_db = result_db.filter_by_locations(locations)

        if date_range:
            result_db = result_db.filter_by_date_range(date_range)

        if crime_categories:
            result_db = result_db.filter_by_crime_categories(crime_categories)

        # Convert the pandas DataFrame to a dictionary of lists
        if result_db._data_frame.empty:
            return CrimeData(data_frame={})

        # Convert DataFrame to dict with lists
        data_dict = {col: result_db._data_frame[col].tolist() for col in result_db._data_frame.columns}
        return CrimeData(data_frame=data_dict)

    @property
    def size(self) -> int:
        """
        Get the number of records in the database.

        Returns:
            Number of records
        """
        return len(self._data_frame) if not self._data_frame.empty else 0

    def to_crime_data(self) -> CrimeData:
        """
        Convert the entire database to a CrimeData instance.

        Returns:
            CrimeData instance containing all data
        """
        if self._data_frame.empty:
            return CrimeData(data_frame={})

        # Convert DataFrame to dict with lists
        data_dict = {col: self._data_frame[col].tolist() for col in self._data_frame.columns}

        return CrimeData(data_frame=data_dict)
