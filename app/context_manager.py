import json
import logging
from pathlib import Path

context_file = Path("context_data.json")

def get_context(user_id):
    try:
        if context_file.exists():
            with open(context_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                return data.get(user_id, None)
        return None
    except Exception as e:
        logging.error(f"Error in get_context: {e}")
        return None

def save_context(user_id, context, incoming_message, response_text, *args):
    try:
        data = {}
        if context_file.exists():
            with open(context_file, "r", encoding="utf-8") as file:
                data = json.load(file)

        data[user_id] = {
            "context": context,
            "last_message": incoming_message,
            "last_response": response_text,
            "args": args
        }

        with open(context_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Error in save_context: {e}")

