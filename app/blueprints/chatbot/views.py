from flask import Blueprint, request, jsonify, session, current_app
import openai
import os
import logging
import traceback
import uuid
from datetime import datetime, timedelta
from functools import wraps
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re
from app.context_manager import save_context, get_context  # Assuming these are defined in your app
from app.models import Message  # Assuming Message model is used to save conversation history

from fuzzywuzzy import process, fuzz
from app.models import QuestionNew, LinkNew, VideoNew, PictureNew, DocumentNew


# Create a Blueprint
chatbot_bp = Blueprint('chatbot_bp', __name__)

# Initialize the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY_CHATBOT1")

# Initialize the Twilio client
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
twilio_client = Client(twilio_account_sid, twilio_auth_token)

def preprocess_text(text):
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    text = text.lower()
    text = re.sub(r'\b\w{1,2}\b', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = ' '.join(lemmatizer.lemmatize(word) for word in text.split() if word not in stop_words)
    return text

def send_whatsapp_message(user_id, text, media_urls):
    try:
        max_length = 1600
        message_chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]

        for idx, chunk in enumerate(message_chunks):
            part_number = f"Part {idx + 1}/{len(message_chunks)}: " if len(message_chunks) > 1 else ""
            chunk_with_part = part_number + chunk
            twilio_client.messages.create(
                from_=twilio_whatsapp_number,
                body=chunk_with_part,
                to=user_id
            )

        for media_url in media_urls:
            twilio_client.messages.create(
                from_=twilio_whatsapp_number,
                body="Here is the media you requested:",
                media_url=[media_url],
                to=user_id
            )
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {e}")


# Rate limiting
user_requests = defaultdict(list)
RATE_LIMIT = 5  # Number of requests
TIME_PERIOD = 60  # Time period in seconds

def rate_limited(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            user_id = str(uuid.uuid4())
            session['user_id'] = user_id

        current_time = datetime.now()
        # Remove old requests outside the time period
        user_requests[user_id] = [t for t in user_requests[user_id] if current_time - t < timedelta(seconds=TIME_PERIOD)]

        # Check if rate limit is exceeded
        if len(user_requests[user_id]) >= RATE_LIMIT:
            return jsonify({"response": "Rate limit exceeded. Please try again later."}), 429

        user_requests[user_id].append(current_time)
        return f(*args, **kwargs)
    return decorated_function



# Define a function to generate answers using GPT-3
def generate_answer(question):
    model_engine = "text-davinci-002"
    prompt = (f"Q: {question}\\n"
              "A:")

    response = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.7,
    )

    answer = response.choices[0].text.strip()
    return answer




def handle_db_query(query):
    try:
        logging.info(f"Searching database for query: {query}")

        # Determine the type of content to search for based on keywords
        media_type = None
        if 'link' in query:
            media_type = 'link'
        elif 'video' in query:
            media_type = 'video'
        elif 'picture' in query or 'image' in query:
            media_type = 'picture'
        elif 'document' in query or 'pdf' in query:
            media_type = 'pdf'

        # Remove keywords from the query to clean it up
        if media_type:
            query = query.replace('links', '').replace('link', '').replace('videos', '').replace('video', '')
            query = query.replace('pictures', '').replace('picture', '').replace('images', '').replace('image', '')
            query = query.replace('documents', '').replace('document', '').replace('pdf', '').strip()

        # Perform an exact search for questions matching the query
        exact_results = QuestionNew.query.filter(
            QuestionNew.text.ilike(f'%{query}%')
        ).all()

        if exact_results:
            logging.info(f"Found {len(exact_results)} exact matching results.")
            return format_db_results(exact_results, media_type)

        # If no exact matches, find similar results using fuzzy matching
        all_questions = QuestionNew.query.all()
        question_texts = [question.text for question in all_questions]
        close_matches = process.extract(query, question_texts, limit=5, scorer=fuzz.token_set_ratio)

        if close_matches:
            close_results = [all_questions[i] for i in [question_texts.index(match[0]) for match in close_matches if match[1] > 70]]
            if close_results:
                logging.info(f"Found {len(close_results)} close matching results.")
                return format_db_results(close_results, media_type)

        logging.info("No matching results found.")
        return "No matching results found in the database.", []

    except Exception as e:
        logging.error(f"Error performing database search: {e}")
        return "An error occurred while searching the database.", []

