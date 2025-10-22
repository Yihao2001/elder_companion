import os

import pickle
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_google_genai import ChatGoogleGenerativeAI

from module_3.utils.embedder import Embedder, CrossEmbedder
from module_3.utils.logger import logger

class SessionContext:

    def __init__(self, elderly_id: str, db_url: str, cross_encoder_model="jinaai/jina-reranker-v1-turbo-en"):
        load_dotenv()

        self.elderly_id = elderly_id

        # === Database engine ===
        self.engine = create_engine(
            os.getenv("DATABASE_URL"),
            pool_size=8,
            max_overflow=16,
            pool_pre_ping=True,
            pool_recycle=600,     # e.g., 10 min; keep < proxy idle timeout
            pool_timeout=30,
            pool_use_lifo=True,
        )

        # self.conn = self.db_engine.connect()

        # === Shared embedding models ===
        self.embedder = Embedder(model_name="google/embeddinggemma-300m")
        self.cross_encoder = CrossEmbedder(cross_encoder_model)

        # === Shared LLM (for online classification or generation) ===
        self.llm_online = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0.6,
        )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def shutdown(self):
        """Dispose pooled DB connections on app shutdown."""
        try:
            logger.info("Shutting down")
            self.engine.dispose()   # <-- was self.db_engine
            logger.info("✅ SessionContext shutdown: database engine disposed.")
        except Exception as e:
            logger.error(f"Shut down error: {e}")
