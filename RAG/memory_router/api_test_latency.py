import requests
import time

url = "http://127.0.0.1:8000/invoke"

# Expanded test cases reflecting real elder care use cases
test_cases = [
    # Offline (local knowledge / memory-based)
    {
        "text": "When do I take my blood pressure pills?",
        "flow_type": "offline",
        "description": "Medication schedule query"
    },
    {
        "text": "What did Dr. Lim say about my diet last week?",
        "flow_type": "offline",
        "description": "Past medical advice recall"
    },
    {
        "text": "Where did I put my glasses?",
        "flow_type": "offline",
        "description": "Personal item location"
    },
    {
        "text": "Who is coming to visit me tomorrow?",
        "flow_type": "offline",
        "description": "Social schedule query"
    },

    # Online (general knowledge / internet-based)
    {
        "text": "What are the side effects of Metformin?",
        "flow_type": "online",
        "description": "Medication information lookup"
    },
    {
        "text": "How do I make chicken soup for a cold?",
        "flow_type": "online",
        "description": "Home remedy recipe"
    },
    {
        "text": "What's the phone number for the nearest pharmacy?",
        "flow_type": "online",
        "description": "Local service search"
    },
    {
        "text": "Explain what diabetes is in simple terms.",
        "flow_type": "online",
        "description": "Health education query"
    },
    {
        "text": "Is it safe to take paracetamol with my heart medication?",
        "flow_type": "online",
        "description": "Drug interaction check"
    },
    {
        "text": "What exercises are good for arthritis in seniors?",
        "flow_type": "online",
        "description": "Physical health guidance"
    }
]

print(f"Testing {len(test_cases)} cases against {url}\n")

for i, case in enumerate(test_cases, 1):
    payload = {
        "text": case["text"],
        "flow_type": case["flow_type"],
        "qa": "",
        "topic": ""
    }

    print(f"[{i:2d}/{len(test_cases)}] {case['flow_type'].upper():7} | {case['description']}")
    print(f"  Input: \"{case['text']}\"")

    start_time = time.perf_counter()
    try:
        response = requests.post(url, json=payload, timeout=60)
        latency = time.perf_counter() - start_time

        print(f"  Status: {response.status_code} | Latency: {latency:.3f}s")

        if response.status_code == 200:
            try:
                result = response.json()
                # Print only top-level keys or a snippet to keep output clean
                if isinstance(result, dict):
                    output = result.get("output", result.get("response", str(result)))
                else:
                    output = str(result)
                print(f"  Output: {str(output)[:150]}{'...' if len(str(output)) > 150 else ''}")
            except requests.exceptions.JSONDecodeError:
                print(f"  Raw response (non-JSON): {response.text[:150]}...")
        else:
            print(f"  Error: {response.text[:200]}")

    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout after {time.perf_counter() - start_time:.3f}s")
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request failed: {e}")

    print("-" * 80)