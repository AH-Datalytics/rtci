from rtci.ai.crime import CrimeRetriever
from rtci.model import QueryRequest
from tests.test_common import TestCommonAdapter


class TestCrimeApi(TestCommonAdapter):

    async def test_retriever(self):
        bot: CrimeRetriever = CrimeRetriever.create()
        response = await bot.retrieve_crime_data_for_query(QueryRequest(query=f"How many murders in Boston, MA this past year?"))
        self.assertIsNotNone(response)
        print(response)
        #response = await bot.retrieve_crime_data_for_query(QueryRequest(query=f"How many murders in TX this past year?"))
        #self.assertIsNotNone(response)
