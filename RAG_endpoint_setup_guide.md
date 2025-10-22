1. make a virtual environment
```bash
python -m venv .venv
```

2. pip install uv (a package installer for faster loading)
```bash
pip install uv
```

3. pip install the requirements.txt
```bash
uv pip install -r requirements.txt
```

4. install other dependencies
```bash
python -m spacy download en_core_web_lg
```

5. run the FastAPI service
```bash
# from root main project directory
uvicorn rag_backend.rag_backend_api:app --reload

# this takes a while to start up, wait for the below to show before ping-ing the api endpoint
# INFO:     Started server process [18176]
# INFO:     Waiting for application startup.
# 2025-10-22 19:51:06.813 SGT | INFO     | rag_backend_api.py:lifespan:28 - Initializing Module 1: NaturalLanguageToJSONPipeline…
# 2025-10-22 19:51:10.258 SGT | INFO     | rag_backend_api.py:lifespan:31 - Initializing Module 2: RouterGraph…
# 2025-10-22 19:51:10.262 SGT | INFO     | rag_backend_api.py:lifespan:35 - Initializing Module 3: Creating SessionContext…
# 2025-10-22 19:51:16.792 SGT | INFO     | embedder.py:_ensure_model_loaded:31 - ✅ Embedding model loaded: google/embeddinggemma-300m
# 2025-10-22 19:51:35.682 SGT | INFO     | embedder.py:_ensure_model_loaded:67 - ✅ CrossEncoder loaded: jinaai/jina-reranker-v1-turbo-en
# 2025-10-22 19:51:35.881 SGT | INFO     | rag_backend_api.py:lifespan:38 - Initializing Module 3: Initializing OfflineGraph…
# 2025-10-22 19:51:36.066 SGT | INFO     | offline_graph.py:__init__:56 - ✅ OfflineGraph ready in 0.18s
# 2025-10-22 19:51:36.067 SGT | INFO     | rag_backend_api.py:lifespan:41 - Initializing Module 3:  Initializing OnlineGraph…
# 2025-10-22 19:51:36.145 SGT | INFO     | online_graph.py:__init__:59 - ✅ OnlineGraph ready in 0.08s
# 2025-10-22 19:51:36.146 SGT | INFO     | rag_backend_api.py:lifespan:51 - Startup complete. API ready.
# INFO:     Application startup complete.

# once Application startup complete you can ping the endpoint at URL = "http://127.0.0.1:8000/invoke"
```