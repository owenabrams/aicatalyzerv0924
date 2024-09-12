from flask import Blueprint

rag_blueprint_faiss = Blueprint('rag_ollama_faiss', __name__)

from . import views
