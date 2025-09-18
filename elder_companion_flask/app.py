from flask import Flask, jsonify, request
from .config import Config
from .blueprints.stm import stm_bp
from .blueprints.ltm import ltm_bp
from .blueprints.healthcare import healthcare_bp
from .blueprints.profile import elderly_bp
from .utils import init_model

app = Flask(__name__)

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

# Global error handler
@app.errorhandler(Exception)
def handle_all_exceptions(e):
    # TODO: log error in logger
    print(f"Unhandled exception: {e}")
    return jsonify({"error": "Internal Server Error"}), 500
