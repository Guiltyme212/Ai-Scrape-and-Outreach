from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Outscraper
    outscraper_api_key: str = ""

    # ScreenshotOne
    screenshotone_access_key: str = ""
    screenshotone_secret_key: str = ""

    # Anthropic Claude
    anthropic_api_key: str = ""

    # Lovable
    lovable_api_key: str = ""

    # Instantly.ai
    instantly_api_key: str = ""
    instantly_sending_email: str = ""

    # App config
    app_name: str = "LeadPilot"
    app_base_url: str = "http://localhost:8000"
    preview_domain: str = "jouwdomein.nl"
    default_niche: str = "plumber"
    default_location: str = "Amsterdam, Netherlands"
    batch_size: int = 50
    min_score_threshold: int = 50

    # Database
    database_url: str = "sqlite:///./leadpilot.db"

    # Mock mode — use mock services instead of real APIs
    mock_mode: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def api_status(self) -> dict[str, bool]:
        """Check which API keys are configured."""
        return {
            "outscraper": bool(self.outscraper_api_key),
            "screenshotone": bool(self.screenshotone_access_key),
            "anthropic": bool(self.anthropic_api_key),
            "lovable": bool(self.lovable_api_key),
            "instantly": bool(self.instantly_api_key),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
