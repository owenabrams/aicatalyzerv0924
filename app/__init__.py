from flask import Flask
from app.blueprints.home import home_blueprint
from app.blueprints.rag_ollama_faiss import rag_blueprint_faiss
from dotenv import load_dotenv
import os

def create_app():
    app = Flask(__name__)

    # Load environment variables
    load_dotenv()

    # Register blueprints here
    from app.blueprints.home import home_blueprint
    from app.blueprints.rag_ollama_faiss import rag_blueprint_faiss
    
    app.register_blueprint(home_blueprint)
    app.register_blueprint(rag_blueprint_faiss, url_prefix='/api/faiss')

    return app
