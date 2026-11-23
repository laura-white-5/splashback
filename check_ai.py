"""Quick check: which Gemini models can my key use, and does one request work?"""
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Models your key can use for text:")
for model in client.models.list():
    if "generateContent" in (model.supported_actions or []):
        print("   ", model.name.replace("models/", ""))

chosen = os.getenv("GEMINI_MODEL")
print(f"\nYour .env says GEMINI_MODEL = {chosen}")
try:
    reply = client.models.generate_content(model=chosen, contents="Say hello in five words.")
    print("SUCCESS:", reply.text)
except Exception as error:
    print("FAILED:", error)

