import logging
import os
from typing import List
from dotenv import load_dotenv
from huggingface_hub import login
from sentence_transformers import SentenceTransformer, CrossEncoder
from module_3.utils.logger import logger

class Embedder:
    def __init__(self, model_name: str = "google/embeddinggemma-300m"):
        load_dotenv()
        self.embedding_model_name = model_name
        self.model = None
        self._ensure_model_loaded()

    def _ensure_model_loaded(self):
        """Lazy load embedding model when needed."""
        if self.model is not None:
            return

        # Import heavy modules here, not at top-level


        huggingface_token = os.getenv("HUGGINGFACE_TOKEN")
        if huggingface_token:
            login(token=huggingface_token)
        else:
            logger.warning("⚠️ No HuggingFace token found. Proceeding without login.")

        self.model = SentenceTransformer(self.embedding_model_name, device="cpu")
        logger.info(f"✅ Embedding model loaded: {self.embedding_model_name}")

    def embed(self, txt: str) -> list:
        if not isinstance(txt, str) or not txt.strip():
            raise ValueError("Input must be a non-empty string.")
        if not self.model:
            self._ensure_model_loaded()
        embedding = self.model.encode(txt, normalize_embeddings=True, show_progress_bar=False)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts or not all(isinstance(t, str) and t.strip() for t in texts):
            raise ValueError("Input texts must be a list of non-empty strings.")
        if not self.model:
            self._ensure_model_loaded()
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]


class CrossEmbedder:
    def __init__(self, model_name: str = "jinaai/jina-reranker-v1-turbo-en"):
        load_dotenv()
        self.model_name = model_name
        self.model = None
        self._ensure_model_loaded()

    def _ensure_model_loaded(self):
        """Load CrossEncoder model lazily."""
        huggingface_token = os.getenv("HUGGINGFACE_TOKEN")
        if huggingface_token:
            login(token=huggingface_token)
        else:
            logger.warning("⚠️ No HuggingFace token found. Proceeding with public model access.")

        try:
            self.model = CrossEncoder(self.model_name, trust_remote_code=True)
            logger.info(f"✅ CrossEncoder loaded: {self.model_name}")
        except Exception as e:
            logger.error(f"❌ Error loading CrossEncoder model: {e}")
            self.model = None

    def predict(self, pairs):
        if not self.model:
            self._ensure_model_loaded()
        return self.model.predict(pairs)
