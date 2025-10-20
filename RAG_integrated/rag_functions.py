import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, text
from typing import List, Dict, Optional, Any
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine, text
from utils.utils import normalize_for_paradedb
from utils.embedder import Embedder, CrossEmbedder
from utils.recency_score import compute_recency_score


def insert_short_term(engine, content: str, elderly_id: str, embedder=Embedder) -> dict:
    """Insert short-term memory item"""
    if elderly_id is None:
        raise ValueError("elderly_id is required and cannot be None.")

    if not content or not content.strip():
        return {"success": False, "error": "content is required and cannot be empty."}

    embedding = embedder.embed(content)

    try:
        with engine.connect() as conn:
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

            # Log successful insertion
            logging.info(
                f"✅ Successfully inserted short-term memory for elderly_id={elderly_id}, record_id={result.id}"
            )

    except SQLAlchemyError as e:
        logging.error(f"❌ Database error inserting STM: {str(e)}")
        return {"success": False, "error": f"Database error: {str(e)}"}
    except Exception as e:
        logging.error(f"Unexpected error inserting STM: {str(e)}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
    


# def insert_long_term(engine, category: str, key: str, value: str, elderly_id: str, embedder=Embedder) -> dict:
#     """Insert long-term memory item"""
#     if elderly_id is None:
#         raise ValueError("elderly_id is required and cannot be None.")

#     if not category or not category.strip():
#         return {"success": False, "error": "category is required and cannot be empty."}
#     if not key or not key.strip():
#         return {"success": False, "error": "key is required and cannot be empty."}
#     if not value or not value.strip():
#         return {"success": False, "error": "value is required and cannot be empty."}

#     # Use embedder instance instead of local embedding function
#     embedding = embedder.embed(value)

#     try:
#         with engine.connect() as conn:
#             query = text("""
#                 INSERT INTO long_term_memory (
#                     elderly_id, category, key, value, embedding
#                 ) VALUES (
#                     :elderly_id, :category, :key, :value, :embedding
#                 )
#                 RETURNING id, last_updated;
#             """)
#             result = conn.execute(query, {
#                 "elderly_id": elderly_id.strip(),
#                 "category": category.strip(),
#                 "key": key.strip(),
#                 "value": value.strip(),
#                 "embedding": str(embedding)
#             }).fetchone()
#             conn.commit()

#             return {
#                 "success": True,
#                 "message": "Long-term memory stored successfully",
#                 "record_id": str(result.id),
#                 "last_updated": result.last_updated.isoformat() if result.last_updated else None,
#                 "embedding_provided": embedding is not None
#             }

#     except SQLAlchemyError as e:
#         logging.error(f"❌ Database error inserting LTM: {str(e)}")
#         return {"success": False, "error": f"Database error: {str(e)}"}
#     except Exception as e:
#         logging.error(f"Unexpected error inserting LTM: {str(e)}")
#         return {"success": False, "error": f"Unexpected error: {str(e)}"}



# def insert_health_record(engine, record_type: str, description: str, elderly_id: str, embedder: Embedder, diagnosis_date: Optional[str] = None, ) -> dict:
#     """Insert healthcare record"""
#     if elderly_id is None:
#         raise ValueError("elderly_id is required and cannot be None.")

#     if not record_type or not record_type.strip():
#         return {"success": False, "error": "record_type is required and cannot be empty."}
#     if not description or not description.strip():
#         return {"success": False, "error": "description is required and cannot be empty."}

#     # Validate date format if provided
#     if diagnosis_date:
#         try:
#             datetime.strptime(diagnosis_date, "%Y-%m-%d")
#         except ValueError:
#             return {"success": False, "error": "diagnosis_date must be in YYYY-MM-DD format if provided."}

#     # Use embedder instance instead of local embedding function
#     embedding = embedder.embed(description)

#     try:
#         with engine.connect() as conn:
#             query = text("""
#                 INSERT INTO healthcare_records (
#                     elderly_id, record_type, description, diagnosis_date, embedding
#                 ) VALUES (
#                     :elderly_id, :record_type, :description, :diagnosis_date, :embedding
#                 )
#                 RETURNING id, last_updated;
#             """)
#             result = conn.execute(query, {
#                 "elderly_id": elderly_id.strip(),
#                 "record_type": record_type.strip(),
#                 "description": description.strip(),
#                 "diagnosis_date": diagnosis_date if diagnosis_date else None,
#                 "embedding": str(embedding) if embedding else None
#             }).fetchone()
#             conn.commit()

#             return {
#                 "success": True,
#                 "message": "Healthcare record stored successfully",
#                 "record_id": str(result.id),
#                 "last_updated": result.last_updated.isoformat() if result.last_updated else None,
#                 "embedding_provided": embedding is not None,
#                 "diagnosis_date": diagnosis_date
#             }

#     except SQLAlchemyError as e:
#         logging.error(f"❌ Database error inserting health record: {str(e)}")
#         return {"success": False, "error": f"Database error: {str(e)}"}
#     except Exception as e:
#         logging.error(f"Unexpected error inserting health record: {str(e)}")
#         return {"success": False, "error": f"Unexpected error: {str(e)}"}



def retrieve_hybrid_ltm(engine, elderly_id, query, top_k_retrieval=5, sim_threshold=0.3, 
                        fuzzy_distance=2, alpha_retrieval=0.5, embedder = Embedder):
    """Retrieve long-term memory using hybrid (embedding + BM25) approach"""
    try:
        emb = embedder.embed(query)
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
        params_emb = {"emb": str(emb), "elderly_id": elderly_id, "top_k": top_k_retrieval}
        if sim_threshold is not None:
            params_emb["threshold"] = sim_threshold
        with engine.connect() as conn:
            rows_emb = conn.execute(sql_emb, params_emb).fetchall()
        emb_results = {
            r.id: {
                "id": r.id,
                "category": r.category,
                "key": r.key,
                "value": r.value,
                "last_updated": r.last_updated,
                "embedding": r.embedding,
                "emb_score": float(r.similarity)
            }
            for r in rows_emb
        }
        
        # --- BM25 ---
        sql_bm25 = text("""
            SELECT id, category, key, value, last_updated, embedding, paradedb.score(id) AS bm25_score
            FROM long_term_memory
            WHERE elderly_id = :elderly_id
              AND (
                category_search @@@ :query
               OR key @@@ :query
               OR value @@@ :query
               OR id @@@ paradedb.match('category_search', :query, distance => :distance)
               OR id @@@ paradedb.match('key', :query, distance => :distance)
               OR id @@@ paradedb.match('value', :query, distance => :distance)
                )
            ORDER BY bm25_score DESC
                LIMIT :top_k;
        """)
        params_bm25 = {
            "elderly_id": elderly_id,
            "query": normalize_for_paradedb(query),
            "distance": fuzzy_distance,
            "top_k": top_k_retrieval
        }
        with engine.connect() as conn:
            rows_bm25 = conn.execute(sql_bm25, params_bm25).fetchall()
        max_bm25 = max((float(r.bm25_score) for r in rows_bm25), default=1.0)
        bm25_results = {
            r.id: {
                "id": r.id,
                "category": r.category,
                "key": r.key,
                "value": r.value,
                "last_updated": r.last_updated,
                "embedding": r.embedding,
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
                "embedding": [],
                "emb_score": 0.0
            })
            bm25_data = bm25_results.get(id_, {
                "id": id_,
                "category": "",
                "key": "",
                "value": "",
                "last_updated": None,
                "embedding": [],
                "bm25_score": 0.0
            })
            combined[id_] = {
                "id": id_,
                "category": emb_data["category"] or bm25_data["category"],
                "key": emb_data["key"] or bm25_data["key"],
                "value": emb_data["value"] or bm25_data["value"],
                "last_updated": emb_data["last_updated"] or bm25_data["last_updated"],
                "embedding": emb_data["embedding"] or bm25_data["embedding"],
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



def retrieve_hybrid_stm(engine, elderly_id, query, top_k_retrieval=5, sim_threshold=0.3, 
                        fuzzy_distance=2, alpha_retrieval=0.5, embedder=Embedder):
    """Retrieve short-term memory using hybrid (embedding + BM25) approach"""
    try:
        emb = embedder.embed(query)
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
        params_emb = {"emb": str(emb), "elderly_id": elderly_id, "top_k": top_k_retrieval}
        if sim_threshold is not None:
            params_emb["threshold"] = sim_threshold
        with engine.connect() as conn:
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
        sql_bm25 = text("""
            SELECT id, content, created_at, embedding, paradedb.score(id) AS bm25_score
            FROM short_term_memory
            WHERE elderly_id = :elderly_id
              AND (content @@@ :query OR id @@@ paradedb.match('content', :query, distance => :distance))
            ORDER BY bm25_score DESC LIMIT :top_k;
        """)
        params_bm25 = {"elderly_id": elderly_id, "query": normalize_for_paradedb(query),
                       "distance": fuzzy_distance, "top_k": top_k_retrieval}
        with engine.connect() as conn:
            rows_bm25 = conn.execute(sql_bm25, params_bm25).fetchall()
        max_bm25 = max((float(r.bm25_score) for r in rows_bm25), default=1.0)
        bm25_results = {
            r.id: {
                "id": r.id,
                "content": r.content,
                "created_at": r.created_at,
                "embedding": r.embedding,
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



def retrieve_hybrid_hcm(engine, elderly_id, query, top_k_retrieval=5, sim_threshold=0.3, 
                        fuzzy_distance=2, alpha_retrieval=0.5, embedder=Embedder):
    """Retrieve healthcare records using hybrid (embedding + BM25) approach"""
    try:
        emb = embedder.embed(query)
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
        params_emb = {"emb": str(emb), "elderly_id": elderly_id, "top_k": top_k_retrieval}
        if sim_threshold is not None:
            params_emb["threshold"] = sim_threshold
        with engine.connect() as conn:
            rows_emb = conn.execute(sql_emb, params_emb).fetchall()
        emb_results = {
            r.id: {
                "id": r.id,
                "record_type": r.record_type,
                "description": r.description,
                "diagnosis_date": r.diagnosis_date.isoformat() if r.diagnosis_date else None,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
                "embedding": r.embedding,
                "emb_score": float(r.similarity)
            }
            for r in rows_emb
        }
        
        # --- BM25 ---
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
            "elderly_id": elderly_id,
            "query": normalize_for_paradedb(query),
            "distance": fuzzy_distance,
            "top_k": top_k_retrieval
        }
        with engine.connect() as conn:
            rows_bm25 = conn.execute(sql_bm25, params_bm25).fetchall()
        max_bm25 = max((float(r.bm25_score) for r in rows_bm25), default=1.0)
        bm25_results = {
            r.id: {
                "id": r.id,
                "record_type": r.record_type,
                "description": r.description,
                "diagnosis_date": r.diagnosis_date.isoformat() if r.diagnosis_date else None,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
                "embedding": r.embedding,
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
                "embedding": [],
                "emb_score": 0.0
            })
            bm25_data = bm25_results.get(id_, {
                "id": id_,
                "record_type": "",
                "description": "",
                "diagnosis_date": None,
                "last_updated": None,
                "embedding": [],
                "bm25_score": 0.0
            })
            combined[id_] = {
                "id": id_,
                "record_type": emb_data["record_type"] or bm25_data["record_type"],
                "description": emb_data["description"] or bm25_data["description"],
                "diagnosis_date": emb_data["diagnosis_date"] or bm25_data["diagnosis_date"],
                "last_updated": emb_data["last_updated"] or bm25_data["last_updated"],
                "embedding": emb_data["embedding"] or bm25_data["embedding"],
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



def rerank_with_mmr_and_recency(query: str, candidates: List[Dict[str, Any]], cross_encoder: CrossEmbedder, 
                                alpha_MMR: float = 0.7, beta_recency: float = 0.1, top_k_MMR: int = 5) -> List[Dict[str, Any]]:
    """Rerank candidates using MMR and recency scoring"""
    if not candidates:
        return []
    
    # Extract relevant metadata
    candidates = compute_recency_score(candidates, query)
    texts = []
    for r in candidates:
        text = r.get("content") or r.get("value") or r.get("description")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Each result must have one of 'content', 'value', or 'description' as non-empty string.")
        texts.append(text)
    
    # Extract embeddings
    embeddings = []
    for r in candidates:
        emb_str = r.pop("embedding", None)
        emb_list = [float(x) for x in emb_str.strip("[]").split(",")]
        embeddings.append(emb_list)
    embeddings = np.array(embeddings, dtype=np.float32)
    
    # Get recency scores
    recency_normalized = np.array([r.get("recency_score", 0.0) for r in candidates], dtype=np.float32)
    
    # Compute cross-encoder relevance
    pairs = [[query, text] for text in texts]
    ce_raw_scores = cross_encoder.predict(pairs)
    min_score, max_score = ce_raw_scores.min(), ce_raw_scores.max()
    ce_scores = (ce_raw_scores - min_score) / (max_score - min_score) if max_score != min_score else np.ones_like(ce_raw_scores)
    
    # MMR greedy selection
    cos_sim_matrix = cosine_similarity(embeddings)
    selected_indices = []
    remaining_indices = list(range(len(candidates)))
    while len(selected_indices) < top_k_MMR and remaining_indices:
        best_score, best_idx = -float("inf"), None
        for idx in remaining_indices:
            ce_score = ce_scores[idx]
            max_sim = max((cos_sim_matrix[idx][s] for s in selected_indices), default=0.0)
            mmr_score = alpha_MMR * ce_score - (1 - alpha_MMR) * max_sim + beta_recency * recency_normalized[idx]
            if mmr_score > best_score:
                best_score, best_idx = mmr_score, idx
        if best_idx is None:
            break
        selected_indices.append(best_idx)
        remaining_indices.remove(best_idx)
    
    # Reorder results
    ranked_results = [candidates[i] for i in selected_indices]
    for i, result in enumerate(ranked_results):
        idx = selected_indices[i]
        result["cross_encoder_score"] = float(ce_scores[idx])
        result["recency_score"] = float(recency_normalized[idx])
        result["mmr_score"] = float(
            alpha_MMR * ce_scores[idx] -
            (1 - alpha_MMR) * max((cos_sim_matrix[idx][selected_indices[j]] for j in range(i)), default=0.0) +
            beta_recency * recency_normalized[idx]
        )
    return ranked_results



def retrieve_rerank(engine, elderly_id, query, mode="long-term", top_k_retrieval=25, 
                    sim_threshold=0.3, fuzzy_distance=2, alpha_retrieval=0.5, 
                    alpha_MMR=0.75, beta_recency=0.1, top_k_MMR=8, embedder=Embedder, cross_encoder=CrossEmbedder()):
    """Retrieve and rerank results based on mode"""
    if cross_encoder is None:
        cross_encoder = CrossEmbedder('BAAI/bge-reranker-base')
    
    # Step 1: Retrieve candidates based on mode
    if mode == "short-term":
        candidates = retrieve_hybrid_stm(engine, embedder, elderly_id, query, top_k_retrieval, 
                                        sim_threshold, fuzzy_distance, alpha_retrieval)
    elif mode == "long-term":
        candidates = retrieve_hybrid_ltm(engine, embedder, elderly_id, query, top_k_retrieval, 
                                        sim_threshold, fuzzy_distance, alpha_retrieval)
    elif mode == "healthcare":
        candidates = retrieve_hybrid_hcm(engine, embedder, elderly_id, query, top_k_retrieval, 
                                        sim_threshold, fuzzy_distance, alpha_retrieval)
    else:
        raise ValueError(f"Unsupported mode: {mode}. Choose from 'short-term', 'long-term', or 'healthcare'.")
    
    # Step 2: Rerank with MMR + recency
    reranked_results = rerank_with_mmr_and_recency(query, candidates, cross_encoder, alpha_MMR, 
                                                  beta_recency, top_k_MMR)
    
    # Step 3: Remove internal score keys
    score_keys = {'emb_score', 'bm25_score', 'hybrid_score', 'recency_score', 
                 'cross_encoder_score', 'mmr_score'}
    clean_results = [
        {k: v for k, v in result.items() if k not in score_keys}
        for result in reranked_results
    ]
    return clean_results