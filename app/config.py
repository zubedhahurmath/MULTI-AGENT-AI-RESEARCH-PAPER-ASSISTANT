from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application Configuration using Pydantic Settings."""

    # Project Information
    APP_NAME: str = "Multi-Agent AI Research Paper Assistant"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Google Gemini API Settings (Read from .env or environment)
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash", description="Gemini Model Identifier")

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    PRESENTATION_DIR: Path = BASE_DIR / "data" / "presentations"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'research_assistant.db'}"

    # Upload Constraints & Security
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: list[str] = [".pdf"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def ensure_directories(self) -> None:
        """Ensure all required runtime data directories exist."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.PRESENTATION_DIR.mkdir(parents=True, exist_ok=True)
        (self.BASE_DIR / "data").mkdir(parents=True, exist_ok=True)


# Global settings singleton
settings = Settings()
settings.ensure_directories()
