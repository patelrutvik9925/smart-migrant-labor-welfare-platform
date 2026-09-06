"""
Application configuration loaded from environment variables.
All secrets must be in the .env file — never hardcoded.
"""
from typing import List, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_parse_none_str="null",
    )

    # IBM watsonx Orchestrate
    WXO_URL: str = ""
    WXO_API_KEY: str = ""
    WXO_ENVIRONMENT: str = "draft"

    # IBM Cloud
    IBM_CLOUD_REGION: str = "jp-tok"
    IBM_CLOUD_API_KEY: str = ""

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "migrant_welfare_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_SSL_MODE: str = "require"
    DB_SSL_CERT_PATH: str = ""

    # IBM Cloud Object Storage
    COS_ENDPOINT: str = ""
    COS_API_KEY: str = ""
    COS_INSTANCE_CRN: str = ""
    COS_BUCKET_WORKER_DOCS: str = "migrant-worker-docs-draft"
    COS_BUCKET_COMPLAINT_EVIDENCE: str = "migrant-complaint-evidence-draft"
    COS_BUCKET_KNOWLEDGE: str = "migrant-knowledge-base-draft"

    # Auth / OTP
    SMS_API_KEY: str = ""
    SMS_SENDER_ID: str = "MGRWLF"
    OTP_EXPIRY_SECONDS: int = 300
    JWT_SECRET: str = "change-this-secret-in-production-min-32-chars"
    JWT_EXPIRY_HOURS: int = 24

    # Backend
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_DEBUG: bool = True
    # Stored as raw string to allow comma-separated values in .env
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    SECRET_KEY: str = "change-this-secret-in-production"

    # Notifications
    NOTIFICATION_SMS_ENABLED: bool = False
    NOTIFICATION_INAPP_ENABLED: bool = True

    # Logging
    LOG_LEVEL: str = "DEBUG"
    LOG_FILE: str = "./logs/backend.log"
    AUDIT_LOG_FILE: str = "./logs/audit.log"

    # Knowledge Base
    KNOWLEDGE_UPDATE_SCHEDULE: str = "0 2 * * *"
    KNOWLEDGE_HUMAN_REVIEW_REQUIRED: bool = True

    # App
    ENVIRONMENT: str = "draft"
    VERSION: str = "1.0.0"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list (supports comma-separated or JSON array)."""
        v = self.ALLOWED_ORIGINS.strip()
        if v.startswith("["):
            import json
            try:
                return json.loads(v)
            except Exception:
                pass
        return [o.strip() for o in v.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        ssl_suffix = "?sslmode=require" if self.DB_SSL_MODE == "require" else ""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}{ssl_suffix}"
        )


settings = Settings()
