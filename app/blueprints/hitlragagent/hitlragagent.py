# hitlragagent.py
import logging
import traceback
from langchain_openai import ChatOpenAI
from app.blueprints.hitlragagent.vector_store_manager import VectorStoreManager

# Initialize vector store manager
VECTOR_STORE_NAME = "enhanced_vector_store"
vector_store_manager = VectorStoreManager(VECTOR_STORE_NAME)

def get_hitlragagent_response(question):
    """
    Get a response from the HITLRAG agent based on the user's question.
    """
    try:
        # Use vector store manager to answer the question
        response = vector_store_manager.answer_question(question)

        # Extract the answer content
        answer_content = response.get('answer', "An error occurred while generating the response.")
        return answer_content
    except Exception as e:
        logging.error(f"Error in get_hitlragagent_response: {traceback.format_exc()}")
        return "An error occurred while processing your request."

