# app/blueprints/main/views.py

import os
import logging
import openai
from flask import Blueprint, request, jsonify
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse



from flask import current_app
from app import db
from app.models import Message
from app.context_manager import save_context, get_context
from .utils import handle_db_query, handle_media_query, send_whatsapp_message, rate_limited  # Import helper functions



import traceback




from . import main_bp  # Import the blueprint

# Load environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/test', methods=['GET'])
def test_route():
    return "Test route is working!"



@main_bp.route('/', methods=['GET'])
def index():
    current_app.logger.info("Accessed the home page ('/').")
    return "This is a WhatsApp chatbot powered by GPT-3.5-turbo. Use the /webchat endpoint to interact with the bot."



@main_bp.route('/chatgpt', methods=['POST'])
@rate_limited
def chatgpt():
    try:
        incoming_message = request.values.get('Body', '').strip()
        user_id = request.values.get('From', 'unknown').strip()
        user_name = request.values.get('ProfileName', 'unknown').strip()

        logging.info(f"Received message from {user_id} ({user_name}): {incoming_message}")

        bot_keyword = "bot:"
        db_keyword = "db:"

        # Check if the message is from a group
        is_group_message = '@g.us' in user_id

        if is_group_message and not incoming_message.lower().startswith(bot_keyword):
            logging.info(f"Ignored non-bot message in group: {incoming_message}")
            return '', 200

        if is_group_message:
            incoming_message = incoming_message[len(bot_keyword):].strip()

        # Retrieve conversation context
        conversation = get_context(user_id)
        context = conversation.get("context", []) if conversation else []

        if incoming_message.lower().startswith(db_keyword):
            logging.info(f"Handling database query: {incoming_message}")
            search_query = incoming_message[len(db_keyword):].strip()
            response_text, media_urls = handle_db_query(search_query)
        else:
            logging.info(f"Processing user message with OpenAI: {incoming_message}")
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Understand and respond appropriately to greetings, questions, and statements in various languages."}
            ]
            if context:
                # Limit context to the last 5 messages
                messages.extend(context[-5:])
            messages.append({"role": "user", "content": incoming_message})

            # Interacting with OpenAI API
            try:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=150,
                    temperature=0.7,
                )
                response_text = response.choices[0].message.content.strip()
                media_urls = []
                logging.info(f"OpenAI Response: {response_text}")

                if any(word in incoming_message.lower() for word in ["video", "image", "document", "link"]):
                    media_response, media_urls = handle_media_query(incoming_message)
                    if media_response:
                        response_text = f"{response_text}\n\n{media_response}"
            except Exception as e:
                logging.error(f"Error while interacting with OpenAI API: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        # Update conversation context
        context.append({"role": "user", "content": incoming_message})
        context.append({"role": "assistant", "content": response_text})
        save_context(user_id, context, incoming_message, response_text, None, None, None, None)

        # Log messages to the database
        try:
            user_message = Message(user_id=user_id, user_name=user_name, role='user', content=incoming_message)
            bot_response = Message(user_id=user_id, user_name='Chatbot', role='assistant', content=response_text)
            db.session.add(user_message)
            db.session.add(bot_response)
            db.session.commit()
            logging.info(f"Messages successfully logged to the database for user: {user_id}")
        except Exception as e:
            logging.error(f"Error saving messages to database: {e}")

        # Send response to user via WhatsApp
        try:
            send_whatsapp_message(user_id, response_text, media_urls)
            logging.info(f"Sent response to user {user_id}: {response_text}")
        except Exception as e:
            logging.error(f"Error sending WhatsApp message: {e}")

        return '', 200
    except Exception as e:
        logging.error(f"Error in /chatgpt route: {traceback.format_exc()}")
        return str(MessagingResponse().message("An error occurred while processing your request.")), 500
