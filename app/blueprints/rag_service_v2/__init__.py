from flask import Blueprint

rag_blueprint_v2 = Blueprint('rag_v2', __name__)

from . import views
