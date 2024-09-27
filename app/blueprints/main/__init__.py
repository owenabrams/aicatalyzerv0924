import openai
from twilio.rest import Client
import os
import spacy
import nltk

from . import openai, twilio_client, nlp  # Import the initialized services


from flask import Blueprint

main_bp = Blueprint('main_bp', __name__)

from . import views  # Import the views to register routes


# Load environment variables and set up services
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY must be set")

twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
if not twilio_account_sid or not twilio_auth_token:
    raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set")
twilio_client = Client(twilio_account_sid, twilio_auth_token)

# Initialize SpaCy model
nlp = spacy.load("en_core_web_sm")

# Ensure the required NLTK data is downloaded
nltk.download('stopwords')
nltk.download('wordnet')
