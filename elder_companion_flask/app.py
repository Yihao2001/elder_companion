from flask import Flask, jsonify
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
