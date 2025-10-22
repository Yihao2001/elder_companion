import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import TypedDict, Literal, Optional, List

from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

from module_2.qa_classifier_class import QAClassifier
from module_2.topic_classifier_class import TopicClassifier


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
    topic: Optional[List[str]]  # now multi-label

# Define nodes
qa_model = QAClassifier()
topic_model = TopicClassifier()

def qa_node(state: ClassificationState) -> ClassificationState:
    """Run offline QA classifier."""
    result = qa_model.classify_text_qa({
        "text": state["text"],
        "qa": state.get("qa", "")
    })
    state["qa"] = result["qa"]
    return state

def topic_node(state: ClassificationState) -> ClassificationState:
    """Run offline topic classifier (multi-label)."""
    result = topic_model.classify_text_topic({
        "text": state["text"],
        "topic": state.get("topic", [])
    })
    topics = result.get("topic") or []
    if not topics:
        topics = ["short-term"]
    
    state["topic"] = topics
    return state

class ClassificationResult(BaseModel):
    topic: List[str]
    qa: str

def llm_node(state: ClassificationState) -> ClassificationState:
    prompt = (
        f"Classify the following text into topic(s) and QA type.\n\n"
        f"Text: {state['text']}\n\n"
        f"Output must be valid JSON in this format:\n"
        f'{{"topic": ["healthcare", "long-term"], "qa": "question"}}\n'
        f"Allowed topics: healthcare, long-term, short-term. QA type: question or statement.\n"
        f"Reply ONLY with JSON, no extra text or Markdown."
    )
    
    llm_response = gemini_client.invoke([HumanMessage(content=prompt)])
    content = llm_response.content.strip()

    # Remove triple backticks if present
    if content.startswith("```") and content.endswith("```"):
        content = "\n".join(content.splitlines()[1:-1]).strip()

    # Parse JSON directly into Pydantic model
    try:
        result = ClassificationResult.parse_raw(content)
    except Exception as e:
        print("LLM output parsing failed, using defaults:", repr(content))
        result = ClassificationResult(topic=["short-term"], qa="unknown")

    # Update state
    state["topic"] = result.topic
    state["qa"] = result.qa

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
