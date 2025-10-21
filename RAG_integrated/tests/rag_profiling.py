import os
import time
import logging
import cProfile
import pstats
from collections import defaultdict
from typing import Any, Dict, List, Callable
from functools import wraps

# ---------------- Logging setup ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("profile_rag")

# ---------------- Timing decorator ----------------
timing_data: Dict[str, List[float]] = defaultdict(list)

def timed(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that records latency of each function call."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            timing_data[func.__name__].append(elapsed)
            logger.info(f"[TIMER] {func.__name__} took {elapsed:.3f}s")
    return wrapper

# ---------------- Imports (after defining timed) ----------------
from offline_graph_builder import (
    GraphState,
    build_offline_graph,
    retrieval_node_health,
    retrieval_node_longterm,
    retrieval_node_shortterm,
    reranker_node,
    insertion_node,
)

from session_context import SessionContext

for fn in [
    retrieval_node_health,
    retrieval_node_longterm,
    retrieval_node_shortterm,
    reranker_node,
    insertion_node,
]:
    name = fn.__name__
    globals()[name] = timed(fn)

# ---------------- Workflow ----------------
def run_workflow(session: SessionContext, input_text: str, qa_type: str, topics: List[str]) -> Dict[str, Any]:
    state: GraphState = {
        "session": session,
        "input_text": input_text,
        "qa_type": qa_type,
        "topics": topics,
        "candidates": [],
        "final_chunks": [],
        "inserted": False,
    }
    graph = build_offline_graph()
    result_state = graph.invoke(state)
    return result_state

# ---------------- Main ----------------
def main():
    session = SessionContext(
        db_url=os.getenv("DATABASE_URL"),
        elderly_id="87654321-4321-4321-4321-019876543210",
        cross_encoder_model="jinaai/jina-reranker-v1-turbo-en"
    )

    profiler = cProfile.Profile()
    profiler.enable()

    # Run both flows
    logger.info(">>> Starting question flow profiling")
    run_workflow(session, "What is the best exercise for elderly with arthritis?", "question", ["healthcare", "short-term"])

    logger.info(">>> Starting statement flow profiling")
    run_workflow(session, "I did 30 minutes of walking today.", "statement", ["short-term"])

    profiler.disable()

    # Save detailed profile
    out_file = "rag_profile.stats"
    profiler.dump_stats(out_file)
    logger.info(f"Profile data saved to: {out_file}")

    # Print summarized node latencies
    print("\n====== NODE-LEVEL LATENCY SUMMARY ======")
    for fn, times in timing_data.items():
        avg_t = sum(times) / len(times)
        print(f"{fn:<25} calls={len(times):<2} avg={avg_t:.3f}s max={max(times):.3f}s")

    print("========================================\n")

    # Still print top 20 from cProfile for deeper digging
    stats = pstats.Stats(profiler).strip_dirs().sort_stats("cumtime")
    stats.print_stats(20)

    logger.info("Profiling complete.")

if __name__ == "__main__":
    main()
