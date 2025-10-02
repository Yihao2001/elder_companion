import os
from dotenv import load_dotenv

# Load .env from the same directory as this file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")

    # HuggingFace
    HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

    # Encryption key
    DATABASE_ENCRYPTION_KEY = os.getenv("DATABASE_ENCRYPTION_KEY")

    # Authorisation token for Flask endpoints
    AUTHORIZATION_TOKEN = os.getenv("AUTHORIZATION_TOKEN")

    # Token to verify that JWT from frontend is issued by backend
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
