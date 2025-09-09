from rtci.ai.location import LocationRetriever, LocationResolver
from rtci.model import QueryRequest
from tests.test_common import TestCommonAdapter


class TestLocationApi(TestCommonAdapter):

    async def test_city_location_retriever(self):
        bot: LocationRetriever = LocationRetriever.create()
        response = await bot.retrieve_locations_for_query(f"How many murders in New Orleans and Houston last year.")
        self.assertIsNotNone(response)
        response = await bot.retrieve_locations_for_query(f"How much crime in Texas last month?")
        self.assertIsNotNone(response)

    async def test_city_location_tool(self):
        bot: LocationResolver = LocationResolver.create()
        response = await bot.resolve_locations(QueryRequest(query=f"How many murders in New Orleans and Houston last year?"))
        self.assertIsNotNone(response)
        self.assertEqual(len(response), 2)
        response = await bot.resolve_locations(QueryRequest(query=f"How many murders in Fancy Bob Town?"))
        self.assertIsNotNone(response)
        self.assertEqual(len(response), 0)
        response = await bot.resolve_locations(QueryRequest(query=f"Which Texas city had the most murders in the past year?"))
        self.assertIsNotNone(response)
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0].state, "TX")
