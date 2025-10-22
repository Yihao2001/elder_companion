import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request

from moduel_1.module1 import NaturalLanguageToJSONPipeline
from module_2.router_graph import RouterGraph
from module_2.states import FlowRequest, FlowResponse
from module_3.session_context import SessionContext
from module_3.offline_graph import OfflineGraph
from module_3.online_graph import OnlineGraph
from module_3.states import FinalResponseOut
from module_3.utils.logger import logger
from rag_backend.services import Services


ELDERLY_ID = "87654321-4321-4321-4321-019876543210"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL not set; graphs may fail to connect")

    logger.info("Initializing Module 1: NaturalLanguageToJSONPipeline…")
    pipeline = NaturalLanguageToJSONPipeline()

    logger.info("Initializing Module 2: RouterGraph…")
    # If RouterGraph.invoke is @classmethod, you may not need an instance.
    router = RouterGraph()

    logger.info("Initializing Module 3: Creating SessionContext…")
    session_ctx = SessionContext(elderly_id=ELDERLY_ID, db_url=db_url)

    logger.info("Initializing Module 3: Initializing OfflineGraph…")
    offline_graph = OfflineGraph(session_ctx, verbose=True)

    logger.info("Initializing Module 3:  Initializing OnlineGraph…")
    online_graph = OnlineGraph(session_ctx, verbose=True)

    app.state.services = Services(
        pipeline=pipeline,
        router=router,
        session_ctx=session_ctx,
        offline_graph=offline_graph,
        online_graph=online_graph
    )
    logger.info("Startup complete. API ready.")
    try:
        yield
    finally:
        # SHUTDOWN (close pools, clients, etc., if available)
        logger.info("Shutting down…")
        logger.info("Shutdown complete.")

app = FastAPI(title="Memory API", lifespan=lifespan)

def get_services(request: Request) -> Services:
    return request.app.state.services

@app.post("/invoke", response_model=FinalResponseOut)
def invoke_flow(request: FlowRequest, services: Services = Depends(get_services)):
    input_data = request.model_dump()
    flow_type = input_data.get("flow_type")

    if flow_type not in ("offline", "online"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid flow_type: {flow_type}. Must be 'offline' or 'online'."
        )

    # --- Module 1: Preprocess ---
    module1_output = services.pipeline.run(input_data["text"])
    input_data["text"] = module1_output["sentences"][0]  # keep your first-sentence behavior


    # --- Module 2: Route --- 
    routing_result = (
        services.router.invoke(input_data)
    )

    flow_type = routing_result["flow_type"]
    text = routing_result["text"]
    qa = routing_result.get("qa", "")
    topic = routing_result.get("topic", [])
    if not isinstance(topic, list):
        topic = [topic] if topic else []


    # --- Module 3: RAG --- 
    payload = {
        "text": text,
        "qa": qa,
        "topic": topic,
        "module1_output": module1_output,
    }

    if flow_type == "offline":
        result = services.offline_graph.invoke(payload)
    else:
        result = services.online_graph.invoke(text)

    # --- Standardize Final Output ---
    final_response: FinalResponseOut = {
        "user_query": text,
        "final_chunks": result.get("final_chunks", []),
        "inserted": result.get("inserted", False),
    }

    return final_response