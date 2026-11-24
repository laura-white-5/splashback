"""Shared test settings: tests always use the mock AI, never the real API."""
import pytest


@pytest.fixture(autouse=True)
def use_mock_ai(monkeypatch):
    monkeypatch.setenv("SPLASHBACK_AI", "mock")
    monkeypatch.setenv("SPLASHBACK_RETRY_DELAY", "0")   # no waiting between retries in tests