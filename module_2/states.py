from typing import TypedDict, Literal, Optional, List, Dict, Any
from pydantic import BaseModel

class ClassificationState(TypedDict):
    text: str
    flow_type: Literal["online", "offline"]
    qa: Optional[str]
    topic: Optional[List[str]]  # now multi-label


class ClassificationResult(BaseModel):
    topic: List[str]
    qa: str


# Request model
class FlowRequest(BaseModel):
    text: str
    flow_type: Literal["offline", "online"]


# Response model
class FlowResponse(BaseModel):
    qa: Optional[str]
    topic: Optional[List[str]]
    module1_output: Optional[Dict[str, Any]]

