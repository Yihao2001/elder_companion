from flask import Blueprint, request, jsonify, g
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..config import Config
from ..models import ElderlyProfile, user_elderly

elderly_bp = Blueprint("elderly", __name__)

SECRET_KEY = Config.DATABASE_ENCRYPTION_KEY

@elderly_bp.route("/elderly", methods=["GET"])
def get_elderly():
    """
    If elderly_id provided, return a single row 
    Else return a list of all elderly information that the user has access to
    """
    
    db: Session = next(get_db())

    try:
        user_id = g.get("user_id")
        user_role = g.get("user_role")
        if not user_id or not user_role:
            return jsonify({"error": "Missing user_id or user_role in flask context"}), 500

        elderly_id = request.args.get("elderly_id")

        if elderly_id:
            # Fetch single elderly row with decryption
            params = {"elderly_id": elderly_id, "key": SECRET_KEY}
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

            if not row:
                return jsonify({"error": "Elderly not found"}), 404

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

        else:
            # Fetch all accessible elderly IDs first
            if user_role == "super_admin":
                accessible_ids = [e.id for e in db.query(ElderlyProfile.id).distinct().all()]
            else:
                accessible_ids = [eid[0] for eid in (
                    db.query(user_elderly.c.elderly_id)
                      .filter(user_elderly.c.user_id == user_id)
                      .distinct()
                      .all()
                )]

            if not accessible_ids:
                return jsonify([]), 200

            # Fetch full decrypted info for all accessible elderly
            params = {"key": SECRET_KEY, "ids": accessible_ids}
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
                WHERE id = ANY(:ids)
            """)

            rows = db.execute(query, params).fetchall()

            result = [
                {
                    "id": str(r["id"]),
                    "name": r["name"],
                    "date_of_birth": r["date_of_birth"],
                    "gender": r["gender"],
                    "nationality": r["nationality"],
                    "dialect_group": r["dialect_group"],
                    "marital_status": r["marital_status"],
                    "address": r["address"]
                }
                for r in rows
            ]

            return jsonify(result), 200

    finally:
        db.close()
