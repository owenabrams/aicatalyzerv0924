# app/blueprints/main/services.py
import os
import openai
import spacy
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY must be set")

# Initialize Twilio
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
if not twilio_account_sid or not twilio_auth_token:
    raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set")

twilio_client = Client(twilio_account_sid, twilio_auth_token)

# Load the SpaCy model
nlp = spacy.load("en_core_web_sm")
