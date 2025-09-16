

_model = None

def get_embedding(text: str):
    if _model is None:
        raise RuntimeError("Model not initialized. Call init_model() first.")
    return _model.encode(text).tolist()
