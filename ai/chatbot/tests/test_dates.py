from rtci.ai.date import DateResolver
from tests.test_common import TestCommonAdapter


class TestDateApi(TestCommonAdapter):

    async def test_date_range_retriever(self):
        bot: DateResolver = DateResolver.create()
        response = await bot.resolve_dates(f"Which city had the most crime in 2023?")
        self.assertIsNotNone(response)
        response = await bot.resolve_dates(f"What is the percent change in the number of murders reported in the date range 2024-01-01 to 2025-06-01?")
        self.assertIsNotNone(response)
        self.assertEqual(response.start_date.year, 2024)
        self.assertEqual(response.end_date.year, 2025)
        response = await bot.resolve_dates(f"How many murders in New Orleans and Houston in the past year?")
        self.assertIsNotNone(response)
        response = await bot.resolve_dates(f"How many violent crimes were there in April of 2024?")
        self.assertIsNotNone(response)
        self.assertEqual(response.start_date.month, 4)
        self.assertEqual(response.start_date.year, 2024)
        self.assertEqual(response.end_date.month, 4)
        self.assertEqual(response.end_date.year, 2024)
        response = await bot.resolve_dates(f"Which location had the highest number of motor vehicle thefts in 2023?")
        self.assertIsNotNone(response)
        self.assertEqual(response.start_date.year, 2023)
        response = await bot.resolve_dates(f"Compare the murders in New Orleans and Houston.")
        self.assertIsNone(response)
        response = await bot.resolve_dates(f"How many murders in Kansas City in 2022 and 2023?")
        self.assertIsNotNone(response)
        self.assertEqual(response.start_date.year, 2022)
        self.assertEqual(response.end_date.year, 2023)
        #response = await bot.resolve_dates(f"When did crime get so bad in Chicago?")
        #self.assertIsNone(response)
        response = await bot.resolve_dates(f"What is the percent change in motor vehicle theft in 2024?")
        self.assertIsNotNone(response)
        self.assertEqual(response.start_date.year, 2023)
        self.assertEqual(response.end_date.year, 2024)
