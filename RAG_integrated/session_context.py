import os
import pickle
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from RAG.utils.embedder import Embedder, CrossEmbedder
from topic_classifier_class_editted import TopicClassifier
from qa_classifier_class_editted import QAClassifier
from rag_functions import (
    insert_short_term,
    retrieve_hybrid_stm,
    retrieve_hybrid_ltm,
    retrieve_hybrid_hcm,
    retrieve_rerank,
)

class SessionContext:
    """
    Centralized context for shared resources:
    - Database engine
    - Classifiers (QA + Topic)
    - Embedding and reranker models
    - LLM client
    - Retrieval and insertion utilities

    Loaded once during FastAPI startup and reused across all requests.
    """

    def __init__(self):
        load_dotenv()

        # === Database engine ===
        self.db_engine = create_engine(
            os.getenv("DATABASE_URL"),
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        # === Core models ===
        self._load_classification_models()

        # === Shared embedding models ===
        self.embedder = Embedder(model_name="google/embeddinggemma-300m")
        self.cross_encoder = CrossEmbedder("BAAI/bge-reranker-base")

        # === Shared LLM (for online classification or generation) ===
        self.llm_online = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0,
            max_output_tokens=1000,
        )

        # === Retrieval + insertion utilities ===
        self.insert_short_term = insert_short_term
        self.retrieve_rerank = retrieve_rerank
        self.retrieve_hybrid_stm = retrieve_hybrid_stm
        self.retrieve_hybrid_ltm = retrieve_hybrid_ltm
        self.retrieve_hybrid_hcm = retrieve_hybrid_hcm

    # ------------------------------------------------------------------
    # Model Loading
    # ------------------------------------------------------------------
    def _load_classification_models(self):
        """Load pickled classifier components and SentenceTransformers once."""
        print("🔹 Loading topic and QA classifiers...")

        # ---- Topic Classifier Components ----
        with open("./model_weights/topic_log_reg_hybrid_model.pkl", "rb") as f:
            log_reg_model_topic = pickle.load(f)
        with open("./model_weights/topic_tfidf_vectorizer.pkl", "rb") as f:
            tfidf_vectorizer_topic = pickle.load(f)
        with open("./model_weights/topic_sbert_model_name.pkl", "rb") as f:
            sbert_model_name_topic = pickle.load(f)
        with open("./model_weights/topic_label_encoder.pkl", "rb") as f:
            le_topic = pickle.load(f)
        with open("./model_weights/topic_category_keywords.pkl", "rb") as f:
            category_keywords = pickle.load(f)

        sbert_model_topic = SentenceTransformer(sbert_model_name_topic)

        topic_model_objects = {
            "log_reg_model_topic": log_reg_model_topic,
            "tfidf_vectorizer_topic": tfidf_vectorizer_topic,
            "sbert_model_topic": sbert_model_topic,
            "le_topic": le_topic,
            "CATEGORY_KEYWORDS": category_keywords,
        }

        # ---- QA Classifier Components ----
        with open("./model_weights/qa_stacked_hybrid_model.pkl", "rb") as f:
            qa_model = pickle.load(f)
        with open("./model_weights/qa_tfidf_vectorizer.pkl", "rb") as f:
            qa_tfidf_vectorizer = pickle.load(f)
        with open("./model_weights/qa_sbert_model_name.pkl", "rb") as f:
            sbert_model_name_qa = pickle.load(f)

        sbert_model_qa = SentenceTransformer(sbert_model_name_qa)

        qa_model_objects = {
            "model": qa_model,
            "tfidf_vectorizer": qa_tfidf_vectorizer,
            "sbert_model": sbert_model_qa,
        }

        # Instantiate lightweight classifier wrappers
        self.topic_classifier = TopicClassifier(model_objects=topic_model_objects)
        self.qa_classifier = QAClassifier(model_objects=qa_model_objects)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def shutdown(self):
        """Dispose pooled DB connections on app shutdown."""
        try:
            self.db_engine.dispose()
            print("✅ SessionContext shutdown: database engine disposed.")
        except Exception as e:
            print(f"⚠️ Error during shutdown: {e}")
