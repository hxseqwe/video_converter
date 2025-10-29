import os
from pathlib import Path

class Settings:
    APP_TITLE = "Video Converter"
    APP_VERSION = "1.0.0"
    
    BASE_DIR = Path(__file__).parent.parent
    UPLOAD_DIR = BASE_DIR / "static" / "uploads"
    CONVERTED_DIR = BASE_DIR / "static" / "converted"
    
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    CONVERTED_DIR.mkdir(parents=True, exist_ok=True)
    
    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

    SUPPORTED_INPUT_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    SUPPORTED_OUTPUT_FORMATS = ['mp4', 'avi', 'mov', 'webm', 'mkv']

    MAX_FILE_SIZE = 100 * 1024 * 1024

settings = Settings()