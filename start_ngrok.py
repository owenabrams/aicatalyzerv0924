import os
from dotenv import load_dotenv, set_key
from twilio.rest import Client

# Load environment variables from .env file
load_dotenv()

# Define your Ngrok URL directly
NGROK_URL = "https://riseai.ngrok.io"

def update_env_file(public_url):
    # Update the .env file with the new ngrok URL
    env_file_path = '.env'
    set_key(env_file_path, 'NGROK_URL', public_url)

def update_twilio_webhook(public_url):
    try:
        # Get Twilio credentials from .env file
        twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')

        # Initialize Twilio client
        client = Client(twilio_account_sid, twilio_auth_token)

        # Update the webhook URL for the Twilio WhatsApp number
        phone_numbers = client.incoming_phone_numbers.list(phone_number=twilio_whatsapp_number)
        if phone_numbers:
            phone_numbers[0].update(voice_url=f'{public_url}/chatgpt', sms_url=f'{public_url}/chatgpt')
            print(f"Updated Twilio webhook to: {public_url}/chatgpt")
        else:
            print(f"Could not find Twilio phone number: {twilio_whatsapp_number}")
    except Exception as e:
        print(f"Error updating Twilio webhook: {e}")

def main():
    # Use the static Ngrok URL
    public_url = NGROK_URL
    if public_url:
        print(f"Ngrok URL: {public_url}")
        # Update the .env file
        update_env_file(public_url)
        # Update the Twilio webhook with the new ngrok URL
        update_twilio_webhook(public_url)
    else:
        print("Failed to set ngrok URL.")

if __name__ == "__main__":
    main()
