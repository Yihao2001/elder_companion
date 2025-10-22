from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional, Literal
from typing_extensions import Annotated
import operator

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import Command
from langchain_core.tools import tool, InjectedToolCallId

from module_3.session_context import SessionContext
from module_3.utils.logger import logger 
from module_3.rag_functions import (
    retrieve_hybrid_stm,
    retrieve_hybrid_hcm,
    retrieve_hybrid_ltm,
    rerank_with_mmr_and_recency,
    insert_short_term,
)


# ---------- State ----------
class AgentState(TypedDict):
    session: Annotated[SessionContext, lambda x, y: x or y, {"persist": False}]
    messages: Annotated[list, operator.add]
    query_embedding: Annotated[Optional[List[float]], lambda x, y: x or y]
    candidates: Annotated[List[Dict[str, Any]], operator.add]
    final_chunks: Annotated[List[Dict[str, Any]], operator.add]
    inserted: Annotated[bool, lambda x, y: x or y]


# ---------- Nodes ----------
def embedding_node(state: AgentState) -> Dict[str, Any]:
    """No-op embedding node (embedding already computed in wrapped_invoke)."""
    session = state["session"]
    embedding = getattr(session, "current_embedding", None)
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


# ---------- Tool factory ----------
def make_tools(session: SessionContext):
    @tool("retrieve_healthcare", description="Retrieve health-care data (conditions, meds, allergies, appointments)")
    def retrieve_healthcare(query: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
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
                "candidates": result,
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
    def retrieve_short_term(query: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
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

        insert_short_term(
            conn=session.conn,
            content=content,
            elderly_id=session.elderly_id,
            embedder=session.embedder,
            embedding=getattr(session, "current_embedding", None),
        )

        logger.info("Tool succeeded: insert_statement")
        return Command(
            update={
                "inserted": True,
                "messages": [
                    ToolMessage(tool_call_id=tool_call_id, content="insert_statement: inserted successfully")
                ],
            }
        )

    return [retrieve_healthcare, retrieve_long_term, retrieve_short_term, insert_statement]


# ---------- Routing node ----------
def route_after_tools(state: AgentState) -> Command[Literal["rerank", END]]:
    has_retrieval = bool(state.get("candidates"))
    was_inserted = bool(state.get("inserted"))
    logger.info(f"Routing: candidates={has_retrieval}, inserted={was_inserted}")

    if has_retrieval:
        logger.info("Proceeding to rerank (retrieval present).")
        return Command(goto="rerank")
    else:
        logger.info("Skipping rerank (no retrieval).")
        # Add a ToolMessage for visibility in the transcript
        skip_msg = ToolMessage(
            tool_call_id="router",
            content="No retrieval results — rerank step skipped.",
        )
        return Command(update={"messages": [skip_msg]}, goto=END)


# ---------- Build Graph ----------
def build_graph(tools: Optional[List] = None) -> StateGraph:
    if tools is None:
        tools = []

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
    graph.add_node("route_after_tools", route_after_tools)
    graph.add_node("rerank", reranker_node)

    graph.add_edge(START, "embedding")
    graph.add_edge("embedding", "agent")
    graph.add_edge("agent", "tools")
    graph.add_edge("tools", "route_after_tools")
    graph.add_edge("route_after_tools", "rerank")
    graph.add_edge("route_after_tools", END)
    graph.add_edge("rerank", END)

    return graph


# ---------- Public Interface ----------
def build_online_graph(session: SessionContext):
    tools = make_tools(session)
    graph = build_graph(tools)
    app = graph.compile()

    original_invoke = app.invoke

    def wrapped_invoke(input_state: Dict[str, Any]):
        human_input = input_state["messages"][-1].content
        session.current_embedding = session.embedder.embed(human_input)
        input_state["inserted"] = False  # reset flag each invocation
        return original_invoke(input_state)

    app.invoke = wrapped_invoke
    return app


# ---------- Visualization ----------
def save_mermaid_graph(as_png: bool = True):
    graph = build_graph()
    compiled_graph = graph.compile()

    try:
        png_bytes = compiled_graph.get_graph().draw_mermaid_png()
        with open("agent_graph.png", "wb") as f:
            f.write(png_bytes)
        print("🖼️ Saved: agent_graph.png")
    except Exception as e:
        print(f"⚠️ Could not save agent_graph.png: {e}")
        print("Ensure `graphviz` is installed: `pip install graphviz`")

if __name__ == "__main__":
    print("Building agent graph...")
    save_mermaid_graph(as_png=True)
    print("Graph visualization saved.")
