from sentence_transformers import SentenceTransformer
import numpy as np
import pickle
import re

from module_2.states import ClassificationState

class TopicClassifier:
    """
    Multi-label topic classifier using TF-IDF, SBERT, and category word counts.
    Compatible with LangChain's Runnable interface.
    """

    def __init__(
        self,
        ova_models_paths: dict = {
            'healthcare': "RAG/memory_router/model_weights/log_reg_ova_healthcare.pkl",
            'long-term': "RAG/memory_router/model_weights/log_reg_ova_long-term.pkl",
            'short-term': "RAG/memory_router/model_weights/log_reg_ova_short-term.pkl"
        },
        tfidf_path: str = "RAG/memory_router/model_weights/topic_tfidf_vectorizer.pkl",
        sbert_name_path: str = "RAG/memory_router/model_weights/topic_sbert_model_name.pkl",
        keywords_path: str = "RAG/memory_router/model_weights/topic_category_keywords.pkl"
    ):
        # Load OvA models
        self.models_ova = {}
        for label, path in ova_models_paths.items():
            with open(path, "rb") as f:
                self.models_ova[label] = pickle.load(f)

        # Load TF-IDF vectorizer
        with open(tfidf_path, "rb") as f:
            self.tfidf_vectorizer_topic = pickle.load(f)

        # Load SBERT model
        with open(sbert_name_path, "rb") as f:
            sbert_model_name = pickle.load(f)
            self.sbert_model_topic = SentenceTransformer(sbert_model_name)

        # Load category keywords
        with open(keywords_path, "rb") as f:
            self.CATEGORY_KEYWORDS = pickle.load(f)

        # Define question-related words for heuristic features (if needed)
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
        predicted_labels = []

        # Run all OvA models independently
        for label_name, clf in self.models_ova.items():
            pred = clf.predict(X_features)[0]
            if pred == 1:
                predicted_labels.append(label_name)

        state["topic"] = predicted_labels  # multi-label output
        return state

'''
if __name__ == "__main__":
    classifier = TopicClassifier()
    state: ClassificationState = {"text": "When do I take my medicine?", "topic": ""}
    result = classifier.classify_text_topic(state)
    print(result)
'''