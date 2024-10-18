# run.py
import sys

import os
import subprocess
from app import create_app

from app.blueprints.hitlragagent.agent_workflow import plan_and_execute_app


# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get Ngrok auth token and Flask port
ngrok_auth_token = os.getenv('2gMrHPKhMX5KCzz18Xt5lZ7PxcB_7Wt7FMgrfeMaYiSgjq1rA')
flask_port = 5000

# Add the 'app' directory to the system path
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

# Add the parent directory of 'run.py' to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print(sys.path)  # Debug: Print sys.path for verification

if ngrok_auth_token:
    # Start Ngrok in a separate process
    subprocess.run(["ngrok", "config", "add-authtoken", ngrok_auth_token])
    subprocess.Popen(["ngrok", "http", str(flask_port)])

app = create_app()

# Log all registered routes
with app.app_context():
    for rule in app.url_map.iter_rules():
        print(f"Registered route: {rule} -> {rule.endpoint}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=flask_port, debug=True)


