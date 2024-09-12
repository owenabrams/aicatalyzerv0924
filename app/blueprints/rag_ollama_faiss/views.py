from flask import Blueprint, request, jsonify
from .rag import MultiDocRAGSystem
import os

rag_blueprint_faiss = Blueprint('rag_ollama_faiss', __name__)

# Initialize the RAG system (can be configured with Pinecone or FAISS)
rag_system = MultiDocRAGSystem(
    vectorstore_path="vectorstore_faiss.faiss",  # Path for FAISS storage for RAG Ollama FAISS
    model_name="llama3.1",
    pinecone_api_key=os.getenv("PINECONE_API_KEY"),  # From environment variables
    pinecone_index_name="ragfaissindex",
    use_faiss=True  # Set to False to use Pinecone instead of FAISS
)

@rag_blueprint_faiss.route('/rag/upload', methods=['POST'])
def upload_pdfs():
    folder_path = request.json.get('folder_path')
    if not folder_path or not os.path.isdir(folder_path):
        return jsonify({"error": "Invalid folder path"}), 400

    try:
        rag_system.load_pdfs_and_create_vector_store(folder_path=folder_path)
        return jsonify({"message": "Vector store created/updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rag_blueprint_faiss.route('/rag/query', methods=['POST'])
def query_rag_service():
    question = request.json.get('question')
    if not question:
        return jsonify({"error": "Question is required"}), 400

    try:
        rag_system.load_vector_store()
        rag_system.setup_llm()
        answer = rag_system.query(question)
        return jsonify({"answer": answer}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
