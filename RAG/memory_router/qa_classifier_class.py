from sentence_transformers import SentenceTransformer
from typing import TypedDict, List, Literal, Optional
import numpy as np
import pickle
import warnings


class ClassificationState(TypedDict):
    text: str
    flow_type: Literal["online", "offline"]
    qa: Optional[str]
    topic: Optional[str]


class QAClassifier:
    """
    A class-based wrapper for the stacked QA classifier using TF-IDF, SBERT, and simple NLP features.
    """

    def __init__(
        self,
        model_path: str = "./model_weights/qa_stacked_hybrid_model.pkl",
        tfidf_path: str = "./model_weights/qa_tfidf_vectorizer.pkl",
        sbert_name_path: str = "./model_weights/qa_sbert_model_name.pkl",
    ):
        # Load trained components
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)
        with open(tfidf_path, "rb") as f:
            self.tfidf_vectorizer = pickle.load(f)
        with open(sbert_name_path, "rb") as f:
            sbert_model_name = pickle.load(f)
        self.sbert_model = SentenceTransformer(sbert_model_name)

        # Define question-related words for heuristic features
        self.question_words = ['who', 'what', 'where', 'when', 'why', 'how', 'which']

    def _extract_simple_nlp_features(self, text: str) -> np.ndarray:
        """Extracts simple binary linguistic features for question detection."""
        words = text.lower().split()
        return np.array([
            int(text.lower().endswith('?')),
            int(words[0] in self.question_words if words else 0)
        ])

    def _prepare_features(self, texts: List[str]) -> np.ndarray:
        """Combines TF-IDF, SBERT, and simple NLP features into a single feature matrix."""
        X_tfidf = self.tfidf_vectorizer.transform(texts).toarray()
        X_sbert = self.sbert_model.encode(texts, show_progress_bar=False)
        X_nlp = np.array([self._extract_simple_nlp_features(t) for t in texts])
        return np.hstack([X_tfidf, X_sbert, X_nlp])

    def classify_text_qa(self, state: ClassificationState) -> ClassificationState:
        """Predicts whether the text is a question or statement."""
        warnings.filterwarnings("ignore", message="X does not have valid feature names")
        X_features = self._prepare_features([state["text"]])
        pred = self.model.predict(X_features)
        state["qa"] = "question" if pred[0] == 1 else "statement"
        return state

'''
if __name__ == "__main__":
    classifier = QAClassifier()
    state: ClassificationState = {"text": "When do I take my medicine?", "qa": ""}
    result = classifier.classify_text_qa(state)
    print(result)
'''