from typing import TypedDict, Literal, Optional
import numpy as np, re


class ClassificationState(TypedDict):
    text: str
    flow_type: Literal["online", "offline"]
    qa: Optional[str]
    topic: Optional[str]


class TopicClassifier:
    def __init__(self, model_objects: dict):
        """Initialize from preloaded models in SessionContext"""
        self.log_reg_model_topic = model_objects["log_reg_model_topic"]
        self.tfidf_vectorizer_topic = model_objects["tfidf_vectorizer_topic"]
        self.sbert_model_topic = model_objects["sbert_model_topic"]
        self.le_topic = model_objects["le_topic"]
        self.CATEGORY_KEYWORDS = model_objects["CATEGORY_KEYWORDS"]

        self.question_words = ["who", "what", "where", "when", "why", "how", "which"]

    def count_category_words_topic(self, text, category_words):
        words = re.findall(r"\b\w+\b", text.lower())
        return sum(1 for w in words if w in category_words)

    def prepare_features_topic(self, texts):
        X_tfidf = self.tfidf_vectorizer_topic.transform(texts).toarray()
        X_sbert = self.sbert_model_topic.encode(texts, show_progress_bar=False)
        category_features = np.array([
            [
                self.count_category_words_topic(t, self.CATEGORY_KEYWORDS["healthcare"]),
                self.count_category_words_topic(t, self.CATEGORY_KEYWORDS["longterm"]),
                self.count_category_words_topic(t, self.CATEGORY_KEYWORDS["shortterm"]),
            ]
            for t in texts
        ])
        return np.hstack([X_tfidf, X_sbert, category_features])

    def classify_text_topic(self, state: ClassificationState) -> ClassificationState:
        X_features = self.prepare_features_topic([state["text"]])
        pred_int = self.log_reg_model_topic.predict(X_features)
        state["topic"] = self.le_topic.inverse_transform(pred_int)[0]
        return state
