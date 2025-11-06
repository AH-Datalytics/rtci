from rtci.ai.crime import CrimeRetriever, CrimeCategoryResolver, validate_query, summarize_query_and_conversation
from rtci.model import CrimeCategory, DateRange
from tests.test_common import TestCommonAdapter


class TestCrimeApi(TestCommonAdapter):

    async def test_validate(self):
        response = await validate_query(query="How many murders in Boston, MA this past year?")
        self.assertEqual("valid", response)
        response = await validate_query(query="What locations do you have sample data for?")
        self.assertEqual("help", response)
        response = await validate_query(query="What crime types do you cover?")
        self.assertEqual("help", response)
        response = await validate_query(query="Why is Portland a warzone?")
        self.assertEqual("inappropriate", response)
        response = await validate_query(query="Why is are there crime in Democrat controlled cities?")
        self.assertEqual("political", response)
        response = await validate_query(query="How many motorcycle accidents are caused by clippings?")
        self.assertEqual("not-crime", response)
        response = await validate_query(query="How many years of crime data do you have?")
        self.assertEqual("help", response)

    async def test_summarize(self):
        original_queries = [
            "How much crime was there in New Orleans?",
            "Which city had more motor vehicle thefts between in 2024, Memphis or New Orleans?",
            "How much violent crime was there in April of 2024?",
        ]
        for query in original_queries:
            response = await summarize_query_and_conversation(query=query)
            self.assertIsNotNone(response)
            self.assertNotEqual(response, query)
        response = await summarize_query_and_conversation(query=f"How many robberies did Memphis and New Orleans have combined?")
        self.assertIsNotNone(response)
        self.assertEquals(-1, response.find(" or "))
        self.assertTrue(response.find(" and ") > 0)

    async def test_categories(self):
        bot = CrimeCategoryResolver.create()
        response = await bot.resolve_categories(f"How many murders and robberies in Boston, MA this past year?")
        self.assertIsNotNone(response)
        self.assertTrue(len(response) == 2)
        self.assertEqual('murder', response[0].matched_category)
        self.assertEqual('robbery', response[1].matched_category)
        response = await bot.resolve_categories(f"How many carjackings in New Orleans this past year?")
        self.assertIsNotNone(response)
        self.assertTrue(len(response) == 1)
        self.assertIsNone(response[0].matched_category)
        response = await bot.resolve_categories(f"How many murders were reported in Chicago in 2023?")
        self.assertIsNotNone(response)
        self.assertTrue(len(response) == 1)
        self.assertEqual('murder', response[0].matched_category)
        response = await bot.resolve_categories(f"How much violent crime in Boston last year?")
        self.assertIsNotNone(response)
        self.assertEqual(4, len(response))
        response = await bot.resolve_categories(f"How much total reported crime was there in New York City, NY and Dallas in 2024?")
        self.assertIsNotNone(response)
        self.assertEqual(0, len(response))
        response = await bot.resolve_categories(f"Summarize all crime categories for Dallas in 2019?")
        self.assertIsNotNone(response)
        self.assertEqual(0, len(response))

    async def test_retriever(self):
        bot: CrimeRetriever = CrimeRetriever.create()
        response = await bot.retrieve_crime_data(
            date_range=DateRange.create(start="2023-01-01", end="2023-12-31"),
            crime_categories=[CrimeCategory(crime_name="murder", matched_category="murder")])
        self.assertIsNotNone(response)
