from datetime import datetime

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnablePick

from rtci.model import QueryRequest, DateRange
from rtci.rtci import RealTimeCrime
from rtci.util.llm import create_llm


class DateResolver:

    @classmethod
    def create(cls):
        tool_prompt = RealTimeCrime.prompt_library.find_prompt("date_hint")
        llm = create_llm()
        chain = (
                RunnablePick(["query", "question", "current_date"])
                | tool_prompt
                | llm
                | StrOutputParser()
        )
        return DateResolver(chain)

    def __init__(self, chain: Runnable):
        self.chain = chain

    async def resolve_dates(self, question: QueryRequest) -> DateRange | None:
        daterange_response = await self.chain.ainvoke({
            "query": question.query,
            "current_date": datetime.now().strftime("%Y-%m-%d")
        })
        if not daterange_response:
            return None
        if daterange_response.lower() == "none" or daterange_response.lower() == "empty":
            return None
        while "\n\n" in daterange_response:
            daterange_response = daterange_response.replace("\n\n", "\n", 1)
        parts = daterange_response.split("\n")
        if not parts or len(parts) != 2:
            return None
        start_date = datetime.strptime(parts[0].strip(), "%Y-%m-%d")
        end_date = datetime.strptime(parts[-1].strip(), "%Y-%m-%d")
        return DateRange(start_date=start_date, end_date=end_date)
