from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableLambda
from typing import TypedDict, Literal, Optional
from qa_classifier_class import QAClassifier
from topic_classifier_class import TopicClassifier
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
import os, re
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

gemini_client = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_output_tokens=1000,
    api_key=api_key
)

# Unified state definition
class ClassificationState(TypedDict):
    text: str
    flow_type: Literal["online", "offline"]
    qa: Optional[str]
    topic: Optional[str]


# Define nodes
qa_model = QAClassifier()
topic_model = TopicClassifier()

def qa_node(state: ClassificationState) -> ClassificationState:
    """Run offline QA classifier."""
    result = qa_model.classify_text_qa({"text": state["text"], "qa": state.get("qa", "")})
    state["qa"] = result["qa"]
    return state

def topic_node(state: ClassificationState) -> ClassificationState:
    """Run offline topic classifier."""
    result = topic_model.classify_text_topic({"text": state["text"], "topic": state.get("topic", "")})
    state["topic"] = result["topic"]
    return state

def llm_node(state: ClassificationState) -> ClassificationState:
    prompt = (
        f"Classify the following text into topic "
        f"(healthcare, long term, short term) and QA type (question/answer). "
        f"Reply ONLY in the format: topic: ..., qa: ...\n\n{state['text']}"
    )
    llm_response = gemini_client.invoke([HumanMessage(content=prompt)])
    content = llm_response.content

    topic_match = re.search(r"topic\s*:\s*(\w+)", content, re.IGNORECASE)
    qa_match = re.search(r"qa\s*:\s*(\w+)", content, re.IGNORECASE)

    state["topic"] = topic_match.group(1) if topic_match else "unknown"
    state["qa"] = qa_match.group(1) if qa_match else "unknown"
    return state


# Build LangGraph
graph = StateGraph(ClassificationState)

graph.add_node("QAClassifier", qa_node)
graph.add_node("TopicClassifier", topic_node)
graph.add_node("LLMClassifier", llm_node)


# Conditional branch from START
def choose_flow(state: ClassificationState):
    if state["flow_type"] == "online":
        return "LLMClassifier"
    elif state["flow_type"] == "offline":
        return "QAClassifier"
    else:
        raise ValueError(f"Invalid flow_type, please select offline or online: {state['flow_type']}")


graph.add_conditional_edges(
    START,
    choose_flow,
    {
        "LLMClassifier": "LLMClassifier",
        "QAClassifier": "QAClassifier"
    }
)

# Offline flow chain
graph.add_edge("QAClassifier", "TopicClassifier")
graph.add_edge("TopicClassifier", END)

# LLM flow ends directly
graph.add_edge("LLMClassifier", END)

# Compile
app = graph.compile()