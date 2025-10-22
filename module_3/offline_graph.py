import os
import time
from typing import Any
from dotenv import load_dotenv

from module_3.offline_graph_builder import build_offline_graph
from module_3.session_context import SessionContext
from module_3.utils.logger import logger


""""
Usage Example
from OfflineGraph import OfflineGraph

# Example input payload
data = {
    "text": "When do I take my medicine?",
    "flow_type": "offline", ## this is not neccessary
    "qa": "question",
    "topic": "healthcare"
}

app = OfflineGraph(verbose=True)
results = app.invoke(data)
"""

class OfflineGraph:
    def __init__(
        self,
        session: SessionContext | None = None,
        db_env_var: str = "DATABASE_URL",
        elderly_id: str | None = None,
        cross_encoder_model: str = "jinaai/jina-reranker-v1-turbo-en",
        verbose: bool = False,
    ):
        load_dotenv()
        self.verbose = verbose

        if session is not None:
            self.session = session
        else:
            self.db_url = os.getenv(db_env_var)
            self.elderly_id = elderly_id or os.getenv("ELDERLY_ID")

            self.session = SessionContext(
                db_url=self.db_url,
                elderly_id=self.elderly_id,
                cross_encoder_model=cross_encoder_model,
            )

        start = time.perf_counter()
        self.app = build_offline_graph()
        end = time.perf_counter()

        if self.verbose:
            logger.info(f"✅ OfflineGraph ready in {end - start:.2f}s")


    # -----------------------------------------------------
    def invoke(self, data: dict[str, Any]) -> dict:
        if not data or "text" not in data:
            raise ValueError("Missing required key 'text' in data.")

        text = data["text"]
        qa = data.get("qa", "question")
        topic = data.get("topic", "short-term")

        # Normalize topic to list
        topics = topic if isinstance(topic, list) else [topic]

        # Validate qa_type
        if qa not in ("question", "statement"):
            raise ValueError("qa must be 'question' or 'statement'")

        # Validate topics
        allowed_topics = {"healthcare", "long-term", "short-term"}
        invalid = [t for t in topics if t not in allowed_topics]
        if invalid:
            raise ValueError(f"Invalid topic(s): {invalid}. Allowed: {allowed_topics}")

        # Minimal required state — LangGraph auto-initializes the rest
        state = {
            "session": self.session,
            "input_text": text,
            "qa_type": qa,
            "topics": topics,
            # Optional but safe to include for clarity (not strictly needed):
            # "inserted": False,  # Uncomment if you want to be extra explicit
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

        # Clean up embeddings for readability
        if "final_chunks" in result:
            for chunk in result["final_chunks"]:
                chunk.pop("embedding", None)

        return result