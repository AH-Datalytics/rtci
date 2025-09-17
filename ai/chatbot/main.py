# main.py
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, UTC
from os import getenv
from time import sleep
from typing import AsyncGenerator

from fastapi import FastAPI, Depends
from langchain.chains import LLMChain
from langchain_core.messages import AIMessage
from langgraph.graph.state import CompiledStateGraph
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from rtci.agent.bot import build_crime_analysis_graph
from rtci.model import CrimeBotState, QueryRequest, QueryResponse
from rtci.rtci import RealTimeCrime
from rtci.util.log import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # setup application core
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    app_env = getenv("APP_ENV") or getenv("ENV") or getenv("RUN_MODE")
    is_dev = False
    if app_env:
        is_dev = app_env.lower() == "development" or app_env.lower() == "dev"
    RealTimeCrime.bootstrap(debug_mode=is_dev)
    # run application server
    yield
    # cleanup application core
    RealTimeCrime.shutdown()


app = FastAPI(
    lifespan=lifespan,
    title="AH Datalytics ChatBot Service",
    description="A chat-bot API for AH Datalytics Real Time Crime Index (RTCI) repository.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


def get_langchain_components() -> CompiledStateGraph:
    graph = build_crime_analysis_graph()
    return graph.compile()


def find_session_state(user_request: QueryRequest) -> CrimeBotState:
    initial_state: CrimeBotState = {
        "query": user_request.query,
        "locations": [],
        "date_range": None,
        "data_frame": None,
        "messages": []
    }
    return initial_state


async def stream_response_with_graph(graph_chain: CompiledStateGraph, user_state: CrimeBotState):
    async for mode, namespace, chunk in graph_chain.astream(user_state,
                                                            stream_mode=["messages", "updates", "custom"],
                                                            subgraphs=True):
        if namespace == "updates":
            for node_or_tool, data in chunk.items():
                if data:
                    if data.get("messages") and data["messages"]:
                        last_message = data["messages"][-1]
                        content = last_message.content if isinstance(last_message, AIMessage) else last_message
                        event = {"content": content}
                        yield f"event: data\ndata: {json.dumps(event)}\n"
        elif namespace == "custom":
            if isinstance(chunk, dict):
                yield f"event: data\ndata: {json.dumps(chunk)}\n"
            else:
                event = {"message": f"*{chunk}*"}
                yield f"event: data\ndata: {json.dumps(event)}\n"
    sleep(1)
    yield f"event: end\n\n"


async def stream_with_errors(generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    try:
        async for chunk in generator:
            yield chunk
    except Exception as ex:
        logger().error(f"An error occurred during streaming.", ex)
        event = {"message": "An error occurred and our developers were notified."}
        yield f"event: error\ndata: {json.dumps(event)}\n"


@app.post("/stream")
async def stream_chatbot_response(user_request: QueryRequest,
                                  graph_chain=Depends(get_langchain_components)):
    user_state = find_session_state(user_request)
    user_state['query'] = user_request.query
    return StreamingResponse(
        stream_with_errors(stream_response_with_graph(graph_chain, user_state)),
        media_type="text/event-stream"
    )


@app.post("/generate", response_model=QueryResponse)
async def generate_chatbot_response(user_request: QueryRequest,
                                    graph_chain=Depends(get_langchain_components)):
    start_time = datetime.now(UTC)
    user_state = find_session_state(user_request)
    user_state['query'] = user_request.query
    result = await graph_chain.ainvoke(user_state)
    if result["messages"]:
        finish_time = datetime.now(UTC)
        message = result["messages"][-1]
        content = message.content if isinstance(message, AIMessage) else message
        return QueryResponse(
            message=content,
            start_time=start_time,
            finish_time=finish_time,
            success=True
        )
    return QueryResponse(
        start_time=start_time,
        message="No response generated.",
        success=False
    )


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "time": datetime.now(UTC).isoformat()
    }


@app.get("/")
async def root():
    return {
        "message": "Welcome to the AH Datalytics Real Time Crime Index (RTCI) chat-bot service.",
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
