from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from flask_jwt_extended import create_access_token
import bcrypt
from ..db import get_db
from ..models import User, user_elderly, RoleEnum
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

@login_bp.route("/create-user", methods=["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    elderly_ids = data.get("elderly_ids", [])

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    db = next(get_db())

    # 1) Check existing username
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return jsonify({"error": "Username already exists"}), 409

    # 2) Hash password
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    # 3) Create user
    user = User(
        username=username,
        password_hash=hashed_password,
        role=RoleEnum.caregiver
    )
    db.add(user)
    db.flush()   # <-- ensures user.id is generated before we insert user_elderly

    # 4) Add user-elderly relationships
    for eid in elderly_ids:
        db.execute(
            user_elderly.insert().values(
                user_id=user.id,
                elderly_id=eid
            )
        )

    # 5) Commit and return
    db.commit()
    db.refresh(user)
    db.close()

    return jsonify({
        "message": "User created successfully",
        "user_id": str(user.id),
        "linked_elderly": elderly_ids
    }), 201
