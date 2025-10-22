#!/usr/bin/env python3
import os
import json
import time
import random
from dotenv import load_dotenv

# ==========================================================
# ⏱️ TIME HEAVY IMPORTS
# ==========================================================
start_import_time = time.perf_counter()

from session_context import SessionContext
from langchain_core.messages import HumanMessage, SystemMessage
from online_graph_builder import build_online_graph
from utils.prompt import SYSTEM_PROMPT

import_end_time = time.perf_counter()
import_latency = import_end_time - start_import_time
print(f"⏱️ SessionContext + imports loaded in {import_latency:.3f} seconds")

# ==========================================================
# 🔧 CONFIGURATION
# ==========================================================
DATABASE_URL_ENV = "DATABASE_URL"
ELDERLY_ID = "87654321-4321-4321-4321-019876543210"
CROSS_ENCODER_MODEL = "jinaai/jina-reranker-v1-turbo-en"

# ==========================================================
# 🧪 TEST CASES
# ==========================================================
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

# ==========================================================
# 🧹 HELPERS
# ==========================================================
def remove_embedding_from_chunks(chunk_list):
    """Remove 'embedding' keys from each chunk dictionary."""
    return [
        {k: v for k, v in chunk.items() if k != "embedding"}
        for chunk in (chunk_list or [])
    ]

def print_case_header(idx, case):
    print("\n" + "=" * 90)
    print(f"🧪  TEST CASE #{idx + 1}: {case['description']}")
    print("-" * 90)
    print(f"📘  Type       : {case['qa_type']}")
    print(f"🏷️   Topics     : {', '.join(case['topics'])}")
    print(f"🗣️  Input Text : {case['input_text']}")

def print_case_details(final_chunks, latency_seconds, qa_type, result):
    print("\n" + "-" * 90)
    print("🧠  AGENT APP INVOCATION RESULT")
    print("-" * 90)
    print("✅ Graph invocation completed.")
    print(f"⏱️  Latency: {latency_seconds:.3f} seconds")
    print(f"🧩  Final chunks retrieved: {len(final_chunks)}")
    print("-" * 90)

    if final_chunks:
        print("\n🔍  FINAL CHUNKS:")
        for i, chunk in enumerate(final_chunks, 1):
            snippet = chunk.get("content", json.dumps(chunk, indent=2, default=str))
            s = str(snippet)
            print(f"  [{i}] {s[:500]}{'...' if len(s) > 500 else ''}")
    else:
        print("\n🔍  FINAL CHUNKS: None found")

    # Determine pass/fail like the offline runner
    passed = False
    if qa_type == "question":
        passed = len(final_chunks) > 0
        if not passed:
            print("⚠️  No chunks returned for this question.")
    elif qa_type == "statement":
        passed = bool(result.get("inserted"))
        if passed:
            print("✅ Content successfully inserted into short-term memory.")
        else:
            print("⚠️  Content was not inserted (result['inserted'] is falsy or missing).")

    return passed

# ==========================================================
# 🚀 MAIN EXECUTION
# ==========================================================
def main():
    total_start = time.perf_counter()

    # ---------- Load environment ----------
    load_dotenv()

    # ---------- Initialize Session ----------
    session_start = time.perf_counter()
    session = SessionContext(
        db_url=os.getenv(DATABASE_URL_ENV),
        elderly_id=ELDERLY_ID,
        cross_encoder_model=CROSS_ENCODER_MODEL,
    )
    session_end = time.perf_counter()
    session_latency = session_end - session_start
    print(f"⏱️ SessionContext initialized in {session_latency:.3f} seconds")

    # ---------- Build ONLINE Graph ----------
    graph_build_start = time.perf_counter()
    app = build_online_graph(session)
    graph_build_end = time.perf_counter()
    graph_build_latency = graph_build_end - graph_build_start
    print(f"⏱️ Graph built in {graph_build_latency:.3f} seconds\n")

    # ---------- Randomize test order (optional, mirrors offline harness) ----------
    random.shuffle(test_cases)
    print("🔀 Test case order randomized.")
    print("🧭 First test to run:", test_cases[0]["description"])
    print("\n🚀 Starting ONLINE agent tests...")

    # ---------- Run all test cases ----------
    results = []
    latencies = []

    for idx, case in enumerate(test_cases):
        print_case_header(idx, case)

        system_msg = SystemMessage(content=SYSTEM_PROMPT)

        # NOTE: We include qa_type & topics in the payload in case your graph uses them.
        payload = {
            "session": session,
            "messages": [system_msg, HumanMessage(content=case["input_text"])],
            "qa_type": case["qa_type"],
            "topics": case["topics"],
            "candidates": [],
            "final_chunks": [],
        }

        print("\n🚀 Invoking ONLINE agent app...\n")
        start_time = time.perf_counter()
        result = app.invoke(payload)
        end_time = time.perf_counter()
        latency_seconds = end_time - start_time

        final_chunks = remove_embedding_from_chunks(result.get("final_chunks", []))
        passed = print_case_details(final_chunks, latency_seconds, case["qa_type"], result)

        latencies.append(latency_seconds)
        results.append({
            "desc": case["description"],
            "qa_type": case["qa_type"],
            "latency": latency_seconds,
            "passed": passed,
        })

    # ---------- Summary Table ----------
    print("\n📊 Summary of Test Results:")
    print("-" * 90)
    passed_tests = sum(1 for r in results if r["passed"])
    failed_tests = len(results) - passed_tests

    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        latency = f"{r['latency']:.3f} sec" if r["latency"] is not None else "—"
        print(f"{status:<10} | {r['desc']:<45} | Latency: {latency}")

    print("-" * 90)
    print(f"✅ Passed: {passed_tests} / {len(results)}")

    if latencies:
        total_latency = sum(latencies)
        avg_latency = total_latency / len(latencies)
        print(f"⚡ Fastest: {min(latencies):.3f} sec")
        print(f"🐢 Slowest: {max(latencies):.3f} sec")
        print(f"📈 Average: {avg_latency:.3f} sec")

    total_end = time.perf_counter()
    total_duration = total_end - total_start

    print(f"🧩 Import time: {import_latency:.3f} sec")
    print(f"🧩 Session init time: {session_latency:.3f} sec")
    print(f"🧩 Graph build time: {graph_build_latency:.3f} sec")
    print(f"🕒 Total runtime for all tests: {total_duration:.3f} sec")
    print("🎉 All tests completed.\n")

# ==========================================================
if __name__ == "__main__":
    main()
