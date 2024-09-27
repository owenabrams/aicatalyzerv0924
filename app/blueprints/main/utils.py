from functools import wraps
from flask import session, jsonify
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import os

user_requests = defaultdict(list)
RATE_LIMIT = 5
TIME_PERIOD = 60

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



