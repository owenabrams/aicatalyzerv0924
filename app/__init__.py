# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    # Create Flask app instance
    app = Flask(__name__)

    # Load environment variables
    load_dotenv()

    # Set configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress warning

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

def setup_logging(app):
    import logging
    logging.basicConfig(level=logging.INFO)
    app.logger.info("Logging is set up successfully.")
