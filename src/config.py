"""Application configuration module using Pydantic Settings.

Adheres to 12-factor application principles and Invariant 2 (Model Configurability)
and Invariant 1 (2-Minute Evaluator Rule with friendly handled validation errors).
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigurationError(Exception):
    """Raised when application configuration is missing or invalid."""

    pass


class Settings(BaseSettings):
    """Application settings with strict validation and friendly error handling."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # 1. Google Gemini AI Studio Configuration
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key obtained from https://aistudio.google.com/",
    )
    model_name: str = Field(
        default="gemini-2.5-flash",
        description="Gemini Flash model family member (default: gemini-2.5-flash)",
    )

    # 2. Google Cloud BigQuery & Offline Mock Strategy
    gcp_project_id: str = Field(
        default="bigquery-public-data",
        description="Google Cloud project ID containing the target dataset",
    )
    mock_bigquery: bool = Field(
        default=False,
        description="Force in-memory DuckDB engine fallback instead of live BigQuery",
    )

    # 3. FinOps & Operational Call Budgets (Vlad Bondarenko Directive: 2-5 calls)
    max_llm_calls_per_query: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Max LLM invocations allowed per user query",
    )
    max_sql_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Circuit breaker cap for SQL self-correction retries",
    )
    backoff_max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max retry attempts on HTTP 429 rate limit exceptions",
    )
    backoff_initial_delay: float = Field(
        default=1.0,
        gt=0.0,
        description="Initial delay in seconds for exponential backoff",
    )
    backoff_factor: float = Field(
        default=2.0,
        ge=1.0,
        description="Multiplicative factor for exponential backoff",
    )
    backoff_jitter: bool = Field(
        default=True,
        description="Add random jitter to backoff delay to prevent herd effects",
    )

    # 4. Storage & Observability
    storage_db_path: str = Field(
        default="reports.db",
        description="SQLite database path for persisting saved reports",
    )
    log_level: str = Field(
        default="INFO",
        description="Standard logging verbosity (DEBUG, INFO, WARNING, ERROR)",
    )
    otel_enabled: bool = Field(
        default=False,
        description="Enable OpenTelemetry tracing exporter",
    )

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate model against Vlad Bondarenko's directives."""
        clean_v = v.strip().lower()
        if "1.5" in clean_v:
            raise ValueError(
                f"Model '{v}' is deprecated/retired per Tech Lead instructions. "
                "Please configure MODEL_NAME=gemini-2.5-flash or gemini-2.5-flash-lite."
            )
        if "pro" in clean_v:
            raise ValueError(
                f"Model '{v}' is not supported on the free tier. "
                "Per Tech Lead instructions, please use a Flash model: "
                "gemini-2.5-flash, gemini-2.5-flash-lite, or gemini-3.1-flash."
            )
        return clean_v


def load_settings(env_file: str | None = ".env", **overrides) -> Settings:
    """Load and validate settings with friendly error handling for the evaluator.

    Raises:
        ConfigurationError: If GEMINI_API_KEY is missing or unpopulated,
                            providing a clean formatted error message.
    """
    try:
        if env_file:
            settings = Settings(_env_file=env_file, **overrides)
        else:
            settings = Settings(_env_file=None, **overrides)
    except Exception as e:
        raise ConfigurationError(f"Configuration validation error: {e}") from e

    # Check for missing or placeholder GEMINI_API_KEY
    key = settings.gemini_api_key.strip()
    if not key or key == "your_gemini_api_key_here":
        msg = (
            "\n"
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ ⚠️  MISSING GEMINI_API_KEY                                              │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ The retail assistant requires a Google Gemini API key to operate.     │\n"
            "│                                                                        │\n"
            "│ 1. Get a free API key at: https://aistudio.google.com/                 │\n"
            "│ 2. Create a .env file from .env.example:                              │\n"
            "│      cp .env.example .env                                              │\n"
            "│ 3. Add your key:                                                       │\n"
            "│      GEMINI_API_KEY=AIzaSy...                                          │\n"
            "│                                                                        │\n"
            "│ Or export it directly in your shell:                                   │\n"
            "│      export GEMINI_API_KEY=AIzaSy...                                   │\n"
            "└────────────────────────────────────────────────────────────────────────┘\n"
        )
        raise ConfigurationError(msg)

    return settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached global accessor for settings."""
    return load_settings()
