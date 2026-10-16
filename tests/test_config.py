"""Unit tests for configuration loading and validation."""

import pytest

from src.config import ConfigurationError, load_settings


def test_valid_settings_loading():
    """Verify that valid configuration loads with expected defaults."""
    settings = load_settings(
        env_file=None,
        gemini_api_key="AIzaSy_test_valid_key",
        model_name="gemini-2.5-flash",
        gcp_project_id="bigquery-public-data",
        mock_bigquery=False,
    )
    assert settings.gemini_api_key == "AIzaSy_test_valid_key"
    assert settings.model_name == "gemini-2.5-flash"
    assert settings.gcp_project_id == "bigquery-public-data"
    assert settings.mock_bigquery is False
    assert settings.max_llm_calls_per_query == 5
    assert settings.max_sql_retries == 2
    assert settings.backoff_max_retries == 3


def test_missing_gemini_api_key_raises_friendly_error():
    """Verify that missing GEMINI_API_KEY raises ConfigurationError with evaluator guidance."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(env_file=None, gemini_api_key="")

    assert "MISSING GEMINI_API_KEY" in str(exc_info.value)
    assert "https://aistudio.google.com/" in str(exc_info.value)


def test_placeholder_gemini_api_key_raises_friendly_error():
    """Verify that placeholder key raises ConfigurationError."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(env_file=None, gemini_api_key="your_gemini_api_key_here")

    assert "MISSING GEMINI_API_KEY" in str(exc_info.value)


def test_configurable_model_family():
    """Verify swappable Flash family models per Vlad's directive."""
    valid_variants = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-3.1-flash",
        "gemini-3.1-flash-lite",
    ]
    for variant in valid_variants:
        settings = load_settings(
            env_file=None,
            gemini_api_key="AIzaSy_test_key",
            model_name=variant,
        )
        assert settings.model_name == variant


def test_retired_model_rejected():
    """Verify that deprecated gemini-1.5 models are rejected with actionable advice."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(
            env_file=None,
            gemini_api_key="AIzaSy_test_key",
            model_name="gemini-1.5-flash",
        )
    assert "deprecated/retired" in str(exc_info.value)


def test_pro_model_rejected():
    """Verify that non-free-tier pro models are rejected per instructions."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(
            env_file=None,
            gemini_api_key="AIzaSy_test_key",
            model_name="gemini-2.5-pro",
        )
    assert "not supported on the free tier" in str(exc_info.value)


def test_finops_budget_bounds():
    """Verify boundary limits on call budgets and SQL retries."""
    with pytest.raises(ConfigurationError):
        load_settings(
            env_file=None,
            gemini_api_key="AIzaSy_test_key",
            max_llm_calls_per_query=0,  # ge=1
        )

    with pytest.raises(ConfigurationError):
        load_settings(
            env_file=None,
            gemini_api_key="AIzaSy_test_key",
            max_sql_retries=10,  # le=5
        )
