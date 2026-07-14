import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

test_models = [
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.0-flash",
    "gemini-flash-latest",
]

for m in test_models:
    try:
        print(f"Testing {m}...")
        resp = client.models.generate_content(
            model=m,
            contents=["Hello"]
        )
        print(f"SUCCESS with {m}")
    except Exception as e:
        print(f"FAILED {m}: {e}")
