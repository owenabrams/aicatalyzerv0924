# run.py
import os
import subprocess
from app import create_app

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get Ngrok auth token and Flask port
ngrok_auth_token = os.getenv('2gMrHPKhMX5KCzz18Xt5lZ7PxcB_7Wt7FMgrfeMaYiSgjq1rA')
flask_port = 5000

if ngrok_auth_token:
    # Start Ngrok in a separate process
    subprocess.run(["ngrok", "config", "add-authtoken", ngrok_auth_token])
    subprocess.Popen(["ngrok", "http", str(flask_port)])

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=flask_port, debug=True)


