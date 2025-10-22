import os

import pickle
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_google_genai import ChatGoogleGenerativeAI

from module_3.utils.embedder import Embedder, CrossEmbedder
from module_3.utils.logger import logger

class SessionContext:

    def __init__(self, elderly_id: str, db_url: str, cross_encoder_model):
        load_dotenv()

        self.elderly_id = elderly_id

        # === Database engine ===
        self.db_engine = create_engine(
            os.getenv("DATABASE_URL"),
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        self.conn = self.db_engine.connect()

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
            self.db_engine.dispose()
            logger.info("✅ SessionContext shutdown: database engine disposed.")
        except Exception as e:
            logger.error(f"Shut down error:  {e}")
