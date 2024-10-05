from flask import current_app
from app.blueprints.rag_service_v1.rag import MultiDocRAGSystem as RAGServiceV1
from app.blueprints.rag_service_v2.rag import MultiDocRAGSystem as RAGServiceV2

'''
Supporting Imports
The /chatgpt route depends on various external libraries, functions, and 
modules to operate. Below are the relevant imports:
'''
import openai
from flask import request, jsonify
import logging
from app import db  # For database interaction
from app.context_manager import save_context, get_context  # Managing conversation context
from app.models import Message  # Message model for database logging
from twilio.rest import Client  # For sending WhatsApp messages
from twilio.twiml.messaging_response import MessagingResponse  # For creating response messages
from functools import wraps  # Used for the @rate_limited decorator
import traceback  # For error handling and logging

"""
/End of supporting Imports * * *
"""

from app import db, socketio
from app.context_manager import save_context, get_context
from app.assistant import start_assistant_function, stop_assistant_function

# Import your models here
from app.models import db, Message, QuestionNew, AnswerNew, LinkNew, VideoNew, PictureNew, DocumentNew, TrainingData, Transcription, VideoMetadata


from app.models import Message, QuestionNew, AnswerNew, LinkNew, VideoNew, PictureNew, DocumentNew, TrainingData, VideoMetadata
from app.rag import transcribe_audio, process_pdf, classify_disease, ask_question, allowed_file

# Load environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY must be set")

client = OpenAI(api_key=openai.api_key)

# Initialize the Twilio client
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
if not twilio_account_sid or not twilio_auth_token:
    raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set")
twilio_client = Client(twilio_account_sid, twilio_auth_token)

# Check if the environment variables are correctly loaded
logging.info(f"TWILIO_ACCOUNT_SID: {twilio_account_sid}")
logging.info(f"TWILIO_AUTH_TOKEN: {twilio_auth_token[:5]}...")  # Only show the first 5 characters for security
logging.info(f"OPENAI_API_KEY: {openai.api_key[:5]}...")  # Only show the first 5 characters for security
logging.info(f"TWILIO_WHATSAPP_NUMBER: {twilio_whatsapp_number[:5]}...")  # Only show the first 5 characters for security

model = SentenceTransformer('all-MiniLM-L6-v2')

# Ensure the required NLTK data is downloaded
nltk.download('stopwords')
nltk.download('wordnet')

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")


# Directory to save uploaded files
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp4', 'avi', 'mov', 'srt'}
main_bp.config = {'UPLOAD_FOLDER': os.path.join(os.path.dirname(__file__), UPLOAD_FOLDER)}

# Ensure the upload directory exists
if not os.path.exists(main_bp.config['UPLOAD_FOLDER']):
    os.makedirs(main_bp.config['UPLOAD_FOLDER'])

