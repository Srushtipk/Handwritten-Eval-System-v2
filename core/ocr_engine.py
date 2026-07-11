import os
import io
import base64
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables (API Key) from .env file
load_dotenv()
api_key = os.getenv("GITHUB_TOKEN", "").strip()

def extract_text_with_gemini(image: Image.Image) -> str:
    """
    Sends a PIL Image to GitHub Models (GPT-4o) and extracts handwritten text.
    We are using GPT-4o which is Microsoft's top tier vision model, completely free via GitHub.
    """
    if not api_key or api_key == "your_github_token_here":
        return "ERROR: Please set your GITHUB_TOKEN in the .env file!"
        
    try:
        # GitHub Models uses the standard OpenAI SDK, perfectly mapping to our old setup!
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=api_key,
        )
        
        # Convert PIL Image to Base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        prompt = (
            "You are an expert handwriting transcription engine. "
            "Read ALL the handwritten text from this image perfectly. "
            "If there are any diagrams or flowcharts, describe their structure and read the text inside each shape. "
            "Return ONLY the extracted text. Do not add any introductory or conversational filler."
        )
        
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            temperature=0,
        )
        
        return completion.choices[0].message.content.strip()
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"ERROR during OCR extraction: {str(e)}"
