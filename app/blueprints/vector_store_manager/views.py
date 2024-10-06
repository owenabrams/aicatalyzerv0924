# app/vector_store_manager/views.py

from flask import Blueprint, request, jsonify
from .manager import VectorStoreManager

vector_store_bp = Blueprint('vector_store_manager', __name__)
vector_manager = VectorStoreManager('chunks_vector_store')

@vector_store_bp.route('/vector_store/add', methods=['POST'])
def add_documents():
    data = request.json
    documents = data.get('documents', [])
    vector_manager.add_documents(documents)
    return jsonify({"status": "success", "message": "Documents added successfully."})

@vector_store_bp.route('/vector_store/search', methods=['GET'])
def search_documents():
    query = request.args.get('query', '')
    results = vector_manager.search(query)
    return jsonify({"results": results})
