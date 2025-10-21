import operator
import logging

from langgraph.prebuilt import ToolExecutor
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage
from langchain_core.pydantic_v1 import BaseModel, Field

from typing import List, Dict, Any, Optional, TypedDict
from typing_extensions import Annotated

from session_context import SessionContext
from rag_functions import retrieve_rerank, insert_short_term

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic Schemas for Tools (LLM Interface) ---
class RetrieveLongTerm(BaseModel):
    """Searches long-term memory for stable profile info like name, preferences, family, or life memories."""
    query: str = Field(description="The specific question or topic to search for in long-term memory.")


class RetrieveHealth(BaseModel):
    """Searches healthcare records for medical info like allergies, medications, conditions, or appointments."""
    query: str = Field(description="The specific question or topic to search for in healthcare records.")


class RetrieveShortTerm(BaseModel):
    """Searches short-term memory for recent plans, reminders, or temporary information from the last few days."""
    query: str = Field(description="The specific question or topic to search for in short-term memory.")


class InsertShortTerm(BaseModel):
    """Stores new, general, or miscellaneous information shared by the user into short-term memory."""
    content: str = Field(description="The factual information to be stored. Should be a clear, concise statement.")



class GraphState(TypedDict):
    session: Annotated[SessionContext, lambda x, y: x or y]
    input_text: Annotated[str, lambda x, y: x or y]
    query_embedding: Annotated[Optional[List[float]], lambda x, y: x or y]
    candidates: Annotated[List[Dict[str, Any]], operator.add]
    tool_outputs: Annotated[List[dict], operator.add]
    final_chunks: Annotated[List[Dict[str, Any]], operator.add]
    inserted: Annotated[bool, lambda x, y: x or y]


