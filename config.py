import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Config(BaseSettings):
    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"

    # ElevenLabs Configuration
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str = "4RZ84U1b4WCqpu57LvIq"
    ELEVENLABS_MODEL: str = "eleven_turbo_v2_5" # eleven_turbo_v2_5

    # Logging
    LOG_LEVEL: str = "INFO"

    # LangSmith / LangChain Tracing
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str  # Make sure this is in your .env
    LANGCHAIN_PROJECT: str = "BrightSmile-Voice-Agent"

    TIMEZONE: str = "America/New_York"

    class Config:
        env_file = ".env"

config = Config()