# offline graph
```python
result = graph.invoke(test_state)
chunks: List[Dict(str, Any)] = result["final_chunks"]
```

chunks is the list of outputs from database in the json format as follow:
```bash
[
  {
    "id": "2e855a4a-f037-475a-9ffb-2fad004f1f9b",
    "category": "lifestyle",
    "key": "hobby",
    "value": "used to play badminton in school days",
    "last_updated": "2025-10-06T08:40:05.253235",
    "emb_score": 0.0,
    "bm25_score": 0.7316405594975022,
    "hybrid_score": 0.3658,
    "recency_score": 0.0,
    "timezone_used": "Asia/Singapore (UTC+8)",
    "cross_encoder_score": 1.0,
    "mmr_score": 0.699999988079071
  },
  {
    "id": "2a635240-5a0a-43e8-bd23-fbea0173bc6b",
    "record_type": "medication",
    "description": "Patient has to take Metformin 500mg every morning to manage blood sugar levels.",
    "diagnosis_date": null,
    "last_updated": "2025-10-06T08:40:19.084086",
    "emb_score": 0.36372402579212615,
    "bm25_score": 0.4948763331364058,
    "hybrid_score": 0.4293,
    "recency_score": 0.0,
    "timezone_used": "Asia/Singapore (UTC+8)",
    "cross_encoder_score": 0.8354958295822144,
    "mmr_score": 0.43845996260643005
  },
  {
    "id": "701ccef9-ff7b-4663-af2c-92e2fc9bc82b",
    "category": "lifestyle",
    "key": "friend",
    "value": "Mr Lim",
    "last_updated": "2025-10-06T08:39:59.961263",
    "emb_score": 0.32545099843717584,
    "bm25_score": 0.4632809579792616,
    "hybrid_score": 0.3944,
    "recency_score": 0.0,
    "timezone_used": "Asia/Singapore (UTC+8)",
    "cross_encoder_score": 0.892337441444397,
    "mmr_score": 0.38951098918914795
  }
]
```


# online mode:
```python

`