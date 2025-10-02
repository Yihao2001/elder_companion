"""
Insertion Agent Module

Converts user input into structured memory storage across different categories:
- Short-term memory: Temporary conversational details
- Long-term memory: Stable traits and preferences
- Healthcare records: Medical information

Usage:
    from insertion_agent import InsertionAgent

    agent = InsertionAgent()
    result = agent.process("I live at 123 Main Street")
"""

import os
import logging
from typing import List, Optional, TypedDict, Annotated
from enum import Enum
from datetime import datetime

# Core dependencies
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field

# LangChain dependencies
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.graph.message import add_messages

# Import embedder
from RAG.embedder import Embedder

from RAG.shared.schemas.schema_stm import InsertShortTermSchema
from RAG.shared.schemas.schema_ltm import InsertLongTermSchema, LTMCategories
from RAG.shared.schemas.schema_hcm import InsertHealthSchema, HealthRecordTypes


class AgentState(TypedDict):
    """State schema for the insertion agent workflow"""
    user_input: str
    messages: Annotated[List[AnyMessage], add_messages]
    has_context: bool
    final_answer: str
    insertion_agent_message: AnyMessage


class InsertionAgent:
    """
    Agent for processing user input and storing relevant information in appropriate memory buckets.

    Attributes:
        elderly_id: Default elderly profile ID to use for insertions
        graph: Compiled LangGraph workflow
        embedder: Embedder instance for generating embeddings
        engine: SQLAlchemy database engine
    """

    INSERTION_SYSTEM = """
    ## Role  
    You are memory agent involved in deciding what information is important to store and in the right place. Only store what is neccessary.
    If you decide to store information, Long-Term and Healthcare are for official and formal information, general miscellaneous and all other information should be stored in short term
    
    --------------------------------------------------
    OBJECTIVES  
    1. Extract ONLY relevant user information from the conversation.  
    2. Decide if any item is worth storing.  
    3. If YES → store all relevant information by calling the matching tool(s).  
    4. If NO → do nothing (silent pass).

    --------------------------------------------------
    BUCKETS 

    1. LONG-TERM (ltm)  
    Content: stable traits & preferences that rarely change, generally fixed profile information
    Examples:  
    - name, preferred_name, date_of_birth, gender, address  
    - food/activity/music/hobby preferences (category + value)  
    - family & social relationships (contact_name, relationship_type, is_emergency_contact)  
    - life memories (memory_title, memory_content, memory_category)  
    - daily routines (routine_name, time_of_day, frequency)

    2. HEALTH-CARE (hcm)  
    Tables: Official medical_records, medications, medical_conditions, allergies, diagnosis  
    Content: physical/mental health info explicitly shared for future care
    Examples:  
    - diagnoses, lab results, vital signs (medical_records)  
    - medication_name, dosage, frequency (medications)  
    - condition_name, severity, status (medical_conditions)  
    - allergen, reaction_type (allergies)
    - official tied medical facility (polyclinics, hospitals, family clinics, general practioners)

    3. GENERAL / SHORT-TERM  
    Tables: memory_contexts (context_summary)  
    Content: conversational details useful in the near future
    Examples:  
    - "I have a cardiology visit next Tuesday"  
    - "Please remind me to call my grandson tonight"  
    - "I prefer chicken for dinner today"

    --------------------------------------------------
    RULES  
    - You may call multiple tools in one go if needed.
    - Only store what's explicitly shared and matches a bucket.
    """

    def __init__(self, elderly_id: str):
        """
        Initialize the Insertion Agent

        Args:
            elderly_id: UUID of the elderly profile to use for insertions
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

        # Ensure elderly profile exists
        self._ensure_elderly_profile()

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

    def insert_elderly_profile(self, profile_data:dict, elderly_id:str=None):
        """Insert a new elderly profile into the database"""
        if elderly_id is None:
            elderly_id = self.elderly_id

        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                                INSERT INTO elderly_profile
                                (id, name, date_of_birth, gender, nationality, dialect_group, marital_status, address)
                                VALUES (%s, pgp_sym_encrypt(%s, %s), pgp_sym_encrypt(%s, %s), %s,
                                        pgp_sym_encrypt(%s, %s), pgp_sym_encrypt(%s, %s), %s,
                                        pgp_sym_encrypt(%s, %s)) ON CONFLICT (id) DO NOTHING;
                                """, (
                                    elderly_id,
                                    profile_data["name"], self.secret_key,
                                    profile_data["date_of_birth"], self.secret_key,
                                    profile_data["gender"],
                                    profile_data["nationality"], self.secret_key,
                                    profile_data["dialect_group"], self.secret_key,
                                    profile_data["marital_status"],
                                    profile_data["address"], self.secret_key
                                ))
        except Exception as e:
            logging.warning(f"Could not ensure elderly profile: {e}")


    def _ensure_elderly_profile(self):
        default_elderly_id = "12345678-1234-1234-1234-012345678910"
        """Ensure the elderly profile exists in the database"""
        profile_data = {
            "name": "Admiralty Bedok Canberra Tan",
            "date_of_birth": "1965-01-01",
            "gender": "Male",
            "nationality": "Singaporean",
            "dialect_group": "Hokkien",
            "marital_status": "Married",
            "address": "38 Oxley Road, Singapore 238629"
        }

        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO elderly_profile 
                        (id, name, date_of_birth, gender, nationality, dialect_group, marital_status, address)
                        VALUES (%s, pgp_sym_encrypt(%s,%s), pgp_sym_encrypt(%s,%s), %s, 
                                pgp_sym_encrypt(%s,%s), pgp_sym_encrypt(%s,%s), %s, pgp_sym_encrypt(%s,%s))
                        ON CONFLICT (id) DO NOTHING;
                    """, (
                        default_elderly_id,
                        profile_data["name"], self.secret_key,
                        profile_data["date_of_birth"], self.secret_key,
                        profile_data["gender"],
                        profile_data["nationality"], self.secret_key,
                        profile_data["dialect_group"], self.secret_key,
                        profile_data["marital_status"],
                        profile_data["address"], self.secret_key
                    ))
        except Exception as e:
            logging.warning(f"Could not ensure elderly profile: {e}")

    def manual_insert_short_term(self, content: str, timestamp: str = None, elderly_id: str = None) -> dict:
        """Manual insertion of short-term memory item with fine-grained control over insertion timing etc.
        This method is solely used for testing and debugging purposes and not to be used in production.

        Args:
            content: The content to store
            timestamp: Custom timestamp in ISO format (YYYY-MM-DDTHH:MM:SS) or None for current time
            elderly_id: Elderly profile ID or None to use default
        """
        if elderly_id is None:
            elderly_id = self.elderly_id

        # Parse and validate timestamp
        if timestamp is None:
            created_at = datetime.utcnow()
        else:
            try:
                # Parse the timestamp string to datetime object
                created_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError as e:
                return {"success": False, "error": f"Invalid timestamp format: {str(e)}. Use ISO format like '2024-01-15T10:30:00'"}

        if not content or not content.strip():
            return {"success": False, "error": "content is required and cannot be empty."}

        # Use embedder instance instead of local embedding function
        embedding = self.embedder.embed(content)

        try:
            with self.engine.connect() as conn:
                query = text("""
                             INSERT INTO short_term_memory (elderly_id, content, embedding, created_at)
                             VALUES (:elderly_id, :content, :embedding, :created_at) RETURNING id, created_at;
                             """)
                result = conn.execute(query, {
                    "elderly_id": elderly_id.strip(),
                    "content": content.strip(),
                    "embedding": str(embedding),
                    "created_at": created_at
                }).fetchone()
                conn.commit()

                return {
                    "success": True,
                    "message": "Short-term memory stored successfully",
                    "record_id": str(result.id),
                    "created_at": result.created_at.isoformat() if result.created_at else None,
                    "embedding_provided": embedding is not None
                }

        except SQLAlchemyError as e:
            logging.error(f"❌ Database error inserting STM: {str(e)}")
            return {"success": False, "error": f"Database error: {str(e)}"}
        except Exception as e:
            logging.error(f"Unexpected error inserting STM: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def insert_short_term(self, content: str, elderly_id: str = None) -> dict:
        """Insert short-term memory item"""
        if elderly_id is None:
            elderly_id = self.elderly_id

        if not content or not content.strip():
            return {"success": False, "error": "content is required and cannot be empty."}

        # Use embedder instance instead of local embedding function
        embedding = self.embedder.embed(content)

        try:
            with self.engine.connect() as conn:
                query = text("""
                    INSERT INTO short_term_memory (
                        elderly_id, content, embedding
                    ) VALUES (
                        :elderly_id, :content, :embedding
                    )
                    RETURNING id, created_at;
                """)
                result = conn.execute(query, {
                    "elderly_id": elderly_id.strip(),
                    "content": content.strip(),
                    "embedding": str(embedding)
                }).fetchone()
                conn.commit()

                return {
                    "success": True,
                    "message": "Short-term memory stored successfully",
                    "record_id": str(result.id),
                    "created_at": result.created_at.isoformat() if result.created_at else None,
                    "embedding_provided": embedding is not None
                }

        except SQLAlchemyError as e:
            logging.error(f"❌ Database error inserting STM: {str(e)}")
            return {"success": False, "error": f"Database error: {str(e)}"}
        except Exception as e:
            logging.error(f"Unexpected error inserting STM: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def insert_long_term(self, category: str, key: str, value: str, elderly_id: str = None) -> dict:
        """Insert long-term memory item"""
        if elderly_id is None:
            elderly_id = self.elderly_id

        if not category or not category.strip():
            return {"success": False, "error": "category is required and cannot be empty."}
        if not key or not key.strip():
            return {"success": False, "error": "key is required and cannot be empty."}
        if not value or not value.strip():
            return {"success": False, "error": "value is required and cannot be empty."}

        # Use embedder instance instead of local embedding function
        embedding = self.embedder.embed(value)

        try:
            with self.engine.connect() as conn:
                query = text("""
                    INSERT INTO long_term_memory (
                        elderly_id, category, key, value, embedding
                    ) VALUES (
                        :elderly_id, :category, :key, :value, :embedding
                    )
                    RETURNING id, last_updated;
                """)
                result = conn.execute(query, {
                    "elderly_id": elderly_id.strip(),
                    "category": category.strip(),
                    "key": key.strip(),
                    "value": value.strip(),
                    "embedding": str(embedding)
                }).fetchone()
                conn.commit()

                return {
                    "success": True,
                    "message": "Long-term memory stored successfully",
                    "record_id": str(result.id),
                    "last_updated": result.last_updated.isoformat() if result.last_updated else None,
                    "embedding_provided": embedding is not None
                }

        except SQLAlchemyError as e:
            logging.error(f"❌ Database error inserting LTM: {str(e)}")
            return {"success": False, "error": f"Database error: {str(e)}"}
        except Exception as e:
            logging.error(f"Unexpected error inserting LTM: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def insert_health_record(self, record_type: str, description: str, diagnosis_date: Optional[str] = None, elderly_id: str = None) -> dict:
        """Insert healthcare record"""
        if elderly_id is None:
            elderly_id = self.elderly_id

        if not record_type or not record_type.strip():
            return {"success": False, "error": "record_type is required and cannot be empty."}
        if not description or not description.strip():
            return {"success": False, "error": "description is required and cannot be empty."}

        # Validate date format if provided
        if diagnosis_date:
            try:
                datetime.strptime(diagnosis_date, "%Y-%m-%d")
            except ValueError:
                return {"success": False, "error": "diagnosis_date must be in YYYY-MM-DD format if provided."}

        # Use embedder instance instead of local embedding function
        embedding = self.embedder.embed(description)

        try:
            with self.engine.connect() as conn:
                query = text("""
                    INSERT INTO healthcare_records (
                        elderly_id, record_type, description, diagnosis_date, embedding
                    ) VALUES (
                        :elderly_id, :record_type, :description, :diagnosis_date, :embedding
                    )
                    RETURNING id, last_updated;
                """)
                result = conn.execute(query, {
                    "elderly_id": elderly_id.strip(),
                    "record_type": record_type.strip(),
                    "description": description.strip(),
                    "diagnosis_date": diagnosis_date if diagnosis_date else None,
                    "embedding": str(embedding) if embedding else None
                }).fetchone()
                conn.commit()

                return {
                    "success": True,
                    "message": "Healthcare record stored successfully",
                    "record_id": str(result.id),
                    "last_updated": result.last_updated.isoformat() if result.last_updated else None,
                    "embedding_provided": embedding is not None,
                    "diagnosis_date": diagnosis_date
                }

        except SQLAlchemyError as e:
            logging.error(f"❌ Database error inserting health record: {str(e)}")
            return {"success": False, "error": f"Database error: {str(e)}"}
        except Exception as e:
            logging.error(f"Unexpected error inserting health record: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def _setup_tools(self):
        """Setup LangChain tools for the insertion functions"""

        @tool(args_schema=InsertShortTermSchema)
        def insert_short_term_tool(content: str) -> str:
            """Insert a short-term memory item."""
            result = self.insert_short_term(content=content)
            return str(result)

        @tool(args_schema=InsertLongTermSchema)
        def insert_long_term_tool(category: LTMCategories, key: str, value: str) -> str:
            """Insert a long-term memory fact (stable traits, demographics, preferences)."""
            result = self.insert_long_term(category=category, key=key, value=value)
            return str(result)

        @tool(args_schema=InsertHealthSchema)
        def insert_health_tool(record_type: HealthRecordTypes, description: str, diagnosis_date: Optional[str] = None) -> str:
            """Insert a healthcare record (conditions, medications, appointments)."""
            result = self.insert_health_record(record_type=record_type, description=description, diagnosis_date=diagnosis_date)
            return str(result)
        self.insertion_tools = [insert_long_term_tool, insert_health_tool, insert_short_term_tool]

        self.insertion_tools = [insert_short_term_tool]
        self.react_insertion_agent = create_react_agent(
            model=self.llm,
            tools=self.insertion_tools
        )

    def _setup_workflow(self):
        """Setup the LangGraph workflow"""

        def react_insertion_node(state: AgentState):
            system = SystemMessage(content=self.INSERTION_SYSTEM)
            input_msg = HumanMessage(content=state["user_input"])
            react_result = self.react_insertion_agent.invoke({"messages": [system, input_msg]})

            last_ai = next(m for m in reversed(react_result["messages"]) if isinstance(m, AIMessage))

            return {
                "messages": react_result["messages"],
                "insertion_agent_message": last_ai
            }

        def route_insertion(state: AgentState):
            messages = state.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    return "execute_insertion"
            return "end"

        # Create workflow
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("Insertion_Agent", react_insertion_node)
        workflow.add_node("execute_insertion", ToolNode(self.insertion_tools))

        # Add edges
        workflow.add_edge(START, "Insertion_Agent")
        workflow.add_conditional_edges(
            "Insertion_Agent",
            route_insertion,
            {
                "execute_insertion": "execute_insertion",
                "end": END,
            }
        )
        workflow.add_edge("execute_insertion", END)

        # Compile graph
        self.graph = workflow.compile()

    def process(self, user_input: str) -> dict:
        """
        Process user input and store relevant information in appropriate memory buckets.

        Args:
            user_input: The user's input text to process

        Returns:
            dict: Result containing processing information and any stored data
        """
        initial_state = {
            "user_input": user_input,
            "messages": [],
            "final_answer": "",
            "insertion_agent_message": None,
            "has_context": False
        }

        try:
            result = self.graph.invoke(initial_state)

            # Extract tool call results from messages
            tool_results = []
            for message in result.get("messages", []):
                if hasattr(message, 'content') and message.content and "success" in str(message.content):
                    try:
                        # Parse the string representation back to dict
                        import ast
                        tool_result = ast.literal_eval(message.content)
                        if isinstance(tool_result, dict):
                            tool_results.append(tool_result)
                    except:
                        pass

            return {
                "success": True,
                "user_input": user_input,
                "tool_results": tool_results,
                "message_count": len(result.get("messages", [])),
                "processed": len(tool_results) > 0
            }

        except Exception as e:
            logging.error(f"Error processing user input: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_input": user_input
            }



# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = InsertionAgent()

    # Process some user input
    result = agent.process("I live at 123 Main Street and I have diabetes")
    print("Processing result:", result)
