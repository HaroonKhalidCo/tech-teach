from pydantic_settings import BaseSettings
from typing import ClassVar
import os


class Settings(BaseSettings):
    APP_NAME: str = "Tech-Teach"
    API_V1_STR: str = "/api/v1"
    
    GOOGLE_API_KEY: str
    
    # Gemini Model Configuration
    TEXT_MODEL: str = "gemini-2.0-flash-exp"
    IMAGE_MODEL: str = "gemini-2.5-flash-image"
    AUDIO_MODEL: str = "gemini-2.5-flash-preview-tts"
    
    # Directory configuration
    BASE_DIR: ClassVar[str] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    OUTPUT_DIR: str = os.path.join(BASE_DIR, "data", "outputs")
    TEMP_DIR: str = os.path.join(BASE_DIR, "data", "temp")
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.TEMP_DIR, exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
settings.ensure_directories()
