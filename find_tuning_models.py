import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

for m in client.models.list():
    if "tuning" in m.name or "flash" in m.name:
        # Check if it supports tuning via some attribute if possible, else just print names
        print(m.name)
