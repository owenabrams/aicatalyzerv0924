# app/blueprints/hitlragagent/views.py

from flask import Blueprint
from .functions_for_pipeline import create_agent
from .helper_functions import escape_quotes, retrieve_context_per_question  # Import the function here

import logging

from .agent_workflow import plan_and_execute_app

# Initialize the blueprint
hitlrag_bp = Blueprint('hitlragagent', __name__)


def call_hitlragagent(query):
    logging.info(f"call_hitlragagent received query: {query}")
    try:
        # Step 1.1: Construct inputs for context retrieval
        inputs = {"question": query}

        # Step 1.2: Retrieve the context for the question and log the process
        logging.info(f"Retrieving context for question: {query}")
        retrieval_result = retrieve_context_per_question(inputs)

        # Step 1.3: Check if there's an error in context retrieval
        if 'error' in retrieval_result:
            logging.error(f"Error in context retrieval: {retrieval_result['error']}")
            return "Unable to find relevant information at the moment. Please try asking a different question."
        
        # Step 1.4: Extract context
        context = retrieval_result.get("context", "")
        
        # Step 1.5: Check if the context is empty
        if not context:
            return "No relevant information found in the vector files."

        # Step 1.6: Call the plan_and_execute_app method to process the retrieved context
        state = {"question": query, "context": context}
        response = None
        try:
            logging.info(f"Starting plan_and_execute_app with context: {context}")
            for plan_output in plan_and_execute_app.stream(state):
                for _, state_value in plan_output.items():
                    response = state_value.get('response', "No response found.")
        except Exception as e:
            logging.error(f"Error during plan_and_execute_app: {e}")
            return "An error occurred while generating a response from the retrieved context."

        # Step 1.7: Return the response or a fallback message
        return response or "No response could be generated for the given question."
    
    except Exception as e:
        logging.error(f"Error in call_hitlragagent: {e}")
        return f"An error occurred while processing your request: {str(e)}"
