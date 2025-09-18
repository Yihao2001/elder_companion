from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import ShortTermMemory
from ..utils import get_embedding

stm_bp = Blueprint("stm", __name__)

@stm_bp.route("/stm", methods=["POST"])
def add_stm():
    data = request.json
    content = data.get("content")
    elderly_id = data.get("elderly_id")

    if not content or not elderly_id:
        return jsonify({"error": "elderly_id and content are required"}), 400

    embedding = get_embedding(content)

    db: Session = next(get_db())
    record = ShortTermMemory(
        elderly_id=elderly_id,
        content=content,
        embedding=embedding
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    db.close()

    return jsonify({"id": str(record.id), "message": "Inserted into STM"}), 201