"""
Configuración global de la aplicación.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "CallQA Server"
    DEBUG: bool = False
    SECRET_KEY: str = "secret-key-placeholder"
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://callqa:password@localhost:5432/callqa_db"
    
    # Storage
    UPLOAD_DIRECTORY: Path = Path("/data/callqa/uploads")
    CLIPS_OUTPUT_DIRECTORY: Path = Path("/data/callqa/clips")
    TEMP_DIRECTORY: Path = Path("/tmp/callqa")
    
    # CDR Integration
    CDR_API_URL: str = "http://cisco-uccx:8080/api/v1"
    CDR_API_TOKEN: str = ""
    CDR_SYNC_DAYS_BACK: int = 7
    
    # Processing
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    AUDIO_SAMPLE_RATE: int = 16000
    SILENCE_THRESHOLD_DB: int = -40
    MIN_CALL_DURATION: int = 3
    SILENCE_DURATION: int = 2
    
    # Worker
    WORKER_CHECK_INTERVAL: int = 30
    MAX_CONCURRENT_TASKS: int = 3
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
