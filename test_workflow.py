# test_workflow.py

from app.blueprints.hitlragagent.agent_workflow import plan_and_execute_app

inputs = {
    "question": "What is the capital of France?",
    "context": "",
    "relevant_context": "",
    "response": ""
}

try:
    result = plan_and_execute_app(inputs)
    print(f"Workflow execution result: {result}")
except Exception as e:
    print(f"Error executing workflow: {e}")
