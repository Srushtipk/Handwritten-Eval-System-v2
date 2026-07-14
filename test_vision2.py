import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GITHUB_TOKEN")
client = OpenAI(base_url="https://models.inference.ai.azure.com", api_key=api_key)

models = ["Phi-3.5-vision-instruct", "phi-3-vision-128k-instruct"]

for m in models:
    try:
        print(f"Testing {m}...")
        resp = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        print(f"SUCCESS with {m}")
    except Exception as e:
        print(f"FAILED {m}: {e}")
