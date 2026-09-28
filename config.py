import os
from dotenv import load_dotenv

# Load variables from .env file if present
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-change-this-secret')
    
    # Upload configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Local SQLite database
    SQLITE_DB_PATH = os.path.join(BASE_DIR, 'placement_cell.db')
    
    # Placement Cell / TPO Admin Credentials
    TPO_USERNAME = os.getenv('TPO_USERNAME', 'tpo_admin')
    TPO_PASSWORD = os.getenv('TPO_PASSWORD', 'change-this-password')
    
    # Analysis & Grammar Settings
    ENABLE_LANGUAGE_TOOL = os.getenv('ENABLE_LANGUAGE_TOOL', 'false').lower() == 'true'
    MAX_GRAMMAR_ISSUES = 25  # Limit reported errors to prevent overwhelming the student
