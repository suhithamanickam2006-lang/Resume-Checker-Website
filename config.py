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
    
    # MySQL Database Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'placement_cell_db')
    
    # SQLite Fallback Mode (active only if MySQL server is offline)
    ENABLE_SQLITE_FALLBACK = os.getenv('ENABLE_SQLITE_FALLBACK', 'true').lower() == 'true'
    SQLITE_DB_PATH = os.path.join(BASE_DIR, 'placement_cell.db')
    
    # Placement Cell / TPO Admin Credentials
    TPO_USERNAME = os.getenv('TPO_USERNAME', 'tpo_admin')
    TPO_PASSWORD = os.getenv('TPO_PASSWORD', 'change-this-password')
    
    # Analysis & Grammar Settings
    ENABLE_LANGUAGE_TOOL = os.getenv('ENABLE_LANGUAGE_TOOL', 'false').lower() == 'true'
    MAX_GRAMMAR_ISSUES = 25  # Limit reported errors to prevent overwhelming the student
