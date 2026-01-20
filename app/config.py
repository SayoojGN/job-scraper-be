from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    app_name: str = "Job Scraper Service"
    app_env: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str

    # Firecrawl
    firecrawl_api_key: str

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Email (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    email_from: str

    # Scheduler
    scrape_interval_hours: int = 6
    notification_interval_minutes: int = 5

    # Rate Limiting
    scrape_rate_limit: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
