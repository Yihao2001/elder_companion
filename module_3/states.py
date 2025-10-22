from __future__ import annotations
import operator
from typing import TypedDict, List, Dict, Any, Optional, Literal
from typing_extensions import Annotated

from module_3.session_context import SessionContext

# ---------- Offline Mode State ----------
AllowedTopic = Literal["healthcare", "long-term", "short-term"]

class GraphState(TypedDict):
    session: Annotated[SessionContext, lambda x, y: x or y]
    input_text: Annotated[str, lambda x, y: x or y]
    qa_type: Annotated[Literal["question", "statement"], lambda x, y: x or y]
    topics: Annotated[List[AllowedTopic], lambda x, y: x or y]
    query_embedding: Annotated[Optional[List[float]], lambda x, y: x or y]
    candidates: Annotated[List[Dict[str, Any]], operator.add]
    final_chunks: Annotated[List[Dict[str, Any]], operator.add]
    inserted: Annotated[bool, lambda x, y: x or y]


# ---------- Online Mode State ----------
class AgentState(TypedDict):
    session: Annotated[SessionContext, lambda x, y: x or y, {"persist": False}]
    messages: Annotated[list, operator.add]
    query_embedding: Annotated[Optional[List[float]], lambda x, y: x or y]
    candidates: Annotated[List[Dict[str, Any]], operator.add]
    final_chunks: Annotated[List[Dict[str, Any]], operator.add]
    inserted: Annotated[bool, lambda x, y: x or y]


# ---------- Unified Final Output ----------
class FinalResponseOut(TypedDict):
    user_query: str
    final_chunks: List[Dict[str, Any]]
    inserted: bool