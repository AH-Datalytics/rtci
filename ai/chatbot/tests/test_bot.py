from rtci.agent.bot import run_crime_analysis
from tests.test_common import TestCommonAdapter


class TestBotLogic(TestCommonAdapter):

    async def test_simple_query(self):
        query: str = "How many murders in New Orleans and Houston this past year?"
        response = await run_crime_analysis(query)
        self.assertIsNotNone(response)
        #query: str = "How many thefts in Texas in May 2024?"
        #await run_crime_analysis(query)
