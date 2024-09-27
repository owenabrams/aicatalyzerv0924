# app/blueprints/main/views.py

from flask import current_app, request, jsonify
from app import db
from app.models import Message
from app.context_manager import save_context, get_context
from .utils import handle_db_query, handle_media_query, send_whatsapp_message, rate_limited  # Import helper functions
from .services import handle_user_query, handle_rag_service_v1, handle_rag_service_v2  # Service functions
from twilio.twiml.messaging_response import MessagingResponse
import openai
import logging
import traceback



from . import main_bp  # Import the blueprint

# Load environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

main_bp = Blueprint('main_bp', __name__)

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

        is_group_message = '@g.us' in user_id

        # Ignore non-bot messages in group chats
        if is_group_message and not incoming_message.lower().startswith(bot_keyword):
            return '', 200

        if is_group_message:
            incoming_message = incoming_message[len(bot_keyword):].strip()

        # Get conversation context
        conversation = get_context(user_id)
        context = conversation.get("context", []) if conversation else []

        # Handle database queries
        if incoming_message.lower().startswith(db_keyword):
            search_query = incoming_message[len(db_keyword):].strip()
            response_text, media_urls = handle_db_query(search_query)
        else:
            # Prepare message for OpenAI
            messages = [
                {"role": "system", "content": "You are a helpful assistant."}
            ]
            if context:
                messages.extend(context)
            messages.append({"role": "user", "content": incoming_message})

            # Generate a response using OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.7,
            )

            response_text = response.choices[0].message.content.strip()
            media_urls = []

            # Handle media-related queries
            if any(word in incoming_message.lower() for word in ["video", "image", "document", "link"]):
                media_response, media_urls = handle_media_query(incoming_message)
                if media_response:
                    response_text = f"{response_text}\n\n{media_response}"

        # Update conversation context
        context.append({"role": "user", "content": incoming_message})
        context.append({"role": "assistant", "content": response_text})
        save_context(user_id, context, incoming_message, response_text, None, None, None, None)

        # Log messages to the database
        user_message = Message(user_id=user_id, user_name=user_name, role='user', content=incoming_message)
        bot_response = Message(user_id=user_id, user_name='Chatbot', role='assistant', content=response_text)
        db.session.add(user_message)
        db.session.add(bot_response)
        db.session.commit()

        # Send response to user via WhatsApp
        send_whatsapp_message(user_id, response_text, media_urls)

        logging.info(f"Sending response: {response_text}")
        return '', 200
    except Exception as e:
        logging.error(f"Error in /chatgpt route: {traceback.format_exc()}")
        return str(MessagingResponse().message("An error occurred while processing your request.")), 500
