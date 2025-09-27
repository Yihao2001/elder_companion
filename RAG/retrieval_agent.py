"""
Retrieval Agent Module

Retrieves relevant information from memory storage across different categories:
- Short-term memory: Temporary conversational details
- Long-term memory: Stable traits and preferences
- Healthcare records: Medical information

Usage:
    from retrieval_agent import RetrievalAgent

    agent = RetrievalAgent()
    result = agent.process("What are my allergies?")
"""

import os
import logging
from typing import List, Dict, Optional, TypedDict, Annotated
from datetime import datetime

# Core dependencies
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# LangChain dependencies
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.graph.message import add_messages

# Import embedder
from RAG.embedder import Embedder


class AgentState(TypedDict):
    """State schema for the retrieval agent workflow"""
    user_input: str
    messages: Annotated[List[AnyMessage], add_messages]
    has_context: bool
    final_answer: str
    retrieval_agent_message: AnyMessage


class RetrievalAgent:
    """
    Agent for retrieving relevant information from appropriate memory buckets.

    Attributes:
        elderly_id: Default elderly profile ID to use for retrievals
        graph: Compiled LangGraph workflow
        embedder: Embedder instance for generating embeddings
        engine: SQLAlchemy database engine
    """

    RETRIEVAL_SYSTEM = """
    ## Role  
    You are an Elder Care Companion Conversation History Agent.

    --------------------------------------------------
    OBJECTIVES  
    1. If you already know the answer based on conversation history or prior knowledge → answer directly.
    2. If you need more context → call ONE or MORE retrieval tools to get it.
    3. After tools return, synthesize the answer using ONLY retrieved facts.
    4. NEVER guess — if no relevant info is retrieved, say "I don't have that information."
    5. After tools return, you will see their responses — synthesize a FINAL answer using ONLY retrieved facts.
    6. NEVER call tools again after seeing responses.

    --------------------------------------------------
    BUCKETS → Postgres tables

    1. LONG-TERM (ltm) → retrieve_long_term
    Use for: name, preferences, family, routines, life memories.

    2. HEALTH-CARE (hcm) → retrieve_health
    Use for: meds, allergies, conditions, appointments.

    3. GENERAL / SHORT-TERM → retrieve_short_term
    Use for: today's plans, reminders, temporary preferences.

    --------------------------------------------------
    IMPORTANT:
    - You may call multiple tools if needed.
    - You will see tool responses automatically — no need to wait or route.
    - After tools, generate the final answer in your message content.
    - If no tools called, answer directly.

    --------------------------------------------------
    TOOLS:
    - retrieve_long_term: for stable profile info (name, preferences, family)
    - retrieve_health: for medical info (allergies, meds, conditions)
    - retrieve_short_term: for recent plans, reminders, temporary info
    """

    def __init__(self, elderly_id: str):
        """
        Initialize the Retrieval Agent

        Args:
            elderly_id: UUID of the elderly profile to use for retrievals
        """
        self.elderly_id = elderly_id

        # Load environment variables
        load_dotenv()

        # Initialize database connection
        self._setup_database()

        # Setup embedding model using Embedder class
        self.embedder = Embedder(model_name="google/embeddinggemma-300m")

        # Initialize LLM
        self._setup_llm()

        # Setup tools and workflow
        self._setup_tools()
        self._setup_workflow()

    def _setup_database(self):
        """Setup database connection and engine"""
        self.connection_string = os.getenv("DATABASE_URL")
        self.secret_key = os.getenv("DATABASE_ENCRYPTION_KEY")

        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable is required")
        if not self.secret_key:
            raise ValueError("DATABASE_ENCRYPTION_KEY environment variable is required")

        self.engine = create_engine(
            self.connection_string,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "tcp_user_timeout": 60000,
            },
            echo=False
        )

    def _setup_llm(self):
        """Setup language model"""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            max_output_tokens=1000
        )

    def retrieve_similar_ltm(self, query: str, top_k: int = 5, threshold: float = 0.3) -> List[Dict[str, str]]:
        """Retrieve similar long-term memory items"""
        try:
            embedding = self.embedder.embed(query)
            prefetch = max(50, top_k * 5) if threshold is not None else max(top_k * 2, 20)

            sql = text("""
                WITH nearest AS MATERIALIZED (
                SELECT
                    category,
                    key,
                    value,
                    embedding <=> (:emb)::vector AS distance
                FROM long_term_memory
                WHERE elderly_id = :elderly_id
                ORDER BY distance
                LIMIT :prefetch
                )
                SELECT
                category,
                key,
                value,
                1 - distance AS similarity
                FROM nearest
                {where_clause}
                ORDER BY distance
                LIMIT :top_k;
            """.format(
                where_clause="WHERE 1 - distance >= :threshold" if threshold is not None else ""
            ))

            params = {
                "emb": str(embedding),
                "elderly_id": self.elderly_id,
                "prefetch": int(prefetch),
                "top_k": int(top_k),
            }
            if threshold is not None:
                params["threshold"] = float(threshold)

            with self.engine.connect() as conn:
                rows = conn.execute(sql, params).fetchall()

            return [
                {
                    "category": r.category,
                    "key": r.key,
                    "value": r.value,
                    "similarity": round(float(r.similarity), 4)
                }
                for r in rows
            ]
        except Exception as e:
            logging.warning(f"❌ Failed to retrieve LTM: {str(e)}")
            return []

    def retrieve_similar_stm(self, query: str, top_k: int = 5, threshold: float = 0.3) -> List[Dict[str, str]]:
        """Retrieve similar short-term memory items"""
        try:
            embedding = self.embedder.embed(query)
            prefetch = max(50, top_k * 5) if threshold is not None else max(top_k * 2, 20)

            sql = text("""
                WITH nearest AS MATERIALIZED (
                SELECT
                    content,
                    created_at,
                    embedding <=> (:emb)::vector AS distance
                FROM short_term_memory
                WHERE elderly_id = :elderly_id
                ORDER BY distance
                LIMIT :prefetch
                )
                SELECT
                content,
                created_at,
                1 - distance AS similarity
                FROM nearest
                {where_clause}
                ORDER BY distance
                LIMIT :top_k;
            """.format(
                where_clause="WHERE 1 - distance >= :threshold" if threshold is not None else ""
            ))

            params = {
                "emb": str(embedding),
                "elderly_id": self.elderly_id,
                "prefetch": int(prefetch),
                "top_k": int(top_k),
            }
            if threshold is not None:
                params["threshold"] = float(threshold)

            with self.engine.connect() as conn:
                rows = conn.execute(sql, params).fetchall()

            return [
                {
                    "content": r.content,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "similarity": round(float(r.similarity), 4),
                }
                for r in rows
            ]
        except Exception as e:
            logging.warning(f"❌ Failed to retrieve STM: {str(e)}")
            return []

    def retrieve_similar_health(self, query: str, top_k: int = 5, threshold: float = 0.3) -> List[Dict[str, str]]:
        """Retrieve similar healthcare records"""
        try:
            embedding = self.embedder.embed(query)
            prefetch = max(50, top_k * 5) if threshold is not None else max(top_k * 2, 20)

            sql = text("""
                WITH nearest AS MATERIALIZED (
                SELECT
                    record_type,
                    description,
                    diagnosis_date,
                    embedding <=> (:emb)::vector AS distance
                FROM healthcare_records
                WHERE elderly_id = :elderly_id
                ORDER BY distance
                LIMIT :prefetch
                )
                SELECT
                record_type,
                description,
                diagnosis_date,
                1 - distance AS similarity
                FROM nearest
                {where_clause}
                ORDER BY distance
                LIMIT :top_k;
            """.format(
                where_clause="WHERE 1 - distance >= :threshold" if threshold is not None else ""
            ))

            params = {
                "emb": str(embedding),
                "elderly_id": self.elderly_id,
                "prefetch": int(prefetch),
                "top_k": int(top_k),
            }
            if threshold is not None:
                params["threshold"] = float(threshold)

            with self.engine.connect() as conn:
                rows = conn.execute(sql, params).fetchall()

            return [
                {
                    "record_type": r.record_type,
                    "description": r.description,
                    "diagnosis_date": r.diagnosis_date.isoformat() if r.diagnosis_date else None,
                    "similarity": round(float(r.similarity), 4),
                }
                for r in rows
            ]
        except Exception as e:
            logging.warning(f"❌ Failed to retrieve health records: {str(e)}")
            return []

    def _setup_tools(self):
        """Setup retrieval tools"""
        @tool
        def retrieve_long_term(query: str, top_k: int = 5, threshold: float = 0.1) -> str:
            """Retrieve long-term profile facts (stable traits, preferences, demographics)"""
            results = self.retrieve_similar_ltm(query, top_k, threshold)
            formatted = []
            for r in results:
                formatted.append(f"Category: {r['category']}, Key: {r['key']}, Value: {r['value']}, Similarity: {r['similarity']}")
            return "\n".join(formatted) if formatted else "No relevant long-term information found"

        @tool
        def retrieve_health(query: str, top_k: int = 5, threshold: float = 0.1) -> str:
            """Retrieve health-care data (conditions, meds, allergies, appointments)"""
            results = self.retrieve_similar_health(query, top_k, threshold)
            formatted = []
            for r in results:
                formatted.append(f"Type: {r['record_type']}, Description: {r['description']}, Date: {r['diagnosis_date']}, Similarity: {r['similarity']}")
            return "\n".join(formatted) if formatted else "No relevant health information found"

        @tool
        def retrieve_short_term(query: str, top_k: int = 5, threshold: float = 0.1) -> str:
            """Retrieve short-term conversational details (recent plans, reminders, temporary preferences)"""
            results = self.retrieve_similar_stm(query, top_k, threshold)
            formatted = []
            for r in results:
                formatted.append(f"Content: {r['content']}, Created: {r['created_at']}, Similarity: {r['similarity']}")
            return "\n".join(formatted) if formatted else "No relevant short-term information found"

        self.retrieval_tools = [retrieve_long_term, retrieve_health, retrieve_short_term]

    def _setup_workflow(self):
        """Setup the LangGraph workflow"""
        # Create ReAct agent
        self.react_retrieval_agent = create_react_agent(
            model=self.llm,
            tools=self.retrieval_tools,
        )

        # Setup workflow nodes
        def react_retrieval_node(state: AgentState):
            system = SystemMessage(content=self.RETRIEVAL_SYSTEM)
            input_msg = HumanMessage(content=state["user_input"])
            react_result = self.react_retrieval_agent.invoke({"messages": [system, input_msg]})

            # Pull the final AI answer out of the ReAct messages
            last_ai = next(m for m in reversed(react_result["messages"]) if isinstance(m, AIMessage))

            return {
                "messages": react_result["messages"],
                "retrieval_agent_message": last_ai
            }

        def build_final_template(state: AgentState) -> AgentState:
            """
            Build the final prompt template using retrieved information.
            If a section is empty we write the literal word 'none'.
            """
            tool_msgs = [m for m in state["messages"] if isinstance(m, ToolMessage)]

            # Bucket the raw tool returns
            personal, health, conv = [], [], []
            for tm in tool_msgs:
                if "long_term" in tm.name:
                    personal.append(tm.content)
                elif "health" in tm.name:
                    health.append(tm.content)
                elif "short_term" in tm.name:
                    conv.append(tm.content)

            # Helper: join or fallback
            def sect(data):
                return "\n".join(data) if data else "none"

            template = f"""
            ## System:
            You are Susan, a Non-Ageist Elder Companion Friend — you are warm, respectful, and emotionally intelligent presence designed to provide gentle support and joyful connection to older adults. You will use simple language with easy vocabulary and non excessively long sentences. Be patience, humorous, curiosity, and deep respect. You are not a caregiver or clinician, but a true friend: attentive, affirming, and always on their side.

            ## Guide
            - Speak with gentle clarity, using natural, conversational language. Avoid infantilizing phrases or over-explaining. Assume competence and wisdom. Use humor when appropriate, and always ask before offering help. 
            - You do not give medical advice or make decisions for the user. 
            - You listen, encourage, and empower — never patronize or presume.

            ## User Information and Profile Context:
            {sect(personal)}

            ## User Healthcare Information:
            {sect(health)}

            ## Past Conversational information / History
            {sect(conv)}
            """

            return {"final_answer": template}

        def route_retrieval(state: AgentState):
            """Conditional routing based on tool calls"""
            messages = state.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    return "execute_retrieval"
            return "build_final_template"

        # Create tool node
        retrieval_tool_node = ToolNode(self.retrieval_tools)

        # Build the workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("Retrieval_Agent", react_retrieval_node)
        workflow.add_node("execute_retrieval", retrieval_tool_node)
        workflow.add_node("build_final_template", build_final_template)

        # Add edges
        workflow.add_edge(START, "Retrieval_Agent")

        workflow.add_conditional_edges(
            "Retrieval_Agent",
            route_retrieval,
            {
                "execute_retrieval": "execute_retrieval",
                "build_final_template": "build_final_template"
            }
        )

        workflow.add_edge("execute_retrieval", "build_final_template")
        workflow.add_edge("build_final_template", END)

        # Compile the graph
        self.graph = workflow.compile()

    def process(self, user_input: str) -> dict:
        """
        Process user input and retrieve relevant information

        Args:
            user_input: The user's question or request

        Returns:
            dict: Contains the final answer template and processing information
        """
        try:
            initial_state = {
                "user_input": user_input,
                "messages": [],
                "has_context": False,
                "final_answer": "",
                "retrieval_agent_message": None
            }

            # Process through the workflow
            result = self.graph.invoke(initial_state)

            return {
                "success": True,
                "final_answer": result.get("final_answer", ""),
                "user_input": user_input,
                "messages_count": len(result.get("messages", [])),
                "has_context": bool(result.get("final_answer"))
            }

        except Exception as e:
            logging.error(f"Error processing retrieval request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_input": user_input
            }

    def retrieve_context(self, query: str, categories: Optional[List[str]] = None) -> dict:
        """
        Direct retrieval method for getting context without the full workflow

        Args:
            query: The search query
            categories: List of categories to search in ('ltm', 'stm', 'health')
                       If None, searches all categories

        Returns:
            dict: Retrieved information organized by category
        """
        results = {
            "ltm": [],
            "stm": [],
            "health": []
        }

        try:
            if categories is None:
                categories = ['ltm', 'stm', 'health']

            if 'ltm' in categories:
                results["ltm"] = self.retrieve_similar_ltm(query)

            if 'stm' in categories:
                results["stm"] = self.retrieve_similar_stm(query)

            if 'health' in categories:
                results["health"] = self.retrieve_similar_health(query)

            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": sum(len(v) for v in results.values())
            }

        except Exception as e:
            logging.error(f"Error in direct retrieval: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
