import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    app_name: str = os.getenv("APP_NAME", "AI Tutor")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"

    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "ai_tutor")

    @property
    def database_url(self) -> str:
        return f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"

    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_api_base: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    temperature: float = float(os.getenv("TEMPERATURE", "0.7"))

    volc_access_key: str = os.getenv("VOLC_ACCESS_KEY", "")
    volc_secret_key: str = os.getenv("VOLC_SECRET_KEY", "")
    volc_region: str = os.getenv("VOLC_REGION", "cn-beijing")
    volc_endpoint: str = os.getenv("VOLC_ENDPOINT", "ark.cn-beijing.volces.com")
    volc_model: str = os.getenv("VOLC_MODEL", "")

    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./storage/chroma")
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "sequence_questions")

    kg_persist_dir: str = os.getenv("KG_PERSIST_DIR", "./storage/kg")
    kg_file_name: str = os.getenv("KG_FILE_NAME", "sequence_kg.json")

    upload_dir: str = os.getenv("UPLOAD_DIR", "./storage/uploads")
    max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))

    cors_origins: List[str] = os.getenv("CORS_ORIGINS", '["http://localhost:3000", "http://localhost:5173"]').strip("[]").replace('"', '').split(",")

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_dir: str = os.getenv("LOG_DIR", "./logs")


settings = Settings()
