from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from datetime import datetime
from ..db import get_db
from ..models import ShortTermMemory
from ..utils import get_embedding

stm_bp = Blueprint("stm", __name__)

@stm_bp.route("/stm", methods=["GET"])
def get_stm():
    db: Session = next(get_db())
    query = db.query(ShortTermMemory)

    elderly_id = request.args.get("elderly_id")
    created_at_start = request.args.get("created_at_start")  # YYYY-MM-DD
    created_at_end = request.args.get("created_at_end")      # YYYY-MM-DD

    if elderly_id:
        query = query.filter(ShortTermMemory.elderly_id == elderly_id)
    else:
        return jsonify({"error": f"Missing elderly_id"}), 400

    # Handle date range
    try:
        if created_at_start:
            start_date = datetime.strptime(created_at_start, "%Y-%m-%d")
            query = query.filter(ShortTermMemory.created_at >= start_date)
        if created_at_end:
            end_date = datetime.strptime(created_at_end, "%Y-%m-%d")
            query = query.filter(ShortTermMemory.created_at <= end_date)
    except ValueError:
        return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

    records = query.all()
    db.close()

    result = [
        {
            "content": r.content,
            "created_at": r.created_at.isoformat()
        } for r in records
    ]
    return jsonify(result), 200


@stm_bp.route("/stm", methods=["POST"])
def post_stm():
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
