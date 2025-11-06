from rtci.agent.bot import run_crime_analysis, build_crime_analysis_graph
from tests.test_common import TestCommonAdapter


class TestBotLogic(TestCommonAdapter):

    async def test_draw_graph(self):
        graph = build_crime_analysis_graph()
        png_bytes = graph.compile().get_graph().draw_mermaid_png()
        self.assertIsNotNone(png_bytes)
        graph.compile().get_graph().draw_mermaid_png(output_file_path='chatbot.png')

    async def test_simple_query(self):
        queries = [
            "How much crime was there in New Orleans?",
            "What were the murders for Boston in 2023?"
        ]
        for query in queries:
            response = await run_crime_analysis(query)
            self.assertIsNotNone(response)
            print(f"{query} => {response}")
