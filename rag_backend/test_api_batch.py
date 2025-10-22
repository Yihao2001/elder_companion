import requests
import time

# --------------------------
# Configuration
# --------------------------
URL = "http://127.0.0.1:8000/invoke"
REQUEST_TIMEOUT = 60  # seconds before giving up on any single request
RETRY_ATTEMPTS = 2    # how many times to retry after timeout or connection error
DELAY_BETWEEN_REQUESTS = 5  # seconds between requests to prevent overload

TEXT_EXAMPLES = [
    "What are the main side effects of this treatment?",
    "Can you explain the new billing policy?",
    "How do I reset my password?",
    "What are your operating hours for the upcoming holiday?",
    "Tell me about the history of your company.",
    "Can I schedule an appointment for next Tuesday?",
    "What is the recommended dosage for this medication?",
    "Summarize the latest product update.",
    "Who is the current CEO?",
    "Compare your product with three main competitors.",
    "What is your privacy policy?",
    "How does the refund process work?"
]

def send_request(text, flow_type):
    """Sends a request to the endpoint with timeout and retry logic."""
    payload = {
        "text": text,
        "flow_type": flow_type,
        "qa": "",
        "topic": ""
    }

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        start_time = time.time()
        try:
            response = requests.post(URL, json=payload, timeout=REQUEST_TIMEOUT)
            end_time = time.time()
            latency = end_time - start_time

            if response.status_code == 200:
                return latency, True

            print(f"  -> Error: Received HTTP {response.status_code}")
            return latency, False

        except requests.exceptions.Timeout:
            print(f"  -> Timeout on attempt {attempt}/{RETRY_ATTEMPTS} ({flow_type})")
        except requests.exceptions.RequestException as e:
            print(f"  -> Critical Error: {e}")
        finally:
            end_time = time.time()
            latency = end_time - start_time

        # If it’s not the last attempt, wait briefly before retrying
        if attempt < RETRY_ATTEMPTS:
            time.sleep(1)

    return latency, False  # after retries fail

def main():
    """Main function to run the stress test."""
    online_latencies = []
    offline_latencies = []

    print("-" * 50)
    print("               Endpoint Stress Test Script")
    print("-" * 50)

    # --- Warm-up Phase ---
    print("\n[PHASE 1: WARM-UP QUERIES (not timed)]")
    _, success = send_request("This is a warm-up query.", "offline")
    print(f"Warm-up 'offline': {'SUCCESS' if success else 'FAILED'}")
    _, success = send_request("This is a warm-up query.", "online")
    print(f"Warm-up 'online':  {'SUCCESS' if success else 'FAILED'}")

    # --- Offline Latency Profiling ---
    print("\n[PHASE 2: OFFLINE LATENCY PROFILING]")
    for i, text in enumerate(TEXT_EXAMPLES):
        latency, success = send_request(text, "offline")
        print(f"OFFLINE Request #{i+1:02d}: {'SUCCESS' if success else 'FAILED'} in {latency:.3f}s")
        if success:
            offline_latencies.append(latency)
        time.sleep(DELAY_BETWEEN_REQUESTS)

    # --- Online Latency Profiling ---
    print("\n[PHASE 3: ONLINE LATENCY PROFILING]")
    for i, text in enumerate(TEXT_EXAMPLES):
        latency, success = send_request(text, "online")
        print(f"ONLINE  Request #{i+1:02d}: {'SUCCESS' if success else 'FAILED'} in {latency:.3f}s")
        if success:
            online_latencies.append(latency)
        time.sleep(DELAY_BETWEEN_REQUESTS)

    # --- Summary ---
    print("\n" + "=" * 50)
    print("                 Latency Test Summary")
    print("=" * 50)

    if offline_latencies:
        avg_off = sum(offline_latencies) / len(offline_latencies)
        print(f"Average OFFLINE latency: {avg_off:.3f}s ({len(offline_latencies)} successful)")
    else:
        print("No successful OFFLINE requests.")

    if online_latencies:
        avg_on = sum(online_latencies) / len(online_latencies)
        print(f"Average ONLINE latency:  {avg_on:.3f}s ({len(online_latencies)} successful)")
    else:
        print("No successful ONLINE requests.")

    print("-" * 50)


if __name__ == "__main__":
    main()
