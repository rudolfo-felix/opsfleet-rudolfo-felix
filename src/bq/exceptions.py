"""Exception hierarchy for BigQuery operations."""


class BigQueryClientError(Exception):
    """Base exception for all BigQuery client errors."""

    pass


class CredentialsMissingError(BigQueryClientError):
    """Raised when Google Cloud Application Default Credentials (ADC) cannot be found.

    Allows upstream callers to fall back gracefully to the offline DuckDB mock engine.
    """

    pass


class ReadOnlyQueryViolationError(BigQueryClientError):
    """Raised when a non-read-only (mutating) SQL query is attempted."""

    pass


class SchemaInspectionError(BigQueryClientError):
    """Raised when dynamic schema inspection fails."""

    pass
