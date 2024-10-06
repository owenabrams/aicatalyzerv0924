from flask import Blueprint
from .views import hitlrag_bp

# Define the blueprint
hitlrag_bp = Blueprint('hitlragagent', __name__)

# Import views or other necessary modules to register routes
from . import views

