import os
from dotenv import load_dotenv
from typing import List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI

from module_2.qa_classifier_class import QAClassifier
from module_2.topic_classifier_class import TopicClassifier
from module_2.states import ClassificationState
from module_3.utils.logger import logger 

# ---------- MODELS ----------
qa_model = QAClassifier()
topic_model = TopicClassifier()


# ---------- NODES ----------
def qa_node(state: ClassificationState) -> Dict[str, Any]:
    """Run QA classifier."""
    logger.info("Running QA node")
    result = qa_model.classify_text_qa({
        "text": state["text"],
        "qa": state.get("qa", "")
    })
    logger.info("QA node successful")
    return {"qa": result["qa"]}


def topic_node(state: ClassificationState) -> Dict[str, Any]:
    """Run topic classifier."""
    logger.info("Running topic node")
    result = topic_model.classify_text_topic({
        "text": state["text"],
        "topic": state.get("topic", [])
    })
    topics = result.get("topic") or ["short-term"]
    logger.info("Topic node successful")
    return {"topic": topics}


def finalize_node(state: ClassificationState) -> Dict[str, Any]:
    """Combine final results."""
    qa = state.get("qa", "unknown")
    topics = state.get("topic", [])
    logger.info(f"✅ Finalized output → QA: {qa} | Topics: {topics}")
    return {"qa": qa, "topic": topics}


# ---------- BUILD GRAPH ----------
def build_classification_graph():
    graph = StateGraph(ClassificationState)

    graph.add_node("QAClassifier", qa_node)
    graph.add_node("TopicClassifier", topic_node)
    graph.add_node("Finalize", finalize_node)

    # Conditional routing from START
    def choose_flow(state: ClassificationState):
        if state["flow_type"] == "online":
            return "END"  # Skip everything
        elif state["flow_type"] == "offline":
            # Run both classifiers concurrently
            return ["QAClassifier", "TopicClassifier"]
        else:
            raise ValueError(f"Invalid flow_type: {state['flow_type']}")

    graph.add_conditional_edges(
        START,
        choose_flow,
        {
            "END": END,
            "QAClassifier": "QAClassifier",
            "TopicClassifier": "TopicClassifier",
        },
    )

    # Fan-in to Finalize, then END
    graph.add_edge("QAClassifier", "Finalize")
    graph.add_edge("TopicClassifier", "Finalize")
    graph.add_edge("Finalize", END)

    return graph.compile()


# # ---------- VISUALIZATION ----------
# def save_mermaid_graph(as_png: bool = True):
#     compiled_graph = build_classification_graph()
#     gviz = compiled_graph.get_graph()

#     try:
#         png_bytes = gviz.draw_mermaid_png()
#         with open("module_2/assets/classification_graph.png", "wb") as f:
#             f.write(png_bytes)
#         print("🖼️ Saved: classification_graph.png")
#     except Exception as e:
#         print(f"⚠️ Could not save graph PNG: {e}")
#         print("Please ensure Graphviz is installed for PNG generation.")
#
#
# # ---------- TEST EXECUTION ----------
# if __name__ == "__main__":
#     graph = build_classification_graph()
#     print("✅ Classification graph built successfully.")
#     save_mermaid_graph(as_png=True)

#     print("\n🚀 Running test flows...\n")

#     # --- Test offline flow (parallel QA + Topic) ---
#     offline_state = {
#         "text": "What are the long-term effects of daily exercise?",
#         "flow_type": "offline",
#         "qa": "",
#         "topic": []
#     }
#     result_offline = graph.invoke(offline_state)
#     print("\n🧩 Offline Flow Result:", result_offline)

#     # --- Test online flow (skip everything) ---
#     online_state = {
#         "text": "Is this a test input?",
#         "flow_type": "online",
#         "qa": "",
#         "topic": []
#     }
#     result_online = graph.invoke(online_state)
#     print("\n🧩 Online Flow Result:", result_online)