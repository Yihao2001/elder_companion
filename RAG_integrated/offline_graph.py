import os
import time
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from online_graph_builder import build_online_graph
from session_context import SessionContext
from utils.prompt import SYSTEM_PROMPT
from utils.logger import logger

"""
# Usage Example
from online_graph_builder import OnlineGraph

# Example input payload
data = {
    "text": "When do I take my medicine?",
    "flow_type": "offline",
    "qa": "question",
    "topic": "healthcare"
}

text = data.get("text")

# Initialize once
app = OnlineGraph(verbose=True)
results = app.invoke(text)
"""


class OnlineGraph:
    def __init__(
        self,
        db_env_var: str = "DATABASE_URL",
        elderly_id: str | None = None,
        cross_encoder_model: str = "jinaai/jina-reranker-v1-turbo-en",
        verbose: bool = False,
    ):
        load_dotenv()

        self.verbose = verbose
        self.elderly_id = elderly_id or os.getenv("ELDERLY_ID")
        self.db_url = os.getenv(db_env_var)

        if self.verbose:
            logger.info("🧠 Initializing OnlineGraph...")

        start = time.perf_counter()
        self.session = SessionContext(
            db_url=self.db_url,
            elderly_id=self.elderly_id,
            cross_encoder_model=cross_encoder_model,
        )
        self.app = build_online_graph(self.session)
        end = time.perf_counter()

        if self.verbose:
            logger.info(f"✅ OnlineGraph ready in {end - start:.2f}s")

    # ------------------------------------------------------
    def invoke(
        self,
        user_input: str,
        qa_type: str = "question",
        topics: list[str] | None = None,
        system_prompt: str | None = None,
    ) -> dict:
        """Convenient entrypoint for invoking the graph with minimal setup."""
        topics = topics or []
        system_prompt = system_prompt or SYSTEM_PROMPT

        system_msg = SystemMessage(content=system_prompt)
        human_msg = HumanMessage(content=user_input)

        payload = {
            "session": self.session,
            "messages": [system_msg, human_msg],
            "qa_type": qa_type,
            "topics": topics,
            "candidates": [],
            "final_chunks": [],
        }

        if self.verbose:
            logger.info(f"🚀 Invoking agent with input: {user_input!r}")

        result = self.app.invoke(payload)

        # Clean up embeddings for readable output
        if "final_chunks" in result:
            for chunk in result["final_chunks"]:
                chunk.pop("embedding", None)

        return result