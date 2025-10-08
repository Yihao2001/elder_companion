
import json
import logging
import os
import numpy as np
import yaml
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer, CrossEncoder
from sqlalchemy import create_engine, text
from huggingface_hub import login
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)



class Embedder:

    def __init__(self, model_name: str="google/embeddinggemma-300m"):
        load_dotenv()
        self.embedding_model_name = model_name
        self.model = None

        self.model = self._load_embedding_model()
        if not self.model:
            raise ValueError("Embedding model loading failed. Please check the model name and Huggingface token.")

    def _load_embedding_model(self):
        if self.model is None:
            huggingface_token = os.getenv("HUGGINGFACE_TOKEN")
            if huggingface_token:
                login(token=huggingface_token)
            else:
                logging.error("Huggingface token not found. Make sure the model is public or you have access.")
            logging.info(f"Loading embedding model: {self.embedding_model_name}")

            self.model = SentenceTransformer(self.embedding_model_name)
            logging.info(f"embedding model loaded successfully: {self.embedding_model_name}")
            return self.model
        return self.model

    def embed(self, txt: str) -> list:
        if not self.model:
            raise ValueError("Embedding model is not loaded.")
        if not text or not isinstance(txt, str):
            raise ValueError("Input text must be a non-empty string.")
        embedding = self.model.encode(txt, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not self.model:
            raise ValueError("Embedding model is not loaded.")
        if not texts or not all(isinstance(t, str) and t for t in texts):
            raise ValueError("Input texts must be a list of non-empty strings.")
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return [emb.tolist() for emb in embeddings]


class CrossEmbedder:

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        load_dotenv()
        self.model_name = model_name
        self.model = None

        self.model = self._load_model()
        if not self.model:
            raise ValueError(f"Failed to load CrossEncoder model: {model_name}")

    def _load_model(self):
        """Initialize and load the CrossEncoder model."""
        huggingface_token = os.getenv("HUGGINGFACE_TOKEN")
        if huggingface_token:
            login(token=huggingface_token)
        else:
            logging.warning("⚠️ No HuggingFace token found. Proceeding with public model access.")

        logging.info(f"Loading CrossEncoder model: {self.model_name}")
        try:
            model = CrossEncoder(self.model_name)
            logging.info(f"✅ CrossEncoder model loaded: {self.model_name}")
            return model
        except Exception as e:
            logging.error(f"❌ Error loading CrossEncoder model: {e}")
            return None
    
    def predict(self, pairs):
        ce_raw_scores = self.model.predict(pairs)
        return ce_raw_scores
