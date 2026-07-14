import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GITHUB_TOKEN")
client = OpenAI(base_url="https://models.inference.ai.azure.com", api_key=api_key)

models = ["Llama-3.2-11B-Vision-Instruct", "Llama-3.2-90B-Vision-Instruct", "meta-llama-3.2-90b-vision-instruct", "meta-llama-3.2-11b-vision-instruct"]

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
