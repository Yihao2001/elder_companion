import os
import time
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from module_3.online_graph_builder import build_online_graph
from module_3.session_context import SessionContext
from module_3.utils.prompt import SYSTEM_PROMPT
from module_3.utils.logger import logger

"""
# Usage Example
from OnlineGraph import OnlineGraph

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
            self.elderly_id = elderly_id or os.getenv("ELDERLY_ID")
            self.db_url = os.getenv(db_env_var)

            self.session = SessionContext(
                db_url=self.db_url,
                elderly_id=self.elderly_id,
                cross_encoder_model=cross_encoder_model,
            )

        start = time.perf_counter()
        self.app = build_online_graph(self.session)
        end = time.perf_counter()

        if self.verbose:
            logger.info(f"✅ OnlineGraph ready in {end - start:.2f}s")

    # ------------------------------------------------------
    def invoke(
        self,
        user_input: str,
    ) -> dict:
        """Convenient entrypoint for invoking the graph with minimal setup."""
        system_msg = SystemMessage(content=SYSTEM_PROMPT)
        human_msg = HumanMessage(content=user_input)

        payload = {
            "session": self.session,
            "messages": [system_msg, human_msg],
        }

        if self.verbose:
            logger.info(f"🚀 Invoking agent with input: {user_input!r}")

        # ⏱️ Add perf timing here (like in offline_graph)
        start_time = time.perf_counter()
        result = self.app.invoke(payload)
        end_time = time.perf_counter()

        latency = end_time - start_time
        if self.verbose:
            logger.info(f"⏱️ Execution completed in {latency:.3f}s")

        # Clean up embeddings for readable output
        if "final_chunks" in result:
            for chunk in result["final_chunks"]:
                chunk.pop("embedding", None)

        return result