def format_db_results(results, media_type=None):
    response_text = "Database search results:\n"
    media_urls = []

    for result in results:
        # Append links
        if not media_type or media_type == 'link':
            if result.links:
                response_text += "Links: " + ", ".join([link.url for link in result.links]) + "\n"
                media_urls.extend([link.url for link in result.links])
        
        # Append videos
        if not media_type or media_type == 'video':
            if result.videos:
                response_text += "Videos: " + ", ".join([video.url for video in result.videos]) + "\n"
                media_urls.extend([video.url for video in result.videos])
        
        # Append pictures
        if not media_type or media_type == 'picture':
            if result.pictures:
                response_text += "Pictures: " + ", ".join([picture.url for picture in result.pictures]) + "\n"
                media_urls.extend([picture.url for picture in result.pictures])
        
        # Append documents
        if not media_type or media_type == 'pdf':
            if result.documents:
                response_text += "Documents: " + ", ".join([document.url for document in result.documents]) + "\n"
                media_urls.extend([document.url for document in result.documents])

        # Add the question and answer if no specific media type is being searched for
        if not media_type:
            response_text += f"Question: {result.text}\nAnswer: {result.answers[0].text}\n"

    return response_text.strip(), media_urls



# Define a route to handle incoming requests
@chatbot_bp.route('/chatgpt', methods=['POST'])
@rate_limited
def chatgpt():
    try:
        incoming_message = request.values.get('Body', '').strip()
        user_id = request.values.get('From', 'unknown').strip()
        user_name = request.values.get('ProfileName', 'unknown').strip()

        logging.info(f"Received message from {user_id} ({user_name}): {incoming_message}")

        # Handle different keywords
        bot_keyword = "bot:"
        db_keyword = "db:"
        is_group_message = '@g.us' in user_id

        if is_group_message and not incoming_message.lower().startswith(bot_keyword):
            return '', 200  # Ignore group messages without the bot keyword

        if is_group_message:
            incoming_message = incoming_message[len(bot_keyword):].strip()

        # Retrieve and maintain conversation context
        conversation = get_context(user_id)
        context = conversation.get("context", []) if conversation else []

        # Handle database-specific queries
        if incoming_message.lower().startswith(db_keyword):
            search_query = incoming_message[len(db_keyword):].strip()
            response_text, media_urls = handle_db_query(search_query)
        else:
            # Use OpenAI for regular conversation
            messages = [{"role": "system", "content": "You are a helpful assistant."}]
            if context:
                messages.extend(context[-5:])  # Include last 5 messages in context
            messages.append({"role": "user", "content": incoming_message})

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.7,
            )

            response_text = response.choices[0].message.content.strip()
            media_urls = []

        # Update conversation context
        context.append({"role": "user", "content": incoming_message})
        context.append({"role": "assistant", "content": response_text})
        save_context(user_id, context, incoming_message, response_text, None, None, None, None)

        # Save the conversation to the database
        user_message = Message(user_id=user_id, user_name=user_name, role='user', content=incoming_message)
        bot_response = Message(user_id=user_id, user_name='Chatbot', role='assistant', content=response_text)
        db.session.add(user_message)
        db.session.add(bot_response)
        db.session.commit()

        # Send the response via WhatsApp
        send_whatsapp_message(user_id, response_text, media_urls)

        logging.info(f"Sending response: {response_text}")
        return '', 200
    except Exception as e:
        logging.error(f"Error in /chatgpt route: {traceback.format_exc()}")
        return str(MessagingResponse().message("An error occurred while processing your request.")), 500
