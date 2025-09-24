from datetime import datetime

from rtci.model import LocationDocument, DateRange
from rtci.util.data import create_database
from tests.test_common import TestCommonAdapter


class TestCrimeDatabase(TestCommonAdapter):

    async def test_database_setup(self):
        database = create_database()
        self.assertIsNotNone(database)
        self.assertTrue(database.size > 0)

    async def test_database_query(self):
        database = create_database()
        data = database.query(locations=[LocationDocument(state="NY")],
                              date_range=DateRange(
                                  start_date=datetime.strptime("2023-01-01", "%Y-%m-%d"),
                                  end_date=datetime.strptime("2023-01-31", "%Y-%m-%d")
                              ))
        self.assertIsNotNone(data)
        self.assertTrue(data.size > 0)
