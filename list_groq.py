import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("Available models:")
for m in client.models.list().data:
    print(m.id)
