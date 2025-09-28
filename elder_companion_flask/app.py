from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager,verify_jwt_in_request, get_jwt_identity
from flask_cors import CORS
from sqlalchemy.orm import Session
import datetime
from .config import Config
from .blueprints.stm import stm_bp
from .blueprints.ltm import ltm_bp
from .blueprints.healthcare import healthcare_bp
from .blueprints.profile import elderly_bp
from .utils import init_model
from .db import get_db
from .models import User

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=24)

jwt = JWTManager(app)

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Add a before_request handler to handle OPTIONS requests
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        response.headers.add('Access-Control-Allow-Credentials', "true")
        return response

# Register blueprints
# URL: <METHOD> /api/<MODULE>
# GET /api/stm
app.register_blueprint(stm_bp, url_prefix="/api")
app.register_blueprint(ltm_bp, url_prefix="/api")
app.register_blueprint(healthcare_bp, url_prefix="/api")
app.register_blueprint(elderly_bp, url_prefix="/api")

# Initialise embedding model upon app startß
init_model()

# Decorator to check for authorisation token in ALL endpoints
# To whitelist endpoint, add it inside the function
@app.before_request
def require_authorisation():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401

    token = auth_header.split(" ")[1]
    if token != Config.AUTHORIZATION_TOKEN:
        return jsonify({"error": "Invalid key"}), 403

# TODO: Enable this middleware once we implement RBAC 
# @app.before_request
# def verify_jwt():
#     # skip jwt check if it is login 
#     if request.endpoint == "login":
#         return None
#     try:
#         # checks if jwt exists inside the authorisation header and if it has expired
#         verify_jwt_in_request()
#     except Exception:
#         return jsonify({"error": "Missing or invalid JWT"}), 401
    
#     # retrieve user_id and user_role from the jwt
#     current_user = get_jwt_identity()
#     user_id, user_role = current_user["user_id"], current_user["user_role"]
#     db: Session = next(get_db())
#     user = db.session.query(User).get(user_id)

#     # Check if user_id from the jwt exists in db
#     if not user:
#         return jsonify({"error": "user_id does not exist"}), 400

#     # Check if elderly_id is provided in query param or body
#     elderly_id = request.view_args.get("elderly_id") or request.args.get("elderly_id")
#     if not elderly_id:
#         return None

#     # Super admin can access everything
#     if user_role == "super_admin":
#         return None

#     # Check if user has permission to access elderly info
#     allowed_ids = [str(e.id) for e in user.elderly]
#     if elderly_id not in allowed_ids:
#         return jsonify({"error": "You cannot access this elderly"}), 403

#     return None

# Global error handler
@app.errorhandler(Exception)
def handle_all_exceptions(e):
    # TODO: log error in logger
    print(f"Unhandled exception: {e}")
    return jsonify({"error": "Internal Server Error"}), 500
