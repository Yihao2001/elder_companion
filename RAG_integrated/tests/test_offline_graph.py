import os
import time
import random
from dotenv import load_dotenv

# 1️⃣ Start timing imports
start_import_time = time.perf_counter()

from offline_graph_builder import build_offline_graph, GraphState
from session_context import SessionContext

import_end_time = time.perf_counter()
import_latency = import_end_time - start_import_time
print(f"⏱️ SessionContext + imports loaded in {import_latency:.3f} seconds")

# 2️⃣ Load environment variables
load_dotenv()

# 3️⃣ Time SessionContext initialization
session_start = time.perf_counter()
session = SessionContext(
    db_url=os.getenv("DATABASE_URL"),
    elderly_id="87654321-4321-4321-4321-019876543210",
    cross_encoder_model="jinaai/jina-reranker-v1-turbo-en"
)
session_end = time.perf_counter()
session_latency = session_end - session_start
print(f"⏱️ SessionContext initialized in {session_latency:.3f} seconds")

# 4️⃣ Build the compiled graph once
graph_build_start = time.perf_counter()
graph = build_offline_graph()
graph_build_end = time.perf_counter()
graph_build_latency = graph_build_end - graph_build_start
print(f"⏱️ Graph built in {graph_build_latency:.3f} seconds\n")


# ---------- TEST CASE EXECUTOR ----------
def run_test_case(description: str, qa_type: str, input_text: str, topics: list[str]):
    """Run a single test case and measure latency."""
    print(f"\n{'='*90}")
    print(f"🧪 Test Case: {description}")
    print(f"{'-'*90}")

    test_state: GraphState = {
        "session": session,
        "input_text": input_text,
        "qa_type": qa_type,
        "topics": topics,
        "candidates": [],
        "final_chunks": [],
        "inserted": False,
    }

    try:
        start_time = time.perf_counter()
        result = graph.invoke(test_state)
        end_time = time.perf_counter()

        latency = end_time - start_time
        print(f"⏱️  Graph execution latency: {latency:.3f} seconds")

        passed = False

        if qa_type == "question":
            if "final_chunks" in result and len(result["final_chunks"]) > 0:
                passed = True
                print(f"✅ Retrieved {len(result['final_chunks'])} chunks.")
                for i, chunk in enumerate(result["final_chunks"]):
                    print(f"{i+1}.", chunk.get("content", chunk))
            else:
                print("⚠️ No chunks returned for this question.")
        elif qa_type == "statement":
            if result.get("inserted"):
                passed = True
                print("✅ Content successfully inserted into short-term memory.")
            else:
                print("⚠️ Content was not inserted.")

        return {"desc": description, "latency": latency, "passed": passed, "result": result}

    except Exception as e:
        print("❌ Test failed with error:", e)
        return {"desc": description, "latency": None, "passed": False, "result": None}


# 5️⃣ Define all test scenarios
test_cases = [
    # 🔹 Retrieval questions
    {"description": "Q: Healthcare", "qa_type": "question", "input_text": "What is John's current medication plan?", "topics": ["healthcare"]},
    {"description": "Q: Long-term", "qa_type": "question", "input_text": "What is John's address?", "topics": ["long-term"]},
    {"description": "Q: Short-term only", "qa_type": "question", "input_text": "What happened to John this morning?", "topics": ["short-term"]},
    {"description": "S: Insert and Healthcare", "qa_type": "question", "input_text": "John took 5mg of atorvastatin this morning", "topics": ["healthcare", "short-term"]},
    {"description": "S: Insert and Multi-topic (healthcare + short + long)", "qa_type": "question", "input_text": "John's brother David brought him to see the doctor this morning at Firefly Hospital for his diabetes checkout", "topics": ["healthcare", "short-term", "long-term"]},

    # 🔹 Insertion statements
    {"description": "S: Insert medication update", "qa_type": "statement", "input_text": "John started taking 5mg of atorvastatin daily.", "topics": ["short-term"]},
    {"description": "S: Insert and Healthcare", "qa_type": "statement", "input_text": "John’s blood pressure was stable this morning.", "topics": ["short-term", "healthcare"]},
    {"description": "S: Insert mood observation", "qa_type": "statement", "input_text": "John was cheerful after breakfast.", "topics": ["short-term"]},
]

# 🔀 Randomize test order
random.shuffle(test_cases)
print("\n🔀 Test case order randomized.")
print("🧭 First test to run:", test_cases[0]["description"])

# 6️⃣ Run all test cases
print("\n🚀 Starting LangGraph tests...")
total_start = time.perf_counter()

results = []
for case in test_cases:
    results.append(run_test_case(**case))

total_end = time.perf_counter()
total_duration = total_end - total_start


# 7️⃣ Summarize results
print("\n📊 Summary of Test Results:")
print("-" * 90)
passed_tests = sum(1 for r in results if r["passed"])
failed_tests = len(results) - passed_tests

for r in results:
    status = "✅ PASS" if r["passed"] else "❌ FAIL"
    latency = f"{r['latency']:.3f} sec" if r["latency"] else "—"
    print(f"{status:<10} | {r['desc']:<45} | Latency: {latency}")

print("-" * 90)
print(f"✅ Passed: {passed_tests} / {len(results)}")

# 🕒 Latency summary
latencies = [r["latency"] for r in results if r["latency"] is not None]
if latencies:
    total_latency = sum(latencies)
    avg_latency = total_latency / len(latencies)
    print(f"⚡ Fastest: {min(latencies):.3f} sec")
    print(f"🐢 Slowest: {max(latencies):.3f} sec")
    print(f"📈 Average: {avg_latency:.3f} sec")

print(f"🧩 Import time: {import_latency:.3f} sec")
print(f"🧩 Session init time: {session_latency:.3f} sec")
print(f"🧩 Graph build time: {graph_build_latency:.3f} sec")
print(f"🕒 Total runtime for all tests: {total_duration:.3f} sec")
print("🎉 All tests completed.\n")
