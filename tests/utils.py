"""Testing utilities."""

import os

import pytest

# check for cmem environment and skip if not present
needs_cmem = pytest.mark.skipif(
    os.environ.get("CMEM_BASE_URI", "") == "", reason="Needs CMEM configuration"
)

needs_kaggle = pytest.mark.skipif(
    "KAGGLE_USERNAME" not in os.environ or "KAGGLE_KEY" not in os.environ,
    reason="Needs Kaggle API configuration",
)


def get_kaggle_config() -> dict[str, str]:
    """To get the kaggle configuration from environment variables"""
    return {
        "username": os.environ.get("KAGGLE_USERNAME", ""),
        "key": os.environ.get("KAGGLE_KEY", ""),
    }
