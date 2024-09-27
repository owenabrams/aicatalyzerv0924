from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

from app.blueprints.main import main_bp  # Import the main blueprint

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Load environment variables
    load_dotenv()

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints here
    from app.blueprints.home import home_blueprint
    from app.blueprints.rag_ollama_faiss import rag_blueprint_faiss
    from app.blueprints.main import main_bp
    

    app.register_blueprint(home_blueprint)
    app.register_blueprint(rag_blueprint_faiss, url_prefix='/api/faiss')
    app.register_blueprint(main_bp, url_prefix='/')  # Register the main blueprint

    return app
