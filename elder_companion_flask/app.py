from flask import Flask, jsonify, request
from functools import wraps
from .config import Config
from .blueprints.stm import stm_bp
from .blueprints.ltm import ltm_bp
from .blueprints.healthcare import healthcare_bp
from .blueprints.profile import elderly_bp
from .utils import init_model

app = Flask(__name__)

# Register blueprints
app.register_blueprint(stm_bp)
app.register_blueprint(ltm_bp)
app.register_blueprint(healthcare_bp)
app.register_blueprint(elderly_bp)

@app.route("/")
def home():
    return jsonify({"status": "elder-companion-flask running"}), 200

# Initialise embedding model upon app start
init_model()

# Decorator to check for authorisation token in ALL endpoints
# To whitelist endpoint, add it inside the function
@app.before_request
def require_authorisation(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401

        token = auth_header.split(" ")[1]
        if token != Config["AUTHORISATION_TOKEN"]:
            return jsonify({"error": "Invalid key"}), 403

        return f(*args, **kwargs)
    return wrapper
