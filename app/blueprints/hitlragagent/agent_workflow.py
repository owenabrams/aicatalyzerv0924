from langgraph.graph import StateGraph, END
from typing import TypedDict
import logging

from .helper_functions import retrieve_context_per_question, keep_only_relevant_content, answer_question_from_context

# Define the state dictionary for the agent's plan execution
class PlanExecute(TypedDict):
    question: str
    context: str
    relevant_context: str
    response: str

# Create the state graph
agent_workflow = StateGraph(PlanExecute)

# Add nodes to the state graph
agent_workflow.add_node("retrieve_context", retrieve_context_per_question)
agent_workflow.add_node("filter_content", keep_only_relevant_content)
agent_workflow.add_node("generate_answer", answer_question_from_context)

# Define edges (transitions) between the nodes
agent_workflow.add_edge("retrieve_context", "filter_content")  # Link the first step to the second
agent_workflow.add_edge("filter_content", "generate_answer")  # Link the second step to the third
agent_workflow.add_edge("generate_answer", END)  # Mark the end of the workflow

# Compile the agent workflow
compiled_agent_workflow = agent_workflow.compile()

# Define the plan_and_execute_app function to handle input, output, and logging
def plan_and_execute_app(inputs):
    logging.info(f"Received inputs for planning: {inputs}")

    # Execute the compiled agent workflow
    try:
        state = inputs
        for plan_output in compiled_agent_workflow.stream(state):
            logging.info(f"Plan output at each step: {plan_output}")
            for _, state_value in plan_output.items():
                output = state_value.get('response', "No response found.")
        
        # Log the output before returning
        logging.info(f"Output generated by plan_and_execute_app: {output}")
        return output

    except Exception as e:
        logging.error(f"Error in plan_and_execute_app: {e}")
        return f"An error occurred during the execution of the plan: {str(e)}"
