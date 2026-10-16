"""Unit tests for enterprise in-process deterministic PII sanitizer engine.

Operationalizes ADR-0005, Invariant 1 (2-minute rule), Invariant 9 (PII scrubbing gate),
and validates protection against collateral redaction of product catalog titles.
"""

import pandas as pd

from src.agent.nodes.sanitize_pii import sanitize_pii
from src.agent.state import create_initial_state
from src.guardrails.pii import (
    TOKEN_ADDRESS,
    TOKEN_EMAIL,
    TOKEN_IP,
    TOKEN_NAME,
    sanitize_dataframe,
    sanitize_records,
    sanitize_text,
)


def test_sanitize_records_scrubs_all_four_mandatory_fields():
    """AC 1: Verify first_name, last_name, email, and ip_address are scrubbed with standard tokens."""
    records = [
        {
            "id": 101,
            "first_name": "Eleanor",
            "last_name": "Vane",
            "email": "eleanor.vane@nassau.gov",
            "ip_address": "198.51.100.42",
            "street_address": "84 Queen Anne Shore",
            "city": "London",
            "total_orders": 5,
        }
    ]

    sanitized = sanitize_records(records)
    assert len(sanitized) == 1
    row = sanitized[0]

    assert row["first_name"] == TOKEN_NAME
    assert row["last_name"] == TOKEN_NAME
    assert row["email"] == TOKEN_EMAIL
    assert row["ip_address"] == TOKEN_IP
    assert row["street_address"] == TOKEN_ADDRESS

    # Verify non-PII attributes remain unmodified
    assert row["id"] == 101
    assert row["city"] == "London"
    assert row["total_orders"] == 5


def test_sanitize_records_protects_catalog_product_names():
    """Verify bare 'name' column representing merchandise titles is NOT redacted."""
    records = [
        {
            "id": 501,
            "name": "Calvin Klein Men's Slim Fit Chino Pant",
            "brand": "Calvin Klein",
            "category": "Pants",
            "retail_price": 79.50,
        },
        {
            "id": 502,
            "name": "Tommy Hilfiger Classic Oxford Button-Down",
            "brand": "Tommy Hilfiger",
            "category": "Shirts",
            "retail_price": 64.00,
        },
    ]

    sanitized = sanitize_records(records)
    assert len(sanitized) == 2
    assert sanitized[0]["name"] == "Calvin Klein Men's Slim Fit Chino Pant"
    assert sanitized[1]["name"] == "Tommy Hilfiger Classic Oxford Button-Down"
    assert sanitized[0]["brand"] == "Calvin Klein"


def test_sanitize_records_customer_name_variations_and_nulls():
    """Verify various customer name column aliases and null handling."""
    records = [
        {
            "customer_first_name": "James",
            "customer_last_name": "Flint",
            "customer_name": "James Flint",
            "user_name": "captain_flint",
            "full_name": "Captain James Flint",
            "email": None,
            "ip_address": None,
        }
    ]

    sanitized = sanitize_records(records)
    row = sanitized[0]

    assert row["customer_first_name"] == TOKEN_NAME
    assert row["customer_last_name"] == TOKEN_NAME
    assert row["customer_name"] == TOKEN_NAME
    assert row["user_name"] == TOKEN_NAME
    assert row["full_name"] == TOKEN_NAME
    assert row["email"] is None
    assert row["ip_address"] is None


def test_sanitize_text_regex_scrubbing():
    """Verify free-form string scrubbing redacts embedded emails and IPv4/IPv6 addresses."""
    text_with_email = "Customer reported issue from john.doe@sample.org regarding order 4821."
    scrubbed_email = sanitize_text(text_with_email)
    assert f"Customer reported issue from {TOKEN_EMAIL} regarding order 4821." == scrubbed_email

    text_with_ipv4 = "User logged in from connection origin 203.0.113.195 at checkout."
    scrubbed_ipv4 = sanitize_text(text_with_ipv4)
    assert f"User logged in from connection origin {TOKEN_IP} at checkout." == scrubbed_ipv4

    text_with_ipv6 = "Audit log traced to 2001:0db8:85a3:0000:0000:8a2e:0370:7334 internal port."
    scrubbed_ipv6 = sanitize_text(text_with_ipv6)
    assert f"Audit log traced to {TOKEN_IP} internal port." == scrubbed_ipv6

    clean_text = "Net revenue surged 24.5% across Outerwear in Q4."
    assert sanitize_text(clean_text) == clean_text


def test_sanitize_dataframe_integration():
    """Verify pandas DataFrame scrubbing preserves catalog columns and masks customer identifiers."""
    data = {
        "id": [1, 2],
        "name": ["Levi's 501 Original Fit Jeans", "Nike Air Force 1"],
        "first_name": ["Alice", "Bob"],
        "last_name": ["Smith", "Jones"],
        "email": ["alice@wonderland.com", "bob@builder.com"],
        "ip_address": ["10.0.0.1", "10.0.0.2"],
        "net_sales": [120.0, 95.0],
    }
    df = pd.DataFrame(data)

    clean_df = sanitize_dataframe(df)

    # Product names intact
    assert clean_df["name"].iloc[0] == "Levi's 501 Original Fit Jeans"
    assert clean_df["name"].iloc[1] == "Nike Air Force 1"

    # Customer identifiers masked
    assert clean_df["first_name"].iloc[0] == TOKEN_NAME
    assert clean_df["last_name"].iloc[1] == TOKEN_NAME
    assert clean_df["email"].iloc[0] == TOKEN_EMAIL
    assert clean_df["ip_address"].iloc[1] == TOKEN_IP
    assert clean_df["net_sales"].iloc[0] == 120.0


def test_sanitize_pii_node():
    """Verify LangGraph sanitize_pii node reads query_results and outputs sanitized_results."""
    state = create_initial_state("Customer lookup")
    state["query_results"] = [
        {
            "user_id": 99,
            "first_name": "Thomas",
            "last_name": "Silver",
            "email": "silver@walrus.co",
            "ip_address": "172.16.254.1",
            "lifetime_value": 850.0,
        }
    ]

    update = sanitize_pii(state)
    assert "sanitized_results" in update
    sanitized = update["sanitized_results"]

    assert len(sanitized) == 1
    assert sanitized[0]["first_name"] == TOKEN_NAME
    assert sanitized[0]["last_name"] == TOKEN_NAME
    assert sanitized[0]["email"] == TOKEN_EMAIL
    assert sanitized[0]["ip_address"] == TOKEN_IP
    assert sanitized[0]["lifetime_value"] == 850.0
