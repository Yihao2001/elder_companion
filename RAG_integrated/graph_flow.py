# graph_builder.py
from langgraph.graph import StateGraph, START, END
from langchain.schema import HumanMessage
import re

def build_memory_graph(context):
    """
    DAG for classification → retrieval → (optional insertion)
    """
    qa_model = context.qa_classifier
    topic_model = context.topic_classifier
    llm = context.llm_online
    engine = context.db_engine
    embedder = context.embedder
    cross_encoder = context.cross_encoder

    # --- NODES ---

    def qa_node(state):
        state = qa_model.classify_text_qa(state)
        return state

    def topic_node(state):
        state = topic_model.classify_text_topic(state)
        return state

    def llm_node(state):
        prompt = (
            f"Classify this text into topic (healthcare, long term, short term) "
            f"and QA type (question/statement). Reply ONLY in format: topic: ..., qa: ...\n\n{state['text']}"
        )
        llm_response = llm.invoke([HumanMessage(content=prompt)])
        content = llm_response.content
        topic_match = re.search(r"topic\s*:\s*(\w+)", content, re.IGNORECASE)
        qa_match = re.search(r"qa\s*:\s*(\w+)", content, re.IGNORECASE)
        state["topic"] = topic_match.group(1) if topic_match else "unknown"
        state["qa"] = qa_match.group(1) if qa_match else "unknown"
        return state

    def retrieval_node(state):
        """Retrieve relevant memories based on topic."""
        mode = (
            "healthcare" if state["topic"] == "healthcare"
            else "long-term" if state["topic"] == "longterm"
            else "short-term"
        )
        results = context.retrieve_rerank(
            engine=engine,
            elderly_id=state.get("elderly_id"),
            query=state["text"],
            mode=mode,
            embedder=embedder,
            cross_encoder=cross_encoder
        )
        state["retrieval_results"] = results
        return state

    def insertion_node(state):
        """Insert short-term memory for all statements."""
        result = context.insert_short_term(
            engine,
            content=state["text"],
            elderly_id=state.get("elderly_id"),
            embedder=embedder
        )
        state["insert_result"] = result
        return state

    # --- GRAPH STRUCTURE ---

    graph = StateGraph(dict)
    graph.add_node("QAClassifier", qa_node)
    graph.add_node("TopicClassifier", topic_node)
    graph.add_node("LLMClassifier", llm_node)
    graph.add_node("Retriever", retrieval_node)
    graph.add_node("Inserter", insertion_node)

    def choose_flow(state):
        if state["flow_type"] == "online":
            return "LLMClassifier"
        return "QAClassifier"

    def branch_on_qa(state):
        if state["qa"] == "question":
            return "Retriever"
        return "Retriever+Insert"

    graph.add_conditional_edges(START, choose_flow, {
        "LLMClassifier": "LLMClassifier",
        "QAClassifier": "QAClassifier"
    })

    # Offline branch → classify → decide retrieval/insertion
    graph.add_edge("QAClassifier", "TopicClassifier")
    graph.add_conditional_edges("TopicClassifier", branch_on_qa, {
        "Retriever": "Retriever",
        "Retriever+Insert": "Retriever",
    })
    graph.add_edge("Retriever", "Inserter")
    graph.add_edge("Inserter", END)

    # Online branch → LLM direct → retrieval (optional insert)
    graph.add_edge("LLMClassifier", "Retriever")
    graph.add_edge("Retriever", "Inserter")
    graph.add_edge("Inserter", END)

    return graph.compile()
