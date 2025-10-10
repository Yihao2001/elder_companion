from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import LongTermMemory, LTMCategoryEnum
from ..utils import get_embedding

ltm_bp = Blueprint("ltm", __name__)

@ltm_bp.route("/ltm", methods=["GET"])
def get_ltm():
    db: Session = next(get_db())
    query = db.query(LongTermMemory)

    elderly_id = request.args.get("elderly_id")
    category = request.args.get("category")

    if elderly_id:
        query = query.filter(LongTermMemory.elderly_id == elderly_id)
    else:
        return jsonify({"error": "Missing elderly_id"}), 400

    if category:
        query = query.filter(LongTermMemory.category == category)

    records = query.all()
    db.close()

    result = [
        {
            "ltm_id": r.id,
            "category": r.category.value if r.category else None,
            "key": r.key,
            "value": r.value,
            "last_updated": r.last_updated.isoformat()
        } for r in records
    ]
    return jsonify(result), 200

@ltm_bp.route("/ltm", methods=["POST"])
def post_ltm():
    data = request.json
    elderly_id = data.get("elderly_id")
    category = data.get("category")
    key = data.get("key")
    value = data.get("value")

    if not elderly_id or not category or not value:
        return jsonify({"error": "elderly_id, category, and value are required"}), 400

    try:
        category_enum = LTMCategoryEnum(category)
    except ValueError:
        return jsonify({"error": f"Invalid category: {category}"}), 400

    embedding = get_embedding(value)

    db: Session = next(get_db())
    record = LongTermMemory(
        elderly_id=elderly_id,
        category=category_enum,
        key=key,
        value=value,
        embedding=embedding
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    db.close()

    return jsonify({"id": str(record.id), "message": "Inserted into LTM"}), 201

@ltm_bp.route("/ltm/<int:ltm_id>", methods=["PUT"])
def update_ltm(ltm_id):
    db: Session = next(get_db())
    record = db.query(LongTermMemory).filter(LongTermMemory.id == ltm_id).first()

    if not record:
        db.close()
        return jsonify({"error": "LTM record not found"}), 404

    data = request.json
    category = data.get("category")
    key = data.get("key")
    value = data.get("value")

    if not category or not key or not value:
        db.close()
        return jsonify({"error": "At least one of category, key or value is required"}), 400

    try:
        category_enum = LTMCategoryEnum(category)
        record.category = category_enum
    except ValueError:
        db.close()
        return jsonify({"error": f"Invalid category: {category}"}), 400

    record.key = key
    record.value = value
    record.embedding = get_embedding(value) # Re-generate embedding for the new value

    db.commit()
    db.close()

    return jsonify({"message": f"LTM record {ltm_id} updated successfully"}), 200
