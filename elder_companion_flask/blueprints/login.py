from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from flask_jwt_extended import create_access_token
from ..db import get_db
from ..models import User
from ..utils import check_password

login_bp = Blueprint("login", __name__)

@login_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    # Find user
    db: Session = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    hashed_password = user.password_hash
    if not user or not check_password(plain_password=password, hashed_password=hashed_password):
        return jsonify({"error": "Invalid username or password"}), 401

    # Create JWT token
    # NOTE: Flask-jwt-extended will encode identity param as 'sub' inside the jwt returned
    jwt_token = create_access_token(identity = str(user.id), additional_claims = {"user_role": user.role.value, "username": username})
    return jsonify({"jwt_token": jwt_token})
