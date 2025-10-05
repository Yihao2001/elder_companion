from sentence_transformers import SentenceTransformer
from typing import TypedDict, List, Literal, Optional
import numpy as np
import pickle
import re


class ClassificationState(TypedDict):
    text: str
    flow_type: Literal["online", "offline"]
    qa: Optional[str]
    topic: Optional[str]


class TopicClassifier:
    """
    A class-based wrapper for the stacked QA classifier using TF-IDF, SBERT, and simple NLP features.
    Compatible with LangChain's Runnable interface.
    """

    def __init__(
        self,
        model_path: str = "./model_weights/topic_log_reg_hybrid_model.pkl",
        tfidf_path: str = "./model_weights/topic_tfidf_vectorizer.pkl",
        sbert_name_path: str = "./model_weights/topic_sbert_model_name.pkl",
        le_path: str = "./model_weights/topic_label_encoder.pkl",
        keywords_path: str = "./model_weights/topic_category_keywords.pkl"
    ):
        # Load trained components
        with open(model_path, "rb") as f:
            self.log_reg_model_topic = pickle.load(f)

        with open(tfidf_path, "rb") as f:
            self.tfidf_vectorizer_topic = pickle.load(f)

        with open(sbert_name_path, "rb") as f:
            sbert_model_name = pickle.load(f)
            self.sbert_model_topic = SentenceTransformer(sbert_model_name)

        with open(le_path, "rb") as f:
            self.le_topic = pickle.load(f)

        with open(keywords_path, "rb") as f:
            self.CATEGORY_KEYWORDS = pickle.load(f)

        # Define question-related words for heuristic features
        self.question_words = ['who', 'what', 'where', 'when', 'why', 'how', 'which']

    def count_category_words_topic(self, text, category_words):
        words = re.findall(r'\b\w+\b', text.lower())
        return sum(1 for w in words if w in category_words)

    def prepare_features_topic(self, texts):
        X_tfidf = self.tfidf_vectorizer_topic.transform(texts).toarray()
        X_sbert = self.sbert_model_topic.encode(texts, show_progress_bar=False)
        category_features = np.array([
            [
                self.count_category_words_topic(t, self.CATEGORY_KEYWORDS['healthcare']),
                self.count_category_words_topic(t, self.CATEGORY_KEYWORDS['longterm']),
                self.count_category_words_topic(t, self.CATEGORY_KEYWORDS['shortterm'])
            ]
            for t in texts
        ])
        return np.hstack([X_tfidf, X_sbert, category_features])

    def classify_text_topic(self, state: ClassificationState) -> ClassificationState:
        X_features = self.prepare_features_topic([state["text"]])
        pred_int = self.log_reg_model_topic.predict(X_features)
        state["topic"] = self.le_topic.inverse_transform(pred_int)[0]
        return state

'''
if __name__ == "__main__":
    classifier = TopicClassifier()
    state: ClassificationState = {"text": "When do I take my medicine?", "topic": ""}
    result = classifier.classify_text_topic(state)
    print(result)
'''