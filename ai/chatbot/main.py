# main.py
import json
import pickle
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, UTC
from os import getenv
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Depends
from langchain.chains import LLMChain
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from rtci.agent.bot import build_crime_analysis_graph
from rtci.model import CrimeBotState, QueryRequest, QueryResponse, CrimeBotSession
from rtci.rtci import RealTimeCrime
from rtci.util.data import cleanup_old_files
from rtci.util.log import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # setup application core
    app_env = getenv("APP_ENV") or getenv("ENV") or getenv("RUN_MODE")
    is_dev = False
    if app_env:
        is_dev = app_env.lower() == "development" or app_env.lower() == "dev"
    RealTimeCrime.bootstrap(debug_mode=is_dev)
    cleanup_pandas_files()
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


def cleanup_pandas_files():
    cleanup_old_files(target_dir=Path('exports/charts'), hours=1)


def get_langchain_components() -> CompiledStateGraph:
    graph = build_crime_analysis_graph()
    return graph.compile()


def find_session_state(user_request: QueryRequest) -> CrimeBotState:
    if user_request.session_id:
        picked_data = RealTimeCrime.file_cache.get(key=user_request.session_id)
        if not picked_data:
            raise HTTPException(status_code=400, detail="Invalid session.")
        user_session: CrimeBotSession = pickle.loads(picked_data)
        if not user_session:
            raise HTTPException(status_code=400, detail="Invalid session.")
        logger().info(f"Session [{user_request.session_id}] loaded.")
        loaded_state: CrimeBotState = {
            "query": user_request.query,
            "locations": user_session.locations,
            "crime_categories": user_session.crime_categories,
            "date_range": user_session.date_range,
            "data_context": user_session.data_context,
            "messages": user_session.messages
        }
        return loaded_state
    else:
        # create a new session context
        user_request.session_id = uuid.uuid4().hex
        logger().info(f"New session created: {user_request.session_id}.")
        initial_state: CrimeBotState = {
            "query": user_request.query,
            "messages": []
        }
        return initial_state


async def stream_response_with_graph(graph_chain: CompiledStateGraph,
                                     user_state: CrimeBotState,
                                     session_id: str):
    # stream graph response
    last_state: dict = {}
    message_list = user_state.get("messages")
    if not message_list:
        message_list = []
    message_list.append(HumanMessage(content=user_state["query"]))
    async for mode, namespace, chunk in graph_chain.astream(user_state,
                                                            stream_mode=["messages", "updates", "custom", "values"],
                                                            subgraphs=True):
        if namespace == "values":
            if chunk:
                last_state = chunk
        elif namespace == "updates":
            for node_or_tool, data in chunk.items():
                if data:
                    if data.get("messages") and data["messages"]:
                        last_message = data["messages"][-1]
                        if isinstance(last_message, (AIMessage, HumanMessage)):
                            if not last_message in message_list:
                                message_list.append(last_message)
                                content = last_message.content if isinstance(last_message, AIMessage) else last_message
                                event = {"content": content, "type": "message", "session_id": session_id}
                                yield f"event: data\ndata: {json.dumps(event)}\n"
        elif namespace == "custom":
            if isinstance(chunk, dict):
                yield f"event: data\ndata: {json.dumps(chunk)}\n"
            else:
                event = {"message": f"{chunk}", "type": "update", "session_id": session_id}
                yield f"event: data\ndata: {json.dumps(event)}\n"
    # delete old temporary files
    cleanup_pandas_files()
    # save session context
    session_state = CrimeBotSession(
        session_id=session_id,
        locations=last_state.get("locations"),
        date_range=last_state.get("date_range"),
        crime_categories=last_state.get("crime_categories"),
        data_context=last_state.get("data_context"),
        messages=message_list
    )
    ttl_sec = 60 * 30
    RealTimeCrime.file_cache.set(key=session_id,
                                 value=pickle.dumps(session_state),
                                 ttl=ttl_sec)
    # stream end event
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
        stream_with_errors(stream_response_with_graph(graph_chain, user_state, user_request.session_id)),
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
            session_id=user_request.session_id,
            message=content,
            start_time=start_time,
            finish_time=finish_time,
            success=True
        )
    return QueryResponse(
        session_id=user_request.session_id,
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