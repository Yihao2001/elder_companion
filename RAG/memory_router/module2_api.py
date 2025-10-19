from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from graph_flow import app as compiled_graph 
from typing import Literal, List, Optional

# Request model
class FlowRequest(BaseModel):
    text: str
    flow_type: Literal["offline", "online"]
    qa: Optional[str] = None
    topic: Optional[List[str]] = None

# Response model
class FlowResponse(BaseModel):
    qa: Optional[str]
    topic: Optional[List[str]]

# Initialize FastAPI
app = FastAPI(title="Module 2 API")

@app.post("/invoke", response_model=FlowResponse)
def invoke_flow(request: FlowRequest):
    """Invoke the compiled LangGraph workflow safely via FastAPI."""
    
    input_data = request.model_dump()

    # Validate flow_type
    if input_data["flow_type"] not in ("offline", "online"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid flow_type: {input_data['flow_type']}. Must be 'offline' or 'online'."
        )

    result = compiled_graph.invoke(input_data)

    # Ensure topic is always a list
    if not isinstance(result.get("topic"), list):
        result["topic"] = [result["topic"]] if result.get("topic") else []

    return {"qa": result.get("qa"), "topic": result.get("topic")}
