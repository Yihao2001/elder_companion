import os
import time
import logging
import cProfile
import pstats
from collections import defaultdict
from typing import Any, Dict, List, Callable
from functools import wraps
from utils.logger import logger

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
from online_graph_builder import (
    build_online_graph,
    make_tools,
    route_after_tools,
    reranker_node,
    embedding_node,
)
from session_context import SessionContext
from langchain_core.messages import HumanMessage

# Wrap critical nodes
for fn in [embedding_node, reranker_node, route_after_tools]:
    name = fn.__name__
    globals()[name] = timed(fn)


# ---------------- Workflow ----------------
def run_online_workflow(session: SessionContext, input_text: str) -> Dict[str, Any]:
    """Simulate one online graph invocation."""
    graph = build_online_graph(session)
    messages = [HumanMessage(content=input_text)]
    state = {
        "session": session,
        "messages": messages,
        "candidates": [],
        "final_chunks": [],
        "inserted": False,
    }

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
    logger.info(">>> Starting online agent flow (retrieval)")
    run_online_workflow(session, "What are the symptoms of dehydration?")

    logger.info(">>> Starting online agent flow (insertion)")
    run_online_workflow(session, "I took my blood pressure medicine this morning.")

    profiler.disable()

    # Save detailed profile
    out_file = "tests/online_profile.stats"
    profiler.dump_stats(out_file)
    logger.info(f"Profile data saved to: {out_file}")

    # Summarize timing
    print("\n====== NODE-LEVEL LATENCY SUMMARY ======")
    for fn, times in timing_data.items():
        avg_t = sum(times) / len(times)
        print(f"{fn:<25} calls={len(times):<2} avg={avg_t:.3f}s max={max(times):.3f}s")
    print("========================================\n")

    # Print top 20 from cProfile
    stats = pstats.Stats(profiler).strip_dirs().sort_stats("cumtime")
    stats.print_stats(20)

    logger.info("Online graph profiling complete.")


if __name__ == "__main__":
    main()
