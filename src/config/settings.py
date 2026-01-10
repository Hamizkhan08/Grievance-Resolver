"""
Application configuration and settings.
Loads environment variables and provides centralized configuration.
"""
import os
from typing import Optional, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase Configuration
    supabase_url: str = Field(default="", env="SUPABASE_URL")
    supabase_key: str = Field(default="", env="SUPABASE_KEY")
    supabase_service_key: Optional[str] = Field(None, env="SUPABASE_SERVICE_KEY")
    supabase_storage_bucket: str = Field(default="forum-images", env="SUPABASE_STORAGE_BUCKET")
    
    # Groq Configuration (Llama models)
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-8b-instant", env="GROQ_MODEL")  # Llama models on Groq
    
    # OpenAI Configuration (optional for GPT models)
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    
    # LLM Provider Selection
    llm_provider: str = Field(default="groq", env="LLM_PROVIDER")  # "groq" (Llama) or "openai" (GPT)
    
    # Application Configuration
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # India-specific Configuration
    default_timezone: str = Field(default="Asia/Kolkata", env="DEFAULT_TIMEZONE")
    default_country: str = Field(default="India", env="DEFAULT_COUNTRY")
    
    # SLA Configuration (in hours)
    sla_urgent: int = Field(default=24, env="SLA_URGENT")
    sla_high: int = Field(default=72, env="SLA_HIGH")
    sla_medium: int = Field(default=168, env="SLA_MEDIUM")
    sla_low: int = Field(default=336, env="SLA_LOW")
    
    # Notification Configuration
    enable_email_notifications: bool = Field(default=False, env="ENABLE_EMAIL_NOTIFICATIONS")
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: Optional[Union[int, str]] = Field(default=None, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    
    @field_validator('smtp_port', mode='before')
    @classmethod
    def parse_smtp_port(cls, v):
        """Convert empty string to None for smtp_port."""
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v
    
    # Agent Configuration
    use_llm_for_communication: bool = Field(default=False, env="USE_LLM_FOR_COMMUNICATION")
    use_llm_for_understanding: bool = Field(default=True, env="USE_LLM_FOR_UNDERSTANDING")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Validate required settings at startup
def validate_settings():
    """Validate that required settings are provided."""
    errors = []
    
    if not settings.supabase_url:
        errors.append("SUPABASE_URL is required")
    if not settings.supabase_key:
        errors.append("SUPABASE_KEY is required")
    if not settings.groq_api_key and not settings.openai_api_key:
        errors.append("Either GROQ_API_KEY (for Llama models) or OPENAI_API_KEY (for GPT models) is required")
    
    if errors:
        error_msg = "Missing required environment variables:\n" + "\n".join(f"  - {e}" for e in errors)
        error_msg += "\n\nPlease create a .env file in the dev/ directory with these variables."
        error_msg += "\nSee .env.example for reference."
        raise ValueError(error_msg)
    
    return True

