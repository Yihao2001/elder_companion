from huggingface_hub import login
from sentence_transformers import SentenceTransformer
import bcrypt
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

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def check_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
