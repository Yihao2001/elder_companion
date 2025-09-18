from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import HealthcareRecord, RecordTypeEnum
from ..utils import get_embedding

healthcare_bp = Blueprint("healthcare", __name__)

@healthcare_bp.route("/healthcare", methods=["GET"])
def get_healthcare():
    db: Session = next(get_db())
    query = db.query(HealthcareRecord)

    elderly_id = request.args.get("elderly_id")
    record_type = request.args.get("record_type")

    if elderly_id:
        query = query.filter(HealthcareRecord.elderly_id == elderly_id)
    else:
        return jsonify({"error": "Missing elderly_id"}), 400

    if record_type:
        query = query.filter(HealthcareRecord.record_type == record_type)

    records = query.all()
    db.close()

    result = [
        {
            "record_type": r.record_type.value if r.record_type else None,
            "description": r.description,
            "diagnosis_date": r.diagnosis_date.isoformat() if r.diagnosis_date else None,
            "last_updated": r.last_updated.isoformat()
        } for r in records
    ]
    return jsonify(result), 200

@healthcare_bp.route("/healthcare", methods=["POST"])
def post_healthcare():
    data = request.json
    elderly_id = data.get("elderly_id")
    record_type = data.get("record_type")
    description = data.get("description")
    diagnosis_date = data.get("diagnosis_date")

    if not elderly_id or not record_type or not description:
        return jsonify({"error": "elderly_id, record_type, and description are required"}), 400

    try:
        record_type_enum = RecordTypeEnum(record_type)
    except ValueError:
        return jsonify({"error": f"Invalid record_type: {record_type}"}), 400

    embedding = get_embedding(description)

    db: Session = next(get_db())
    record = HealthcareRecord(
        elderly_id=elderly_id,
        record_type=record_type_enum,
        description=description,
        diagnosis_date=diagnosis_date,
        embedding=embedding
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    db.close()

    return jsonify({"id": str(record.id), "message": "Inserted into Healthcare"}), 201
