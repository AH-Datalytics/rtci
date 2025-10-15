from rtci.ai.location import LocationRetriever, LocationResolver, build_location_retriever
from tests.test_common import TestCommonAdapter


class TestLocationApi(TestCommonAdapter):

    async def test_city_location_retriever(self):
        bot: LocationRetriever = build_location_retriever()
        response = await bot.retrieve_locations_for_query(f"How many murders in New Orleans and Houston last year.")
        self.assertIsNotNone(response)
        response = await bot.retrieve_locations_for_query(f"How much crime in Texas last month?")
        self.assertIsNotNone(response)

    async def test_city_location_tool(self):
        bot: LocationResolver = LocationResolver.create()
        response = await bot.resolve_locations(f"Which state has the most crime?")
        self.assertIsNotNone(response)
        self.assertEqual(len(response), 0)
        response = await bot.resolve_locations(f"How many murders in New Orleans and Houston last year?")
        self.assertIsNotNone(response)
        self.assertEqual(len(response), 2)
        self.assertIsNotNone(response[0].matching_city_state)
        self.assertIsNotNone(response[1].matching_city_state)
        response = await bot.resolve_locations(f"How many murders in Sometown,PA?")
        self.assertIsNotNone(response)
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0].location_name, "Sometown,PA")
        self.assertIsNone(response[0].matching_city_state)
        response = await bot.resolve_locations(f"Compare crime in Illinois and Boston?")
        print(response)
        self.assertIsNotNone(response)
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0].matching_state, "MA")
        self.assertEqual(response[1].matching_state, "IL")
        response = await bot.resolve_locations(f"Which Texas city had the most murders in the past year?")
        self.assertIsNotNone(response)
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0].matching_state, "TX")
        response = await bot.resolve_locations(f"Which city in Florida has the most murders?")
        self.assertIsNotNone(response)
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0].matching_state, "FL")
