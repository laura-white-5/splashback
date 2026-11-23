"""The ONE place that decides which AI provider the app uses.

Settings come from environment variables, usually in a .env file
(never committed to GitHub):
  GEMINI_API_KEY  - your Google AI Studio key
  SPLASHBACK_AI   - "gemini" or "mock" (default: gemini if a key is set, otherwise mock)
  GEMINI_MODEL    - optional, defaults to gemini-2.5-flash
"""
import os

from dotenv import load_dotenv

from ai_provider.mock import MockAIProvider

load_dotenv()


def get_ai_provider():
    api_key = os.getenv("GEMINI_API_KEY")
    choice = os.getenv("SPLASHBACK_AI", "gemini" if api_key else "mock")

    if choice == "gemini" and api_key:
        from ai_provider.gemini import GeminiAIProvider
        return GeminiAIProvider(api_key, model=os.getenv("GEMINI_MODEL", "GEMINI_MODEL=gemini-3.5-flash-lite"))
    return MockAIProvider()