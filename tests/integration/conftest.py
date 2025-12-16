"""
Pytest configuration and fixtures for integration tests
"""

import pytest
import asyncio
import os


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def api_url() -> str:
    """Get API URL from environment or use default"""
    return os.getenv("API_URL", "http://localhost:8080")


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test"""
    # Add any global setup here
    yield
    # Add any cleanup here


# Configure pytest-asyncio mode
def pytest_configure(config):
    config.option.asyncio_mode = "auto"