# Rate limiting
user_requests = defaultdict(list)
RATE_LIMIT = 5
TIME_PERIOD = 60

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_text(text):
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    text = text.lower()
    text = re.sub(r'\b\w{1,2}\b', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = ' '.join(lemmatizer.lemmatize(word) for word in text.split() if word not in stop_words)
    return text


@socketio.on('send_message')
def handle_send_message(data):
    current_app.logger.info(f"Received message: {data['message']}")
    message = data['message']
    response = process_message(message)
    current_app.logger.info(f"Emitting response: {response}")
    emit('receive_message', {'message': response}, broadcast=False)



def handle_user_query(question):
    if "startup" in question.lower():
        return handle_rag_service_v1(question)
    elif "new feature" in question.lower():
        return handle_rag_service_v2(question)
    else:
        return {"error": "No matching service found for this query."}, 404

def handle_rag_service_v1(question):
    rag_system = RAGServiceV1()
    rag_system.load_vector_store()
    return {"answer": rag_system.query(question)}, 200

def handle_rag_service_v2(question):
    rag_system = RAGServiceV2()
    rag_system.load_vector_store()
    return {"answer": rag_system.query(question)}, 200





#Helper Functions and Decorators
#These functions assist the /chatgpt route in various ways, 
#such as rate limiting, handling media queries, sending messages, and interacting with external services.

#a. Rate Limiting Decorator: @rate_limited
#This decorator is used to limit the number of requests a user can make within a specified time period.

def rate_limited(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            user_id = str(uuid.uuid4())
            session['user_id'] = user_id

        current_time = datetime.now()
        user_requests[user_id] = [t for t in user_requests[user_id] if current_time - t < timedelta(seconds=TIME_PERIOD)]
        if len(user_requests[user_id]) >= RATE_LIMIT:
            return jsonify({"response": "Rate limit exceeded. Please try again later."})
        user_requests[user_id].append(current_time)
        return f(*args, **kwargs)
    return decorated_function

#b. Retrieve and Save Conversation Context
#These functions handle the retrieval and saving of user conversation context.
#get_context(user_id):
    #Retrieves the current context for a given user_id.
#save_context(user_id, context, ...):
    #Saves the context of the conversation, including the user's input and assistant's response.

#c. Database and Media Handling: handle_db_query and handle_media_query
#handle_db_query(search_query):
    #Interacts with the database to search for the query and return relevant results.
#handle_media_query(incoming_message):
    #Processes media-related messages (videos, images, documents, links) and formulates a response.

def handle_db_query(query):
    from app.models import QuestionNew  # Deferred import
    try:
        logging.info(f"Searching for query: {query}")

        media_type = None
        if 'link' in query:
            media_type = 'link'
        elif 'video' in query:
            media_type = 'video'
        elif 'picture' in query or 'image' in query:
            media_type = 'picture'
        elif 'document' in query or 'pdf' in query:
            media_type = 'pdf'

        if media_type:
            query = query.replace('links', '').replace('link', '').replace('videos', '').replace('video', '').replace('pictures', '').replace('picture', '').replace('images', '').replace('image', '').replace('documents', '').replace('document', '').replace('pdf', '').strip()

        exact_results = QuestionNew.query.filter(
            QuestionNew.text.ilike(f'%{query}%')
        ).all()

        if exact_results:
            logging.info(f"Found {len(exact_results)} exact matching results.")
            return format_db_results(exact_results, media_type)

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



def handle_media_query(query):
    from app.models import QuestionNew  # Deferred import
    try:
        media_type = None
        if 'video' in query:
            media_type = 'video'
        elif 'image' in query or 'picture' in query:
            media_type = 'picture'
        elif 'pdf' in query or 'document' in query:
            media_type = 'pdf'
        elif 'link' in query:
            media_type = 'link'

        if media_type:
            topic_match = re.search(r"on (.+)", query)
            if topic_match:
                topic = topic_match.group(1).strip()
                media_results = find_media_on_topic(media_type, topic)
                if media_results:
                    response_text = f"Here are some {media_type}s related to '{topic}':\n"
                    media_urls = []
                    for result in media_results:
                        if media_type == 'video':
                            if result.videos:
                                media_urls.extend([video.url for video in result.videos])
                                response_text += "Videos: " + ", ".join([video.url for video in result.videos]) + "\n"
                        elif media_type == 'picture':
                            if result.pictures:
                                media_urls.extend([picture.url for picture in result.pictures])
                                response_text += "Pictures: " + ", ".join([picture.url for picture in result.pictures]) + "\n"
                        elif media_type == 'pdf':
                            if result.documents:
                                media_urls.extend([document.url for document in result.documents])
                                response_text += "Documents: " + ", ".join([document.url for document in result.documents]) + "\n"
                        elif media_type == 'link':
                            if result.links:
                                media_urls.extend([link.url for link in result.links])
                                response_text += "Links: " + ", ".join([link.url for link in result.links]) + "\n"
                    return response_text, media_urls
                else:
                    return f"No {media_type}s found related to '{topic}'.", []
        return None, []
    except Exception as e:
        logging.error(f"Error handling media query: {e}")
        return None, []


#d. Sending WhatsApp Messages: send_whatsapp_message
#This function uses the Twilio client to send text and media messages to a user on WhatsApp.

def send_whatsapp_message(user_id, text, media_urls):
    try:
        max_length = 1600
        message_chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]

        for idx, chunk in enumerate(message_chunks):
            if len(message_chunks) > 1:
                part_number = f"Part {idx + 1}/{len(message_chunks)}: "
                chunk_with_part = part_number + chunk
            else:
                chunk_with_part = chunk
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

# Main Route

@main_bp.route('/', methods=['GET'])
def index():
    return "This is a WhatsApp chatbot powered by GPT-3.5-turbo. Use the /webchat endpoint to interact with the bot."

        
#Primary Route Function: /chatgpt
#This is the main function that handles incoming POST requests for the /chatgpt route. 
#It processes user messages, interacts with the OpenAI API to generate responses, 
#manages conversation context, and sends replies to the user via WhatsApp.


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


"""
End /Primary Route Function: /chatgpt * * *
"""

