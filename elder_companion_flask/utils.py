from flask import request, jsonify
from functools import wraps
from huggingface_hub import login
from sentence_transformers import SentenceTransformer
from .config import Config

_model = None

def init_model():
    """
    Initialise model and store it globally when app starts
    """
    global _model
    login(Config.HUGGINGFACE_TOKEN)
    _model = SentenceTransformer("google/embeddinggemma-300m")

def get_embedding(text: str):
    if _model is None:
        raise RuntimeError("Model not initialized. Call init_model() first.")
    return _model.encode(text).tolist()
