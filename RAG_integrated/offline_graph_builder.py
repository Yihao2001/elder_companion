from __future__ import annotations
from typing import TypedDict, Literal, List, Dict, Any, Optional
from typing_extensions import Annotated
import operator
from langgraph.graph import StateGraph, START, END
from session_context import SessionContext

from rag_functions import (
    retrieve_hybrid_stm,
    retrieve_hybrid_hcm,
    retrieve_hybrid_ltm,
    rerank_with_mmr_and_recency,
    insert_short_term,
)
from utils.logger import logger 


AllowedTopic = Literal["healthcare", "long-term", "short-term"]


# ---------- State ----------
class GraphState(TypedDict):
    session: Annotated[SessionContext, lambda x, y: x or y]
    input_text: Annotated[str, lambda x, y: x or y]
    qa_type: Annotated[Literal["question", "statement"], lambda x, y: x or y]
    topics: Annotated[List[AllowedTopic], lambda x, y: x or y]
    query_embedding: Annotated[Optional[List[float]], lambda x, y: x or y]
    candidates: Annotated[List[Dict[str, Any]], operator.add]
    final_chunks: Annotated[List[Dict[str, Any]], operator.add]
    inserted: Annotated[bool, lambda x, y: x or y]


# ---------- Nodes ----------

def embedding_node(state: GraphState) -> Dict[str, Any]:
    """Computes the embedding for the input_text and stores it in the state."""
    session = state["session"]
    text = state["input_text"]
    logger.info("Called embedding_node...")
    
    # We enforce that the embedder must be present at this point
    if session.embedder is None:
        raise ValueError("Embedder not provided in SessionContext.")

    # Compute embedding
    embedding = session.embedder.embed(text)
    
    logger.info("embedding_node successful! Computed embedding of size %d.", len(embedding))
    return {"query_embedding": embedding}


def retrieval_node_health(state: GraphState) -> Dict[str, Any]:
    session = state["session"]
    text = state["input_text"]
    embedding = state["query_embedding"] # Get pre-computed embedding
    logger.info("Called retrieval_node_health...")
    results = retrieve_hybrid_hcm(
        conn=session.conn,
        elderly_id=session.elderly_id,
        query=text,
        embedder=session.embedder, # Pass embedder as fallback/for other steps in hybrid
        embedding=embedding,        # Pass pre-computed embedding
    )
    logger.info("retrieval_node_health successful! Retrieved %d results.", len(results))
    return {"candidates": results}


def retrieval_node_longterm(state: GraphState) -> Dict[str, Any]:
    session = state["session"]
    text = state["input_text"]
    embedding = state["query_embedding"] # Get pre-computed embedding
    logger.info("Called retrieval_node_longterm...")
    results = retrieve_hybrid_ltm(
        conn=session.conn,
        elderly_id=session.elderly_id,
        query=text,
        embedder=session.embedder,
        embedding=embedding,        # Pass pre-computed embedding
    )
    logger.info("retrieval_node_longterm successful! Retrieved %d results.", len(results))
    return {"candidates": results}


def retrieval_node_shortterm(state: GraphState) -> Dict[str, Any]:
    session = state["session"]
    text = state["input_text"]
    embedding = state["query_embedding"] # Get pre-computed embedding
    logger.info("Called retrieval_node_shortterm...")
    results = retrieve_hybrid_stm(
        conn=session.conn,
        elderly_id=session.elderly_id,
        query=text,
        embedder=session.embedder,
        embedding=embedding,        # Pass pre-computed embedding
    )
    logger.info("retrieval_node_shortterm successful! Retrieved %d results.", len(results))
    return {"candidates": results}


def reranker_node(state: GraphState) -> Dict[str, Any]:
    session = state["session"]
    text = state["input_text"]
    candidates = state.get("candidates", [])
    logger.info("Called reranker_node with %d candidates...", len(candidates))
    # No change needed here, as the retrieval nodes already fetch the candidate embeddings
    # and reranker_with_mmr_and_recency does not use the query embedding (only the query text).
    chunks = rerank_with_mmr_and_recency(
        query=text, candidates=candidates, cross_encoder=session.cross_encoder
    )
    logger.info("reranker_node successful! Produced %d chunks.", len(chunks))
    return {"final_chunks": chunks}


def insertion_node(state: GraphState) -> Dict[str, Any]:
    session = state["session"]
    text = state["input_text"]
    embedding = state["query_embedding"] # Get pre-computed embedding
    logger.info("Called insertion_node...")
    
    # The insert_short_term function now accepts the pre-computed embedding
    result = insert_short_term(
        conn=session.conn,
        content=text,
        elderly_id=session.elderly_id,
        embedder=session.embedder,
        embedding=embedding, # Pass pre-computed embedding
    )
    
    if result.get("success"):
        logger.info("insertion_node successful! Inserted new content (ID: %s).", result.get("record_id"))
        return {"inserted": True}
    else:
        logger.error("insertion_node failed: %s", result.get("error"))
        # In a real application, you might raise an exception or handle the failure
        return {"inserted": False}


# ---------- Routers (No change needed) ----------
def qa_router(state: GraphState) -> str:
    """Route between question and statement flows."""
    qa = state["qa_type"]
    return "question" if qa == "question" else "statement"


