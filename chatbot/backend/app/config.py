import base64
import json
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_timeout_s: float = 30.0
    
    # Google Service Account (JSON string)
    google_service_account_json: str = ""
    # Alternative: base64 encoded JSON (recommended for env vars)
    google_service_account_json_b64: str = ""
    # Alternative: path to a JSON file (recommended for Cloud Run secret mounts)
    google_service_account_json_path: str = ""
    google_sheet_id: str = ""
    
    # Email notifications
    notification_email: str = "sales@ebottles.com"
    notification_from_email: str = "noreply@ebottles.com"
    # Comma-separated list of admin emails to notify (optional)
    admin_notification_emails: str = ""
    
    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # App settings
    debug: bool = False

    # Optional shared secret for backend endpoints (leave empty to disable)
    api_key: str = ""
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def admin_notification_emails_list(self) -> list[str]:
        """Parse comma-separated admin notification emails into a list."""
        return [e.strip() for e in self.admin_notification_emails.split(",") if e.strip()]
    
    @property
    def google_credentials_dict(self) -> Optional[dict]:
        """Load Google service account credentials.

        Supports:
        - GOOGLE_SERVICE_ACCOUNT_JSON (raw JSON string)
        - GOOGLE_SERVICE_ACCOUNT_JSON_B64 (base64-encoded JSON; recommended)
        - GOOGLE_SERVICE_ACCOUNT_JSON_PATH (file path; recommended for secret mounts)
        """
        raw = self.google_service_account_json.strip()
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return None

        b64 = self.google_service_account_json_b64.strip()
        if b64:
            try:
                decoded = base64.b64decode(b64).decode("utf-8")
                return json.loads(decoded)
            except Exception:
                return None

        path = self.google_service_account_json_path.strip()
        if path:
            try:
                content = Path(path).read_text(encoding="utf-8")
                return json.loads(content)
            except Exception:
                return None

        return None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

