from flask import Flask, jsonify
from huggingface_hub import login
from sentence_transformers import SentenceTransformer
from .config import Config
from .blueprints.stm import stm_bp
from .blueprints.ltm import ltm_bp
from .blueprints.healthcare import healthcare_bp
from .blueprints.profile import elderly_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(stm_bp)
app.register_blueprint(ltm_bp)
app.register_blueprint(healthcare_bp)
app.register_blueprint(elderly_bp)

@app.route("/")
def home():
    return jsonify({"status": "elder-companion-flask running"}), 200

def init_model():
    """
    Initialise model and store it globally when app starts
    """
    global _model
    login(Config.HUGGINGFACE_TOKEN)
    _model = SentenceTransformer("google/embeddinggemma-300m")

# Initialise embedding model upon app start
init_model()