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


# class Config(BaseSettings):
#     # OpenAI Configuration
#     OPENAI_API_KEY: str
#     OPENAI_MODEL: str = "gpt-4o"
#     OPENAI_TTS_MODEL: str = "tts-1"
#     OPENAI_TTS_VOICE: str = "nova" #alloy , echo, fable, onyx, nova, or shimmer

#     LOG_LEVEL: str = "INFO"

#     class Config:
#         env_file = ".env"

class Config(BaseSettings):
    # OpenAI Configuration (Still used for LLM and Speech-to-Text)
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    
    # ElevenLabs Configuration (Used for Text-to-Speech)
    ELEVENLABS_API_KEY: str
    # You can find Voice IDs in the ElevenLabs VoiceLab. 
    # Example ID (Rachel): "21m00Tcm4TlvDq8ikWAM"
    ELEVENLABS_VOICE_ID: str = "4RZ84U1b4WCqpu57LvIq" 
    ELEVENLABS_MODEL: str = "eleven_turbo_v2_5" # Turbo is best for real-time latency

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


config = Config()
