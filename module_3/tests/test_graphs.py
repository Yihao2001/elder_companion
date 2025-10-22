# test_both_graphs.py
import os
from dotenv import load_dotenv
from session_context import SessionContext
from module_3.online_graph import OnlineGraph
from module_3.offline_graph import OfflineGraph

# Load environment variables
load_dotenv()

def main():
    # Shared config
    elderly_id = os.getenv("ELDERLY_ID")
    db_url = os.getenv("DATABASE_URL")
    cross_encoder_model = "jinaai/jina-reranker-v1-turbo-en"
    
    # Create a shared session to avoid duplicate DB/embedder setup
    session = SessionContext(
        db_url=db_url,
        elderly_id=elderly_id,
        cross_encoder_model=cross_encoder_model,
    )

    print("🧪 Starting end-to-end test for Online and Offline Graphs\n")

    # ========== TEST ONLINE GRAPH ==========
    print("🌐 Testing OnlineGraph...")
    online_app = OnlineGraph(session=session, verbose=True)
    
    online_input = "What is my current medication plan?"
    online_result = online_app.invoke(online_input)
    
    print(f"✅ Online result keys: {list(online_result.keys())}")
    print(f"📄 Final chunks count: {len(online_result.get('final_chunks', []))}\n")

    # ========== TEST OFFLINE GRAPH ==========
    print("💾 Testing OfflineGraph...")
    offline_app = OfflineGraph(session=session, verbose=True)
    
    # Test a QUESTION
    offline_question = {
        "text": "When do I take my blood pressure pills?",
        "qa": "question",
        "topic": ["healthcare"]
    }
    offline_result_q = offline_app.invoke(offline_question)
    
    print(f"✅ Offline (question) result keys: {list(offline_result_q.keys())}")
    print(f"📄 Final chunks count: {len(offline_result_q.get('final_chunks', []))}\n")

    # Test a STATEMENT (for insertion + retrieval)
    offline_statement = {
        "text": "I took my vitamin D supplement this morning.",
        "qa": "statement",
        "topic": ["short-term", "healthcare"]
    }
    offline_result_s = offline_app.invoke(offline_statement)
    
    print(f"✅ Offline (statement) result keys: {list(offline_result_s.keys())}")
    print(f"📎 Inserted: {offline_result_s.get('inserted', False)}")
    print(f"📄 Final chunks count: {len(offline_result_s.get('final_chunks', []))}\n")

    print("🎉 All tests completed successfully!")

if __name__ == "__main__":
    main()