from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..config import Config

elderly_bp = Blueprint("elderly", __name__)

SECRET_KEY = Config.DATABASE_ENCRYPTION_KEY

@elderly_bp.route("/elderly", methods=["GET"])
def get_elderly():

    # return None if elderly_id not present
    elderly_id = request.args.get("elderly_id")
    if not elderly_id:
        # TODO: Return a list of all elderly that the user has access to
        return jsonify({"error": "Missing elderly_id"}), 400

    db: Session = next(get_db())
    params = {"elderly_id": elderly_id, "key": SECRET_KEY}

    # Query with decryption using pgp_sym_decrypt
    query = text(f"""
        SELECT
            id,
            pgp_sym_decrypt(name::bytea, :key) AS name,
            pgp_sym_decrypt(date_of_birth::bytea, :key) AS date_of_birth,
            gender,
            pgp_sym_decrypt(nationality::bytea, :key) AS nationality,
            pgp_sym_decrypt(dialect_group::bytea, :key) AS dialect_group,
            marital_status,
            pgp_sym_decrypt(address::bytea, :key) AS address
        FROM elderly_profile
        WHERE id = :elderly_id
    """)

    row = db.execute(query, params).fetchone()
    db.close()

    result = {
        "id": str(row["id"]),
        "name": row["name"],
        "date_of_birth": row["date_of_birth"],
        "gender": row["gender"],
        "nationality": row["nationality"],
        "dialect_group": row["dialect_group"],
        "marital_status": row["marital_status"],
        "address": row["address"]
    }

    return jsonify(result), 200

@elderly_bp.route("/elderly", methods=["POST"])
def post_elderly():
    data = request.json
    required_fields = ["name", "date_of_birth", "gender", "nationality",
                       "dialect_group", "marital_status", "address"]

    # Validate input
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    db: Session = next(get_db())
    try:
        # Insert using pgp_sym_encrypt for sensitive fields
        sql = text(f"""
            INSERT INTO elderly_profile
            (name, date_of_birth, gender, nationality, dialect_group, marital_status, address)
            VALUES (
                pgp_sym_encrypt(:name, :key),
                pgp_sym_encrypt(:date_of_birth, :key),
                :gender::genderenum,
                pgp_sym_encrypt(:nationality, :key),
                pgp_sym_encrypt(:dialect_group, :key),
                :marital_status::maritalenum,
                pgp_sym_encrypt(:address, :key)
            )
            RETURNING id;
        """)

        result = db.execute(sql, {
            "name": data["name"],
            "date_of_birth": data["date_of_birth"],
            "gender": data["gender"],
            "nationality": data["nationality"],
            "dialect_group": data["dialect_group"],
            "marital_status": data["marital_status"],
            "address": data["address"],
            "key": SECRET_KEY
        })
        db.commit()

        new_id = result.scalar_one()
        return jsonify({"id": str(new_id), "message": "Elderly profile created"}), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()
