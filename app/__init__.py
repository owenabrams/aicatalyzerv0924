# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

from app.models import *  # Import all models

# Import the blueprints here
from app.blueprints.vector_manager.views import vector_manager_bp

def create_app():
    # Create Flask app instance
    app = Flask(__name__)

    # Load environment variables
    load_dotenv()

    # Use an absolute path for the SQLite database file
    db_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database')

    # Ensure the directory for the database exists
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Set the absolute path for the database file
    db_path = os.path.join(db_dir, 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{db_path}')
    print(f"Database file path: {db_path}")

    # Other configurations
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv('SECRET_KEY', 'your-default-secret-key')  # For session management

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    register_blueprints(app)

    # Set up logging for debugging
    setup_logging(app)

    return app

def register_blueprints(app):
    # Import and register blueprints
    from app.blueprints.main import main_bp
    app.register_blueprint(main_bp, url_prefix='/')

    from app.blueprints.home import home_blueprint
    app.register_blueprint(home_blueprint, url_prefix='/home')

    from app.blueprints.chatbot import chatbot_bp
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')

    # Register hitlragagent blueprint
    from app.blueprints.hitlragagent import hitlrag_bp
    app.register_blueprint(hitlrag_bp, url_prefix='/hitlragagent')

    # Register vector_manager blueprint
    app.register_blueprint(vector_manager_bp, url_prefix='/vector_manager')

def setup_logging(app):
    import logging
    logging.basicConfig(level=logging.INFO)
    app.logger.info("Logging is set up successfully.")
