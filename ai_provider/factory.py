# The one place that picks which AI the app uses
"""The ONE place that decides which AI provider the app uses.

To switch from the mock to a real LLM, change only this function.
"""
from ai_provider.mock import MockAIProvider


def get_ai_provider():
    return MockAIProvider()