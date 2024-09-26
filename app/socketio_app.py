# app/socketio_app.py

from flask_socketio import SocketIO, emit
from app import create_app
from app.main import process_message  # Import the process_message function

socketio = SocketIO()

def run_socketio():
    app = create_app()
    socketio.init_app(app)
    socketio.run(app)

@socketio.on('send_message')
def handle_send_message(data):
    logging.info(f"Received message: {data['message']}")
    message = data['message']
    # Process the message and generate a response
    response = process_message(message)
    emit('receive_message', {'message': response}, broadcast=False)
