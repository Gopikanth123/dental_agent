import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

# class Config(BaseSettings):
#     # Groq for Intelligence (Llama 3)
#     GROQ_API_KEY: str
#     GROQ_MODEL: str = "llama-3.3-70b-versatile"

#     LOG_LEVEL: str = "INFO"

#     class Config:
#         env_file = ".env"


class Config(BaseSettings):
    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TTS_MODEL: str = "tts-1"
    OPENAI_TTS_VOICE: str = "shimmer" # alloy, echo, fable, onyx, nova, or shimmer

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

config = Config()
