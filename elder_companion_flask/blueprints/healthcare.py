from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import HealthcareRecord, RecordTypeEnum, TableNameEnum, ActionEnum
from ..utils import get_embedding
from ..services.audit_service import create_audit_log

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
            "healthcare_record_id": r.id,
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

    # Log audit
    new_record = {
        "record_type": record.record_type.value,
        "description": record.description,
        "diagnosis_date": format_date(record.diagnosis_date)
    }
    create_audit_log(db, elderly_id, TableNameEnum.healthcare_records, None, new_record, ActionEnum.add)

    db.commit()
    db.refresh(record)
    db.close()

    return jsonify({"id": str(record.id), "message": "Inserted into Healthcare"}), 201

@healthcare_bp.route("/healthcare", methods=["PUT"])
def update_healthcare():
    db: Session = next(get_db())

    record_id = request.args.get("healthcare_record_id")
    if not record_id:
        return jsonify({"error": "record_id is required"}), 400
    
    record = db.query(HealthcareRecord).filter(HealthcareRecord.id == record_id).first()
    curr_record = {
        'record_type': record.record_type.value,
        'description': record.description,
        'diagnosis_date': format_date(record.diagnosis_date)
    }

    if not record:
        db.close()
        return jsonify({"error": "Healthcare record not found"}), 404

    data = request.json
    record_type = data.get("record_type")
    description = data.get("description")
    diagnosis_date = data.get("diagnosis_date")

    if not record_type or not description or not diagnosis_date:
        db.close()
        return jsonify({"error": "At least one of record_type, description or diagnosis_date is required"}), 400

    try:
        record_type_enum = RecordTypeEnum(record_type)
        record.record_type = record_type_enum
    except ValueError:
        db.close()
        return jsonify({"error": f"Invalid record_type: {record_type}"}), 400

    record.description = description if description else record.description
    record.diagnosis_date = diagnosis_date if diagnosis_date else record.diagnosis_date
    record.embedding = get_embedding(description) if description else record.embedding # Re-generate embedding for the new description

    # Log audit 
    new_record = {
        'record_type': record.record_type.value,
        'description': record.description,
        'diagnosis_date': format_date(record.diagnosis_date)
    }
    create_audit_log(db, record.elderly_id, TableNameEnum.healthcare_records, curr_record, new_record, ActionEnum.update)

    db.commit()
    db.close()

    return jsonify({"message": f"Healthcare record {record_id} updated successfully"}), 200

def format_date(date_obj):
    if date_obj is None:
        return None
    return date_obj.isoformat() if hasattr(date_obj, 'isoformat') else str(date_obj)