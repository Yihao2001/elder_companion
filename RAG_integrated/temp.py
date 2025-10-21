import time
import importlib
import sys

# List all modules you import in your script
modules_to_time = [
    "__future__",               # annotated only
    "typing",                   # standard lib
    "typing_extensions",        # third-party
    "operator",
    "logging",
    "ast",
    "json",
    "langgraph.graph",
    "langgraph.prebuilt",
    "langgraph.checkpoint.memory",
    "langchain_core.messages",
    "langchain_core.tools",
    "session_context",
    "rag_functions",
]

def time_import(name: str):
    start = time.perf_counter()
    module = importlib.import_module(name)
    end = time.perf_counter()
    elapsed = end - start
    print(f"Imported {name:<40} in {elapsed:.4f} seconds")
    return module

def main():
    # Optionally clear relevant modules for more accurate cold import
    for m in list(sys.modules):
        if m.startswith("langgraph") or m.startswith("langchain_core") or m.startswith("session_context") or m.startswith("rag_functions"):
            del sys.modules[m]

    print("Timing individual imports:")
    for mod in modules_to_time:
        try:
            time_import(mod)
        except Exception as e:
            print(f"Failed to import {mod}: {e}")

    # Then time the full script import
    print("\nTiming full module import of your main script:")
    start = time.perf_counter()
    # Replace 'your_module' with the path/name of your script
    end = time.perf_counter()
    print(f"Full import of your_module took {(end - start):.4f} seconds")

if __name__ == "__main__":
    main()
