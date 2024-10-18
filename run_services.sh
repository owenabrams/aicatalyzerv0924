#!/bin/bash

# Define the port for Flask
FLASK_PORT=5000

# Kill any process using the specified port (e.g., Flask server)
function kill_process_on_port() {
    lsof -t -i:$1 | xargs kill -9
}

# Start Flask in the background
start_flask() {
    echo "Starting Flask on port $FLASK_PORT..."
    kill_process_on_port $FLASK_PORT
    # Run Flask in the background
    python run.py &
    FLASK_PID=$!
}

# Start ngrok in the background
start_ngrok() {
    echo "Starting ngrok..."
    # Kill any existing ngrok processes
    pkill -f ngrok
    # Start ngrok in the background and redirect its output to a log file
    ngrok http $FLASK_PORT > /dev/null 2>&1 &
    NGROK_PID=$!
    # Wait a moment to allow ngrok to start and retrieve its URL
    sleep 2
    # Fetch ngrok URL and save it to the .env file
    python start_ngrok.py
}

# Stop all services
stop_services() {
    echo "Stopping Flask and ngrok..."
    kill $FLASK_PID
    kill $NGROK_PID
}

# Main script execution
trap stop_services EXIT  # This ensures services are stopped when the script exits

# Start services
start_flask
start_ngrok

# Wait for Flask process to complete
wait $FLASK_PID



#Give the script execute permission using the following command:

#chmod +x run_services.sh

#Run the Script

#To start your services, use the script:

#./run_services.sh

#This script will automatically start ngrok and Flask, handle port conflicts, and clean up processes when it exits.