def topics_router(state: GraphState) -> Dict[str, List[str]]:
    """Router that returns selected topics as a list in a dict."""
    seen = set()
    selected: List[str] = []
    for t in state.get("topics", []):
        if t in ("healthcare", "long-term", "short-term") and t not in seen:
            selected.append(t)
            seen.add(t)
    return {"next": selected}


def retrieve_insert_statement(state: GraphState) -> Dict[str, List[str]]:
    """For 'statement', run insertion AND retrieval in parallel."""
    return {"next": ["insert", "retrieve"]}


# ---------- Subgraph Builders (No change needed to structure) ----------
def build_retrieval_subgraph(name_prefix: str = "") -> StateGraph[GraphState]:
    """Builds a mini-graph that:
       topics_router -> topic-specific retrieval nodes -> rerank
    """
    g = StateGraph(GraphState)
    g.add_node(f"{name_prefix}topics_router", topics_router)
    g.add_node(f"{name_prefix}retrieve_healthcare", retrieval_node_health)
    g.add_node(f"{name_prefix}retrieve_long_term", retrieval_node_longterm)
    g.add_node(f"{name_prefix}retrieve_short_term", retrieval_node_shortterm)
    g.add_node(f"{name_prefix}rerank", reranker_node)

    # Fan-out based on topics
    g.add_conditional_edges(
        f"{name_prefix}topics_router",
        lambda s: s["next"],
        {
            "healthcare": f"{name_prefix}retrieve_healthcare",
            "long-term": f"{name_prefix}retrieve_long_term",
            "short-term": f"{name_prefix}retrieve_short_term",
        },
    )

    # Merge to rerank
    g.add_edge(f"{name_prefix}retrieve_healthcare", f"{name_prefix}rerank")
    g.add_edge(f"{name_prefix}retrieve_long_term", f"{name_prefix}rerank")
    g.add_edge(f"{name_prefix}retrieve_short_term", f"{name_prefix}rerank")

    g.add_edge(START, f"{name_prefix}topics_router")
    g.add_edge(f"{name_prefix}rerank", END)
    return g


def build_insertion_subgraph(name_prefix: str = "") -> StateGraph[GraphState]:
    """Simple insertion subgraph."""
    g = StateGraph(GraphState)
    g.add_node(f"{name_prefix}insert", insertion_node)
    g.add_edge(START, f"{name_prefix}insert")
    g.add_edge(f"{name_prefix}insert", END)
    return g


# ---------- Unified Graph (Modified) ----------
def build_offline_graph() -> Any:
    """Unifies the embedding, retrieval and insertion logic."""
    retrieval = build_retrieval_subgraph("q_")
    retrieval_stmt = build_retrieval_subgraph("s_")
    insertion = build_insertion_subgraph("s_")

    g = StateGraph(GraphState)

    g.add_node("embedding_node", embedding_node)
    
    g.add_node("retrieval_question", retrieval.compile())
    g.add_node("retrieval_statement", retrieval_stmt.compile())
    g.add_node("insertion_statement", insertion.compile())

    g.add_node("qa_router", qa_router)
    g.add_node("retrieve_insert_statement", retrieve_insert_statement)

    # Start with embedding, then route
    g.add_edge(START, "embedding_node")
    
    # Question vs Statement routing after embedding
    g.add_conditional_edges(
        "embedding_node",
        qa_router,
        {
            "question": "retrieval_question",
            "statement": "retrieve_insert_statement",
        },
    )

    # For statements, run insertion and retrieval in parallel
    g.add_conditional_edges(
        "retrieve_insert_statement",
        lambda s: s["next"],
        {
            "insert": "insertion_statement",
            "retrieve": "retrieval_statement",
        },
    )
    
    # Final END nodes (assuming some other nodes might follow, but for now they are terminal)
    g.add_edge("retrieval_question", END)
    g.add_edge("retrieval_statement", END)
    g.add_edge("insertion_statement", END)

    return g.compile()


# ---------- Visualization (No change needed) ----------
def save_mermaid_graph(as_png: bool = True):
    """Build and save the LangGraph DAGs as PNG images only."""
    unified_graph = build_offline_graph()
    retrieval_q_graph = build_retrieval_subgraph("q_").compile()
    retrieval_s_graph = build_retrieval_subgraph("s_").compile()
    insertion_graph = build_insertion_subgraph("s_").compile()

    gviz_unified = unified_graph.get_graph()
    gviz_retrieval_q = retrieval_q_graph.get_graph()
    gviz_retrieval_s = retrieval_s_graph.get_graph()
    gviz_insertion = insertion_graph.get_graph()

    graphs = [
        ("unified_graph", gviz_unified),
        ("retrieval_question_graph", gviz_retrieval_q),
        ("retrieval_statement_graph", gviz_retrieval_s),
        ("insertion_statement_graph", gviz_insertion),
    ]

    for name, gviz in graphs:
        # NOTE: This part assumes langgraph is correctly installed with graphviz dependencies
        try:
            png_bytes = gviz.draw_mermaid_png()
            with open(f"{name}.png", "wb") as f:
                f.write(png_bytes)
            print(f"🖼️ Saved: {name}.png")
        except Exception as e:
            print(f"⚠️ Could not save {name}.png: {e}")
            print("Please ensure graphviz is installed and accessible for PNG generation.")


if __name__ == "__main__":
    # Example usage:
    # Build and compile the graph
    app = build_offline_graph()
    print("Graph built successfully.")
    
    save_mermaid_graph(as_png=True)