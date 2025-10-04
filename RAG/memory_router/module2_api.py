from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from graph_flow import app
from typing import Literal

class FlowRequest(BaseModel):
    text: str
    flow_type: Literal["offline", "online"]
    qa: str = ""
    topic: str = ""

# Initialize FastAPI
api = FastAPI(title="Module 2 API")

@api.post("/invoke")
def invoke_flow(request: FlowRequest):
    """Invoke the module2 app with the provided flow parameters."""
    input_data = request.model_dump()

    # Validate flow_type
    if input_data["flow_type"] not in ("offline", "online"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid flow_type: {input_data['flow_type']}. Must be 'offline' or 'online'."
        )

    result = app.invoke(input_data)
    return {"result": result}