from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = "Task Manager Agent API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # LLM Configuration
    GOOGLE_GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"  # Default to Gemini (use gemini-2.5-flash, gemini-2.0-flash, or gemini-pro-latest)
    LLM_TEMPERATURE: float = 0.7
    LLM_PROVIDER: str = "gemini"  # Primary provider: gemini, openai, anthropic
    
    # Database Configuration
    SUPABASE_URL: str = ""
    SUPABASE_API_KEY: str = ""
    SUPABASE_DB_NAME: str = "task_manager"
    
    # ChromaDB Configuration
    CHROMADB_PERSIST_DIR: str = "./chroma_data"
    CHROMADB_COLLECTION_NAME: str = "task_embeddings"
    
    # External APIs
    GOOGLE_CALENDAR_API_KEY: str = ""
    NOTION_API_KEY: str = ""
    
    # Scheduler Configuration
    SCHEDULER_ENABLED: bool = True
    REMINDER_CHECK_INTERVAL_MINUTES: int = 5
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Frontend Configuration (optional, used by frontend)
    API_URL: str = "http://localhost:8000/api/v1"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()