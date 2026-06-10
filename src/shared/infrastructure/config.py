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
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
