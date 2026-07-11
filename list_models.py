import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Available models:")
for m in client.models.list():
    if "flash" in m.name:
        print(m.name)
