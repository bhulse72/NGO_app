import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
CREDENTIALS_FILE = "credentials.json"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

USERS = {
    "maria": {
        "password_hash": generate_password_hash("password123"),
        "name": "Maria Garcia",
        "worker_id": "sw001",
        "is_admin": True,
        "is_social_worker": True
    },
    "james": {
        "password_hash": generate_password_hash("password123"),
        "name": "James Brown",
        "worker_id": "sw002",
        "is_admin": False,
        "is_social_worker": True
    }
}