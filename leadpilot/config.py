"""Configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Google Sheets
    google_credentials_path: str = "credentials/service_account.json"
    google_sheet_id: str = ""
    sheet_name: str = "Sheet1"

    # Anthropic
    anthropic_api_key: str = ""

    # Netlify
    netlify_api_token: str = ""

    # Pipeline
    score_threshold: int = 60
    claude_model: str = "claude-sonnet-4-5-20250929"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
