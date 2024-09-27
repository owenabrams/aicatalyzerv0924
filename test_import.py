# test_import.py
try:
    from flask_sqlalchemy import SQLAlchemy
    print("Flask-SQLAlchemy imported successfully.")
except ImportError as e:
    print(f"ImportError: {e}")
