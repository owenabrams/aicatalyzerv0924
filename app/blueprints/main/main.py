from flask import Blueprint, request, jsonify, current_app
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os
import logging
from app.models import Message  # Assuming you have this model for database logging
from app import db  # For database interaction

# Initialize blueprint
main_bp = Blueprint('main_bp', __name__)

# Load environment variables
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Helper function to send WhatsApp messages
def send_whatsapp_message(user_id, text, media_urls=None):
    try:
        twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=text,
            to=user_id
        )
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {e}")

# Primary /chatgpt route
@main_bp.route('/chatgpt', methods=['POST'])
def chatgpt():
    try:
        incoming_message = request.values.get('Body', '').strip()
        user_id = request.values.get('From', 'unknown').strip()
        user_name = request.values.get('ProfileName', 'unknown').strip()

        logging.info(f"Received message from {user_id} ({user_name}): {incoming_message}")

        # Example processing: Generate response using OpenAI API
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": incoming_message}
        ]

        # Get response from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )

        response_text = response.choices[0].message.content.strip()

        # Send response to user via WhatsApp
        send_whatsapp_message(user_id, response_text)

        logging.info(f"Sending response: {response_text}")
        return '', 200
    except Exception as e:
        logging.error(f"Error in /chatgpt route: {e}")
        return str(MessagingResponse().message("An error occurred while processing your request.")), 500
