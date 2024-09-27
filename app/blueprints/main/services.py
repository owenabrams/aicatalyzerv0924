from app.blueprints.rag_service_v1.rag import MultiDocRAGSystem as RAGServiceV1
from app.blueprints.rag_service_v2.rag import MultiDocRAGSystem as RAGServiceV2

def handle_user_query(question):
    if "startup" in question.lower():
        return handle_rag_service_v1(question)
    elif "new feature" in question.lower():
        return handle_rag_service_v2(question)
    else:
        return {"error": "No matching service found for this query."}, 404

def handle_rag_service_v1(question):
    rag_system = RAGServiceV1()
    rag_system.load_vector_store()
    return {"answer": rag_system.query(question)}, 200

def handle_rag_service_v2(question):
    rag_system = RAGServiceV2()
    rag_system.load_vector_store()
    return {"answer": rag_system.query(question)}, 200
