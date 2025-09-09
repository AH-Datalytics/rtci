from rtci.ai.date import DateResolver, DateRange
from rtci.model import QueryRequest
from tests.test_common import TestCommonAdapter


class TestDateApi(TestCommonAdapter):

    async def test_city_location_retriever(self):
        bot: DateResolver = DateResolver.create()
        response:DateRange = await bot.resolve_dates(QueryRequest(query=f"How many murders in New Orleans and Houston in the past year?"))
        self.assertIsNotNone(response)
        response = await bot.resolve_dates(QueryRequest(query=f"How many murders in Kansas City?"))
        self.assertIsNone(response)
        response = await bot.resolve_dates(QueryRequest(query=f"Compare the murders in New Orleans and Houston."))
        self.assertIsNone(response)