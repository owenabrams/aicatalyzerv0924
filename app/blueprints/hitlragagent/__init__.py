from flask import Blueprint
from .views import hitlrag_bp

# app/blueprints/hitlragagent/__init__.py

from .hitlragagent import get_hitlragagent_response

# Define the blueprint
hitlrag_bp = Blueprint('hitlragagent', __name__)

# Import views or other necessary modules to register routes
from . import views

