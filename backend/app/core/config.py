"""
config settings
"""

# from pydantic import BaseSettings
from ctypes import DEFAULT_MODE
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import find_dotenv



class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_dotenv(),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        validate_default=False,
    )

    APP_NAME: str = "Data Research Agent"
    DEBUG: bool = True
    DATABASE_URL: str | None = None
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEV: bool = True

    DEEPSEEK_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str | None = None
    OLLAMA_BASE_URL: str | None = None
    OLLAMA_MODEL: str | None = None

    DEFAULT_MODEL: str = "gpt-4o-mini"

    EMBEDDING_MODEL: str = "bge-m3"
    CHROMA_PATH: str = "resource/chroma_db"

    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    def is_dev(self):
        return self.DEV



settings = Settings()