from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AI_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:5173"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024 # 10MB
    # For Image generation, maybe we will use Gemini as well, or Pollinations.AI which is free/no key.
    # We will use pollinations.ai for image generation (free, no auth needed).
    
    class Config:
        env_file = ".env"

settings = Settings()
