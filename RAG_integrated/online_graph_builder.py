from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional, Literal
from typing_extensions import Annotated
import operator
import logging
import ast
import json

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import Command
from langchain_core.tools import tool, InjectedToolCallId
from typing_extensions import Annotated

from session_context import SessionContext
from rag_functions import (
    retrieve_hybrid_stm,
    retrieve_hybrid_hcm,
    retrieve_hybrid_ltm,
    rerank_with_mmr_and_recency,
    insert_short_term,
)

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- State ----------
class AgentState(TypedDict):
    session: Annotated[SessionContext, lambda x, y: x or y, {"persist": False}]
    messages: Annotated[list, operator.add]
    query_embedding: Annotated[Optional[List[float]], lambda x, y: x or y]
    candidates: Annotated[List[Dict[str, Any]], operator.add]
    final_chunks: Annotated[List[Dict[str, Any]], operator.add]
    inserted: Annotated[bool, lambda x, y: x or y]


# ---------- Nodes (embedding & reranker are stateless) ----------
def embedding_node(state: AgentState) -> Dict[str, Any]:
    session = state["session"]
    last_msg = state["messages"][-1]
    if not isinstance(last_msg, HumanMessage):
        raise ValueError("Expected a human message as input.")
    text = last_msg.content

    if session.embedder is None:
        raise ValueError("Embedder not provided in SessionContext.")
    embedding = session.embedder.embed(text)
    logger.info("Computed embedding of size %d.", len(embedding))
    return {"query_embedding": embedding}



def reranker_node(state: AgentState) -> Dict[str, Any]:
    session = state["session"]
    query = next((m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), "")
    candidates = state.get("candidates", [])
    logger.info("Reranking %d candidates...", len(candidates))
    chunks = rerank_with_mmr_and_recency(
        query=query, candidates=candidates, cross_encoder=session.cross_encoder
    )
    logger.info("Reranked to %d final chunks.", len(chunks))
    return {"final_chunks": chunks}



# ---------- Tool factory (captures session; reads embedding from session.current_embedding) ----------
def make_tools(session: SessionContext):
    @tool("retrieve_healthcare", description="Retrieve health-care data (conditions, meds, allergies, appointments)")
    def retrieve_healthcare(query: str,tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
        logger.info("Tool called: retrieve_healthcare")
        embedding = getattr(session, "current_embedding", None)
        result = retrieve_hybrid_hcm(
            conn=session.conn,
            elderly_id=session.elderly_id,
            query=query,
            embedder=session.embedder,
            embedding=embedding,
        )
        logger.info("Tool succeeded: retrieve_healthcare")
        return Command(
            update={
                # This is what populates your state key using the reducer
                "candidates": result,
                # Optional: emit a ToolMessage for the chat transcript
                "messages": [
                    ToolMessage(tool_call_id=tool_call_id, content=f"retrieve_healthcare: {len(result)} hits")
                ],
            }
        )

    @tool("retrieve_long_term", description="Retrieve long-term profile facts (stable traits, preferences, demographics)")
    def retrieve_long_term(query: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
        logger.info("Tool called: retrieve_long_term")
        embedding = getattr(session, "current_embedding", None)
        result = retrieve_hybrid_ltm(
            conn=session.conn,
            elderly_id=session.elderly_id,
            query=query,
            embedder=session.embedder,
            embedding=embedding,
        )
        logger.info("Tool succeeded: retrieve_long_term")
        return Command(
            update={
                "candidates": result,
                "messages": [
                    ToolMessage(tool_call_id=tool_call_id, content=f"retrieve_long_term: {len(result)} hits")
                ],
            }
        )

    @tool("retrieve_short_term", description="Retrieve past conversational details (recent plans, reminders, temporary preferences)")
    def retrieve_short_term(query: str, tool_call_id: Annotated[str, InjectedToolCallId],) -> Command:
        logger.info("Tool called: retrieve_short_term")
        embedding = getattr(session, "current_embedding", None)
        result = retrieve_hybrid_stm(
            conn=session.conn,
            elderly_id=session.elderly_id,
            query=query,
            embedder=session.embedder,
            embedding=embedding,
        )
        logger.info("Tool succeeded: retrieve_short_term")
        return Command(
            update={
                "candidates": result,
                "messages": [
                    ToolMessage(tool_call_id=tool_call_id, content=f"retrieve_short_term: {len(result)} hits")
                ],
            }
        )

    @tool("insert_statement", description="Insert general conversational details (recent plans, reminders, temporary preferences)")
    def insert_statement(content: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
        logger.info("Tool called: insert_statement")
        embedding = getattr(session, "current_embedding", None)
        result = insert_short_term(
            conn=session.conn,
            content=content,
            elderly_id=session.elderly_id,
            embedder=session.embedder,
            embedding=embedding,
        )
        logger.info("Tool succeeded: insert_statement")
        # This tool doesn’t contribute to candidates; only add a transcript message
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        tool_call_id=tool_call_id,
                        content=f"insert_statement: {json.dumps(result)[:200]}"
                    )
                ]
            }
        )

    return [retrieve_healthcare, retrieve_long_term, retrieve_short_term, insert_statement]



# ---------- Build Graph (tools optional so viz works) ----------
def build_graph(tools: Optional[List] = None) -> StateGraph:
    if tools is None:
        @tool
        def noop_tool(text: str) -> str:
            """No-op tool for visualization."""
            return text
        tools = [noop_tool]

    graph = StateGraph(AgentState)

    def agent_node(state: AgentState) -> Dict[str, Any]:
        session = state["session"]
        llm = session.llm_online.bind_tools(tools)
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    graph.add_node("embedding", embedding_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("rerank", reranker_node)

    graph.add_edge(START, "embedding")
    graph.add_edge("embedding", "agent")
    graph.add_edge("agent", "tools")
    graph.add_edge("tools", "rerank")
    graph.add_edge("rerank", END)

    return graph



# ---------- Public Interface ----------
def build_online_graph(session: SessionContext):
    """Factory to create a compiled agent app with session bound."""
    tools = make_tools(session)  # session captured via closure
    graph = build_graph(tools)
    app = graph.compile()

    original_invoke = app.invoke

    def wrapped_invoke(input_state: Dict[str, Any]):
        # Compute per-query embedding once and stash on the session
        human_input = input_state["messages"][-1].content
        session.current_embedding = session.embedder.embed(human_input)
        # embedding_node still computes & returns query_embedding for downstream consumers
        return original_invoke(input_state)

    app.invoke = wrapped_invoke
    return app



# ---------- Visualization ----------
def save_mermaid_graph(as_png: bool = True):
    """Save the agent graph as a PNG using Mermaid."""
    # Build graph with a harmless noop tool so this works without a SessionContext
    graph = build_graph()  # tools defaulted inside
    compiled_graph = graph.compile()

    try:
        png_bytes = compiled_graph.get_graph().draw_mermaid_png()
        with open("agent_graph.png", "wb") as f:
            f.write(png_bytes)
        print("🖼️ Saved: agent_graph.png")
    except Exception as e:
        print(f"⚠️ Could not save agent_graph.png: {e}")
        print("Ensure `graphviz` is installed: `pip install graphviz` and system Graphviz is available.")

if __name__ == "__main__":
    # Example: build and visualize
    print("Building agent graph...")
    save_mermaid_graph(as_png=True)
    print("Graph visualization saved.")
