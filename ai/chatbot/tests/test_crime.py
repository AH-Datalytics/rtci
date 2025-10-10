from rtci.ai.crime import CrimeRetriever, CrimeCategoryResolver, summarize_query
from rtci.model import CrimeCategory, DateRange
from tests.test_common import TestCommonAdapter


class TestCrimeApi(TestCommonAdapter):

    async def test_summarize(self):
        response = await summarize_query(query="How many murders in Boston, MA this past year?")
        self.assertIsNotNone(response)
        print(response)
        response = await summarize_query(query="What locations do you have sample data for?")
        self.assertIsNotNone(response)
        self.assertEqual("help", response)
        response = await summarize_query(query="How many years of crime data do you have?")
        self.assertIsNotNone(response)
        self.assertEqual("help", response)
        response = await summarize_query(query="What crime types do you cover?")
        self.assertIsNotNone(response)
        self.assertEqual("help", response)
        response = await summarize_query(query="Why is Portland a warzone?")
        self.assertIsNotNone(response)
        self.assertEqual("inappropriate", response)
        response = await summarize_query(query="How many motorcycle accidents are caused by clippings?")
        self.assertIsNotNone(response)
        self.assertEqual("not-crime", response)

    async def test_categories(self):
        bot = CrimeCategoryResolver.create()
        response = await bot.resolve_categories(f"How many murders and robberies in Boston, MA this past year?")
        self.assertIsNotNone(response)
        self.assertTrue(len(response) == 2)
        response = await bot.resolve_categories(f"How many carjackings in New Orleans this past year?")
        self.assertIsNotNone(response)
        self.assertTrue(len(response) == 1)
        self.assertIsNone(response[0].category)
        response = await bot.resolve_categories(f"How many jaywalkings in New Orleans this past year?")
        self.assertIsNotNone(response)
        self.assertEqual(1, len(response))
        self.assertIsNone(response[0].category)

    async def test_retriever(self):
        bot: CrimeRetriever = CrimeRetriever.create()
        response = await bot.retrieve_crime_data(
            date_range=DateRange.create(start="2023-01-01", end="2023-12-31"),
            crime_categories=[CrimeCategory(crime="murder", category="murder")])
        self.assertIsNotNone(response)
        response = await bot.retrieve_crime_data_for_query(QueryRequest(query=f"How many murders in Boston, MA this past year?"))
        self.assertIsNotNone(response)
        response = await bot.retrieve_crime_data_for_query(QueryRequest(query=f"How many murders in TX this past year?"))
        self.assertIsNotNone(response)
