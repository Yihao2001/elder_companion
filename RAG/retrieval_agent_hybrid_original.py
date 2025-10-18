import os
import logging
from typing import List, Dict, Optional, TypedDict, Annotated, Any
from datetime import datetime

# Core dependencies
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# LangChain dependencies
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.graph.message import add_messages

# Import local
from RAG.utils.embedder import Embedder, CrossEmbedder
from RAG.utils.recency_score import compute_recency_score
from RAG.utils.utils import normalize_for_paradedb


class AgentState(TypedDict):
    user_input: str
    messages: Annotated[List[AnyMessage], add_messages]
    has_context: bool
    final_answer: str
    retrieval_agent_message: AnyMessage


class HybridRetrievalAgent:
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
        self.encoder = CrossEmbedder('BAAI/bge-reranker-base')

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

    def _setup_tools(self):
        """Setup retrieval tools"""

        @tool
        def retrieve_long_term(query: str) -> str:
            """Retrieve long-term profile facts (stable traits, preferences, demographics)"""
            results = self.retrieve_rerank(query, mode="long-term")
            formatted = []
            for r in results:
                formatted.append(
                    f"Category: {r['category']}, Key: {r['key']}, Value: {r['value']}"
                )
            print("long term retrieval was made!")
            return "\n".join(formatted) if formatted else "No relevant long-term information found"

        @tool
        def retrieve_health(query: str) -> str:
            """Retrieve health-care data (conditions, meds, allergies, appointments)"""
            results = self.retrieve_rerank(query, mode="healthcare")
            formatted = []
            for r in results:
                formatted.append(
                    f"Type: {r['record_type']}, Description: {r['description']}, Date: {r['diagnosis_date']}"
                )
            print("Health retrieval was made!")
            return "\n".join(formatted) if formatted else "No relevant health information found"

        @tool
        def retrieve_short_term(query: str) -> str:
            """Retrieve short-term conversational details (recent plans, reminders, temporary preferences)"""
            results = self.retrieve_rerank(query, mode="short-term")
            formatted = []
            for r in results:
                formatted.append(
                    f"Content: {r['content']}, Created: {r['created_at']}"
                )
            print("short term retrieval was made!")
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

    def retrieve_hybrid_ltm(self, query: str, top_k_retrieval: int = 5, sim_threshold: float = 0.3,
                            fuzzy_distance: int = 2, alpha_retrieval: float = 0.5):
        try:
            emb = self.embedder.embed(query)

            # --- Embeddings ---
            sql_emb = text(f"""
                WITH nearest AS MATERIALIZED (
                    SELECT id, category, key, value, last_updated, embedding,
                        embedding <=> (:emb)::vector AS distance
                    FROM long_term_memory
                    WHERE elderly_id = :elderly_id
                    ORDER BY distance
                    LIMIT :top_k
                )
                SELECT id, category, key, value, last_updated, embedding, 1 - distance AS similarity
                FROM nearest
                {"WHERE 1 - distance >= :threshold" if sim_threshold is not None else ""}
                ORDER BY distance
                LIMIT :top_k;
            """)
            params_emb = {"emb": str(emb), "elderly_id": self.elderly_id, "top_k": top_k_retrieval}
            if sim_threshold is not None:
                params_emb["threshold"] = sim_threshold

            with self.engine.connect() as conn:
                rows_emb = conn.execute(sql_emb, params_emb).fetchall()

            emb_results = {
                r.id: {
                    "id": r.id,
                    "category": r.category,
                    "key": r.key,
                    "value": r.value,
                    "last_updated": r.last_updated,
                    "embedding": r.embedding,  # ✅ Added
                    "emb_score": float(r.similarity)
                }
                for r in rows_emb
            }

            # --- BM25 ---
            # query = query.replace("'", "''")

            sql_bm25 = text("""
                            SELECT id, category, key, value, last_updated, embedding, paradedb.score(id) AS bm25_score
                            FROM long_term_memory
                            WHERE elderly_id = :elderly_id
                              AND (
                                category_search @@@ :query
                               OR key @@@ :query
                               OR value @@@ :query
                               OR id @@@ paradedb.match('category_search'
                                , :query
                                , distance =
                                > :distance)
                               OR id @@@ paradedb.match('key'
                                , :query
                                , distance =
                                > :distance)
                               OR id @@@ paradedb.match('value'
                                , :query
                                , distance =
                                > :distance)
                                )
                            ORDER BY bm25_score DESC
                                LIMIT :top_k;
                            """)
            params_bm25 = {
                "elderly_id": self.elderly_id,
                "query": normalize_for_paradedb(query),
                "distance": fuzzy_distance,
                "top_k": top_k_retrieval
            }

            with self.engine.connect() as conn:
                rows_bm25 = conn.execute(sql_bm25, params_bm25).fetchall()

            max_bm25 = max((float(r.bm25_score) for r in rows_bm25), default=1.0)
            bm25_results = {
                r.id: {
                    "id": r.id,
                    "category": r.category,
                    "key": r.key,
                    "value": r.value,
                    "last_updated": r.last_updated,
                    "embedding": r.embedding,  # ✅ Added
                    "bm25_score": float(r.bm25_score) / max_bm25
                }
                for r in rows_bm25
            }

            # --- Merge + hybrid ---
            combined = {}
            all_ids = set(emb_results.keys()) | set(bm25_results.keys())

            for id_ in all_ids:
                emb_data = emb_results.get(id_, {
                    "id": id_,
                    "category": "",
                    "key": "",
                    "value": "",
                    "last_updated": None,
                    "embedding": [],  # ✅ Default empty list
                    "emb_score": 0.0
                })
                bm25_data = bm25_results.get(id_, {
                    "id": id_,
                    "category": "",
                    "key": "",
                    "value": "",
                    "last_updated": None,
                    "embedding": [],  # ✅ Default empty list
                    "bm25_score": 0.0
                })

                combined[id_] = {
                    "id": id_,
                    "category": emb_data["category"] or bm25_data["category"],
                    "key": emb_data["key"] or bm25_data["key"],
                    "value": emb_data["value"] or bm25_data["value"],
                    "last_updated": emb_data["last_updated"] or bm25_data["last_updated"],
                    "embedding": emb_data["embedding"] or bm25_data["embedding"],  # ✅ Merge embedding
                    "emb_score": emb_data.get("emb_score", 0.0),
                    "bm25_score": bm25_data.get("bm25_score", 0.0),
                    "hybrid_score": round(
                        alpha_retrieval * bm25_data.get("bm25_score", 0.0) +
                        (1 - alpha_retrieval) * emb_data.get("emb_score", 0.0),
                        4
                    )
                }

            return sorted(combined.values(), key=lambda x: x["hybrid_score"], reverse=True)[:top_k_retrieval]

        except Exception as e:
            logging.warning(f"❌ Failed hybrid LTM retrieval: {str(e)}")
            return []

    def retrieve_hybrid_stm(self, query: str, top_k_retrieval: int = 5, sim_threshold: float = 0.3,
                            fuzzy_distance: int = 2, alpha_retrieval: float = 0.5):
        try:
            emb = self.embedder.embed(query)

            # --- Embeddings ---
            sql_emb = text(f"""
                WITH nearest AS MATERIALIZED (
                    SELECT
                        id, content, created_at, embedding,
                        embedding <=> (:emb)::vector AS distance
                    FROM short_term_memory
                    WHERE elderly_id = :elderly_id
                    ORDER BY distance
                    LIMIT :top_k
                )
                SELECT id, content, created_at, embedding, 1 - distance AS similarity
                FROM nearest
                {"WHERE 1 - distance >= :threshold" if sim_threshold is not None else ""}
                ORDER BY distance
                LIMIT :top_k;
            """)
            params_emb = {"emb": str(emb), "elderly_id": self.elderly_id, "top_k": top_k_retrieval}
            if sim_threshold is not None:
                params_emb["threshold"] = sim_threshold

            with self.engine.connect() as conn:
                rows_emb = conn.execute(sql_emb, params_emb).fetchall()

            emb_results = {
                r.id: {
                    "id": r.id,
                    "content": r.content,
                    "created_at": r.created_at,
                    "embedding": r.embedding,
                    "emb_score": float(r.similarity)
                }
                for r in rows_emb
            }

            # --- BM25 ---
            # query = query.replace("'", "''")

            sql_bm25 = text("""
                            SELECT id, content, created_at, embedding, paradedb.score(id) AS bm25_score
                            FROM short_term_memory
                            WHERE elderly_id = :elderly_id
                              AND (content @@@ :query OR id @@@ paradedb.match('content', :query, distance => :distance))
                            ORDER BY bm25_score DESC LIMIT :top_k;
                            """)
            params_bm25 = {"elderly_id": self.elderly_id, "query": normalize_for_paradedb(query),
                           "distance": fuzzy_distance, "top_k": top_k_retrieval}
            with self.engine.connect() as conn:
                rows_bm25 = conn.execute(sql_bm25, params_bm25).fetchall()

            max_bm25 = max((float(r.bm25_score) for r in rows_bm25), default=1.0)
            bm25_results = {
                r.id: {
                    "id": r.id,
                    "content": r.content,
                    "created_at": r.created_at,
                    "embedding": r.embedding,  # ✅ Added
                    "bm25_score": float(r.bm25_score) / max_bm25
                }
                for r in rows_bm25
            }

            # --- Merge + hybrid ---
            combined = {}
            for id_, r in {**emb_results, **bm25_results}.items():
                emb_score = emb_results.get(id_, {}).get("emb_score", 0.0)
                bm25_score = bm25_results.get(id_, {}).get("bm25_score", 0.0)
                hybrid = alpha_retrieval * bm25_score + (1 - alpha_retrieval) * emb_score
                combined[id_] = {
                    **r,
                    "emb_score": emb_score,
                    "bm25_score": bm25_score,
                    "hybrid_score": round(hybrid, 4)
                }

            return sorted(combined.values(), key=lambda x: x["hybrid_score"], reverse=True)[:top_k_retrieval]

        except Exception as e:
            logging.warning(f"❌ Failed hybrid STM retrieval: {str(e)}")
            return []

    def retrieve_hybrid_hcm(self, query: str, top_k_retrieval: int = 5, sim_threshold: float = 0.3,
                            fuzzy_distance: int = 2, alpha_retrieval: float = 0.5):
        try:
            emb = self.embedder.embed(query)

            # --- Embeddings ---
            sql_emb = text(f"""
                WITH nearest AS MATERIALIZED (
                    SELECT id, record_type, description, diagnosis_date, last_updated, embedding,
                        embedding <=> (:emb)::vector AS distance
                    FROM healthcare_records
                    WHERE elderly_id = :elderly_id
                    ORDER BY distance
                    LIMIT :top_k
                )
                SELECT id, record_type, description, diagnosis_date, last_updated, embedding, 1 - distance AS similarity
                FROM nearest
                {"WHERE 1 - distance >= :threshold" if sim_threshold is not None else ""}
                ORDER BY distance
                LIMIT :top_k;
            """)
            params_emb = {"emb": str(emb), "elderly_id": self.elderly_id, "top_k": top_k_retrieval}
            if sim_threshold is not None:
                params_emb["threshold"] = sim_threshold

            with self.engine.connect() as conn:
                rows_emb = conn.execute(sql_emb, params_emb).fetchall()

            emb_results = {
                r.id: {
                    "id": r.id,
                    "record_type": r.record_type,
                    "description": r.description,
                    "diagnosis_date": r.diagnosis_date.isoformat() if r.diagnosis_date else None,
                    "last_updated": r.last_updated.isoformat() if r.last_updated else None,
                    "embedding": r.embedding,  # ✅ Added
                    "emb_score": float(r.similarity)
                }
                for r in rows_emb
            }

            # --- BM25 ---
            # query = query.replace("'", "''")

            sql_bm25 = text("""
                            SELECT id,
                                   record_type,
                                   description,
                                   diagnosis_date,
                                   last_updated,
                                   embedding,
                                   paradedb.score(id) AS bm25_score
                            FROM healthcare_records
                            WHERE elderly_id = :elderly_id
                              AND (
                                record_type_search @@@ :query OR description @@@ :query
                                OR id @@@ paradedb.match('record_type_search', :query, distance => :distance)
                                OR id @@@ paradedb.match('description', :query, distance => :distance)
                                )
                            ORDER BY bm25_score DESC LIMIT :top_k;
                            """)
            params_bm25 = {
                "elderly_id": self.elderly_id,
                "query": normalize_for_paradedb(query),
                "distance": fuzzy_distance,
                "top_k": top_k_retrieval
            }

            with self.engine.connect() as conn:
                rows_bm25 = conn.execute(sql_bm25, params_bm25).fetchall()

            max_bm25 = max((float(r.bm25_score) for r in rows_bm25), default=1.0)
            bm25_results = {
                r.id: {
                    "id": r.id,
                    "record_type": r.record_type,
                    "description": r.description,
                    "diagnosis_date": r.diagnosis_date.isoformat() if r.diagnosis_date else None,
                    "last_updated": r.last_updated.isoformat() if r.last_updated else None,
                    "embedding": r.embedding,  # ✅ Added
                    "bm25_score": float(r.bm25_score) / max_bm25
                }
                for r in rows_bm25
            }

            # --- Merge + hybrid ---
            combined = {}
            all_ids = set(emb_results.keys()) | set(bm25_results.keys())

            for id_ in all_ids:
                emb_data = emb_results.get(id_, {
                    "id": id_,
                    "record_type": "",
                    "description": "",
                    "diagnosis_date": None,
                    "last_updated": None,
                    "embedding": [],  # ✅ Default empty list
                    "emb_score": 0.0
                })
                bm25_data = bm25_results.get(id_, {
                    "id": id_,
                    "record_type": "",
                    "description": "",
                    "diagnosis_date": None,
                    "last_updated": None,
                    "embedding": [],  # ✅ Default empty list
                    "bm25_score": 0.0
                })

                combined[id_] = {
                    "id": id_,
                    "record_type": emb_data["record_type"] or bm25_data["record_type"],
                    "description": emb_data["description"] or bm25_data["description"],
                    "diagnosis_date": emb_data["diagnosis_date"] or bm25_data["diagnosis_date"],
                    "last_updated": emb_data["last_updated"] or bm25_data["last_updated"],
                    "embedding": emb_data["embedding"] or bm25_data["embedding"],  # ✅ Merge embedding
                    "emb_score": emb_data.get("emb_score", 0.0),
                    "bm25_score": bm25_data.get("bm25_score", 0.0),
                    "hybrid_score": round(
                        alpha_retrieval * bm25_data.get("bm25_score", 0.0) +
                        (1 - alpha_retrieval) * emb_data.get("emb_score", 0.0),
                        4
                    )
                }

            return sorted(combined.values(), key=lambda x: x["hybrid_score"], reverse=True)[:top_k_retrieval]

        except Exception as e:
            logging.warning(f"❌ Failed hybrid health retrieval: {str(e)}")
            return []

    def rerank_with_mmr_and_recency(
            self,
            query: str,
            candidates: List[Dict[str, Any]],
            cross_encoder: CrossEmbedder,
            alpha_MMR: float = 0.7,  # MMR balance: relevance vs diversity
            beta_recency: float = 0.1,  # Small bonus for recency
            top_k_MMR: int = 5,
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        #################################################################
        # --- Extracting relevant metadata about information chunks --- #
        #################################################################

        # ensure recency scores exist (already scaled 0–1)
        candidates = compute_recency_score(candidates, query)

        # extract texts
        texts = []
        for r in candidates:
            text = r.get("content") or r.get("value") or r.get("description")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(
                    "Each result must have one of 'content', 'value', or 'description' as non-empty string.")
            texts.append(text)

        # extract embeddings
        embeddings = []
        for r in candidates:
            emb_str = r.pop("embedding", None)
            emb_list = [float(x) for x in emb_str.strip("[]").split(",")]  # embeddings are saved as strings
            embeddings.append(emb_list)
        embeddings = np.array(embeddings, dtype=np.float32)

        # recency is already normalized [0,1]
        recency_normalized = np.array([r.get("recency_score", 0.0) for r in candidates], dtype=np.float32)

        #################################################################
        # ---               Computing CE Relevance                    --- #
        #################################################################

        # relevance from cross-encoder
        pairs = [[query, text] for text in texts]
        ce_raw_scores = cross_encoder.predict(pairs)

        # normalize cross_encoder scores [0,1]
        min_score, max_score = ce_raw_scores.min(), ce_raw_scores.max()
        if max_score != min_score:
            ce_scores = (ce_raw_scores - min_score) / (max_score - min_score)
        else:
            ce_scores = np.ones_like(ce_raw_scores)

        #################################################################
        # ---                  MMR Greedy Selection                  --- #
        #################################################################
        cos_sim_matrix = cosine_similarity(embeddings)  # Shape: (n, n)
        selected_indices = []
        remaining_indices = list(range(len(candidates)))

        while len(selected_indices) < top_k_MMR and remaining_indices:
            best_score, best_idx = -float("inf"), None

            for idx in remaining_indices:
                ce_score = ce_scores[idx]
                max_sim = max((cos_sim_matrix[idx][s] for s in selected_indices), default=0.0)

                # MMR with recency bias
                mmr_score = alpha_MMR * ce_score - (1 - alpha_MMR) * max_sim
                mmr_score += beta_recency * recency_normalized[idx]

                if mmr_score > best_score:
                    best_score, best_idx = mmr_score, idx

            if best_idx is None:
                break

            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)

        #################################################################
        # ---             Reorder results and add metadata           ---#
        #################################################################
        ranked_results = [candidates[i] for i in selected_indices]

        for i, result in enumerate(ranked_results):
            idx = selected_indices[i]
            result["cross_encoder_score"] = float(ce_scores[idx])
            result["recency_score"] = float(recency_normalized[idx])
            result["mmr_score"] = float(
                alpha_MMR * ce_scores[idx]
                - (1 - alpha_MMR) * max((cos_sim_matrix[idx][selected_indices[j]] for j in range(i)), default=0.0)
                + beta_recency * recency_normalized[idx]
            )

        return ranked_results

    def retrieve_rerank(
            self,
            query: str,
            mode: str = "long-term",  # Options: "short-term", "long-term", "healthcare"
            top_k_retrieval: int = 25,
            sim_threshold: float = 0.3,
            fuzzy_distance: int = 2,
            alpha_retrieval: float = 0.5,
            cross_encoder: Optional[CrossEmbedder] = None,
            alpha_MMR: float = 0.75,
            beta_recency: float = 0.1,
            top_k_MMR: int = 8
    ) -> List[Dict[str, Any]]:

        # Initialize default cross-encoder if not provided
        if cross_encoder is None:
            cross_encoder = CrossEmbedder('BAAI/bge-reranker-base')

        # Step 1: Retrieve candidates based on mode
        if mode == "short-term":
            candidates = self.retrieve_hybrid_stm(
                query=query,
                top_k_retrieval=top_k_retrieval,
                sim_threshold=sim_threshold,
                fuzzy_distance=fuzzy_distance,
                alpha_retrieval=alpha_retrieval
            )
        elif mode == "long-term":
            candidates = self.retrieve_hybrid_ltm(
                query=query,
                top_k_retrieval=top_k_retrieval,
                sim_threshold=sim_threshold,
                fuzzy_distance=fuzzy_distance,
                alpha_retrieval=alpha_retrieval
            )
        elif mode == "healthcare":
            candidates = self.retrieve_hybrid_hcm(
                query=query,
                top_k_retrieval=top_k_retrieval,
                sim_threshold=sim_threshold,
                fuzzy_distance=fuzzy_distance,
                alpha_retrieval=alpha_retrieval
            )
        else:
            raise ValueError(f"Unsupported mode: {mode}. Choose from 'stm', 'ltm', or 'hcm'.")

        # Step 2: Rerank with MMR + recency (assumes candidates have needed fields like 'text', 'timestamp')
        reranked_results = self.rerank_with_mmr_and_recency(
            query=query,
            candidates=candidates,
            cross_encoder=cross_encoder,
            alpha_MMR=alpha_MMR,
            beta_recency=beta_recency,
            top_k_MMR=top_k_MMR
        )

        # Step 3: Remove internal score keys
        score_keys = {
            'emb_score',
            'bm25_score',
            'hybrid_score',
            'recency_score',
            'cross_encoder_score',
            'mmr_score'
        }

        clean_results = [
            {k: v for k, v in result.items() if k not in score_keys}
            for result in reranked_results
        ]

        return clean_results

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
                results["ltm"] = self.retrieve_rerank(query, mode="long-term")

            if 'stm' in categories:
                results["stm"] = self.retrieve_rerank(query, mode="short-term")

            if 'health' in categories:
                results["health"] = self.retrieve_rerank(query, mode="healthcare")

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