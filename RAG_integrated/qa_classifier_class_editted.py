from typing import TypedDict, Literal, Optional, List
import numpy as np, warnings


class ClassificationState(TypedDict):
    text: str
    flow_type: Literal["online", "offline"]
    qa: Optional[str]
    topic: Optional[str]


class QAClassifier:
    def __init__(self, model_objects: dict):
        self.model = model_objects["model"]
        self.tfidf_vectorizer = model_objects["tfidf_vectorizer"]
        self.sbert_model = model_objects["sbert_model"]
        self.question_words = ["who", "what", "where", "when", "why", "how", "which"]

    def _extract_simple_nlp_features(self, text: str) -> np.ndarray:
        words = text.lower().split()
        return np.array([
            int(text.lower().endswith("?")),
            int(words[0] in self.question_words if words else 0),
        ])

    def _prepare_features(self, texts: List[str]) -> np.ndarray:
        X_tfidf = self.tfidf_vectorizer.transform(texts).toarray()
        X_sbert = self.sbert_model.encode(texts, show_progress_bar=False)
        X_nlp = np.array([self._extract_simple_nlp_features(t) for t in texts])
        return np.hstack([X_tfidf, X_sbert, X_nlp])

    def classify_text_qa(self, state: ClassificationState) -> ClassificationState:
        warnings.filterwarnings("ignore", message="X does not have valid feature names")
        X_features = self._prepare_features([state["text"]])
        pred = self.model.predict(X_features)
        state["qa"] = "question" if pred[0] == 1 else "statement"
        return state
