import os
import io
import time
import traceback
import fitz  # PyMuPDF
from PIL import Image
from dotenv import load_dotenv

# We use google-genai SDK for the new Google Gemini API key
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY", "").strip()

def extract_text_with_gemini(image: Image.Image) -> str:
    """
    Sends a PIL Image to Google Gemini and extracts handwritten text.
    Includes robust retries and model fallbacks for 503 Overloaded errors.
    """
    if not api_key:
        return "ERROR: Please set your GEMINI_API_KEY in the .env file!"
        
    try:
        # Initialize Google GenAI client
        client = genai.Client(api_key=api_key)
        
        # Compress image before sending to OCR to save bandwidth and speed up API
        image.thumbnail((1200, 1600), Image.Resampling.LANCZOS)
        
        buffered = io.BytesIO()
        image.convert("RGB").save(buffered, format="JPEG", quality=85)
        
        prompt = (
            "You are an expert handwriting transcription engine. "
            "Read ALL the handwritten text from this image perfectly. "
            "If there are any diagrams or flowcharts, describe their structure and read the text inside each shape. "
            "Return ONLY the extracted text. Do not add any introductory or conversational filler."
        )
        
        # Fallback cascade: Try the bleeding edge model first, then stable, then lite.
        models_to_try = ['gemini-3.5-flash', 'gemini-flash-latest', 'gemini-3.1-flash-lite']
        last_e = None
        
        for model_name in models_to_try:
            # Try each model up to 3 times if it throws 503 (Overloaded)
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[prompt, image],
                        config=types.GenerateContentConfig(
                            temperature=0.0
                        )
                    )
                    return response.text.strip()
                except Exception as e:
                    err_str = str(e)
                    last_e = e
                    # 503 means the server is experiencing high demand (very common when sending parallel requests to free tier)
                    if "503" in err_str or "429" in err_str:
                        time.sleep(2) # Sleep for 2 seconds to let the server breathe before retrying
                        continue
                    else:
                        # If it's a 404 or some other fatal error, don't retry, just move to the next model
                        break
                        
        # If we exhausted all models and all retries, return the final error
        return f"ERROR during OCR extraction: {str(last_e)}"
        
    except Exception as e:
        traceback.print_exc()
        return f"ERROR during OCR extraction: {str(e)}"

def process_pdf(pdf_path: str) -> str:
    """
    Converts a PDF into images and extracts text from all pages using Gemini.
    Uses PyMuPDF (fitz) so Poppler is not required on Windows.
    """
    try:
        print(f"Converting PDF to images using PyMuPDF: {pdf_path}")
        doc = fitz.open(pdf_path)
        
        full_text = ""
        for i, page in enumerate(doc):
            print(f"Extracting text from page {i+1}...")
            # Render page to an image (pixmap)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for better OCR
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            text = extract_text_with_gemini(img)
            full_text += f"\n--- Page {i+1} ---\n{text}\n"
            
        return full_text
    except Exception as e:
        traceback.print_exc()
        return f"ERROR processing PDF: {str(e)}"
