"""
conftest.py — pytest configuration for NutriKen test suite.

Registers custom markers and suppresses expected deprecation warnings
from httpx/starlette so the output stays clean in CI.
"""

import warnings
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: mark test as requiring real network access (deselect with -m 'not integration')",
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --integration flag is passed."""
    if not config.getoption("--integration", default=False):
        skip_integration = pytest.mark.skip(reason="pass --integration to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests that require real network access",
    )
