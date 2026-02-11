"""
Configuration Module
Mengelola konfigurasi aplikasi menggunakan Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Kelas konfigurasi aplikasi
    Menggunakan Pydantic untuk validasi dan type checking
    """
    # Application Info
    APP_NAME: str = "OCR Microservice - DISKOMINFOTIK Bengkulu"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Security
    API_KEY: str = "your_secure_api_key_here"
    
    # OCR Configuration
    OCR_LANGUAGES: List[str] = ["en"]
    OCR_GPU: bool = False
    OCR_CONFIDENCE_THRESHOLD: float = 0.5
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10485760  # 10MB in bytes
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png"]
    
    # PUSAKO Website Configuration
    PUSAKO_BASE_URL: str = "https://pusako.bengkuluprov.go.id"
    PUSAKO_TIMEOUT: int = 30
    PUSAKO_MAX_RETRIES: int = 3
    PUSAKO_RATE_LIMIT_DELAY: int = 2
    
    # Paths
    ASSETS_DIR: Path = BASE_DIR / "assets"
    
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Singleton instance
settings = Settings()

# Ensure directories exist
settings.ASSETS_DIR.mkdir(exist_ok=True)
