import os
from dotenv import load_dotenv
import time
from typing import Any
from session_context import SessionContext
from offline_graph_builder import build_offline_graph
from utils.logger import logger

""""
Usage Example
from offline_graph_builder import OfflineAgentApp

# Example input payload
data = {
    "text": "When do I take my medicine?",
    "flow_type": "offline",
    "qa": "question",
    "topic": "healthcare"
}

app = OfflineAgentApp(verbose=True)
results = app.invoke(data)
"""


class OfflineAgentApp:
    def __init__(
        self,
        db_env_var: str = "DATABASE_URL",
        elderly_id: str | None = None,
        cross_encoder_model: str = "jinaai/jina-reranker-v1-turbo-en",
        verbose: bool = False,
    ):
        load_dotenv()

        self.verbose = verbose
        self.db_url = os.getenv(db_env_var)
        self.elderly_id = elderly_id or os.getenv("ELDERLY_ID")

        if self.verbose:
            logger.info("🧠 Initializing OfflineAgentApp...")

        start = time.perf_counter()
        self.session = SessionContext(
            db_url=self.db_url,
            elderly_id=self.elderly_id,
            cross_encoder_model=cross_encoder_model,
        )
        self.app = build_offline_graph()
        end = time.perf_counter()

        if self.verbose:
            logger.info(f"✅ OfflineAgentApp ready in {end - start:.2f}s")

    # ------------------------------------------------------
    def invoke(self, data: dict[str, Any]) -> dict:
        """
        Invokes the offline graph with a simple data dict.

        Expected keys:
            - text (str)
            - qa (str): "question" or "statement"
            - topic (str or list[str]): may be single topic or list
            - flow_type (str): ignored but kept for uniformity
        """
        if not data or "text" not in data:
            raise ValueError("Missing required key 'text' in data.")

        text = data.get("text")
        qa = data.get("qa", "question")
        topic = data.get("topic", "short-term")

        # Allow topic to be string or list
        topics = topic if isinstance(topic, list) else [topic]

        state = {
            "session": self.session,
            "input_text": text,
            "qa_type": qa,
            "topics": topics,
            "candidates": [],
            "final_chunks": [],
            "inserted": False,
        }

        if self.verbose:
            logger.info(f"🚀 Invoking offline agent (qa={qa}, topics={topics})...")
            logger.info(f"🗣️  Input text: {text}")

        start_time = time.perf_counter()
        result = self.app.invoke(state)
        end_time = time.perf_counter()

        latency = end_time - start_time
        if self.verbose:
            logger.info(f"⏱️ Execution completed in {latency:.3f}s")

        # Remove embeddings for cleaner printing
        if "final_chunks" in result:
            for chunk in result["final_chunks"]:
                chunk.pop("embedding", None)

        return result