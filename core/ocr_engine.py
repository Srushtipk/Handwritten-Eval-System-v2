import os
import io
import time
import traceback
import concurrent.futures
import fitz  # PyMuPDF
from PIL import Image
from dotenv import load_dotenv

# We use google-genai SDK for the new Google Gemini API key
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY", "").strip()

def extract_text_with_gemini(images: list) -> str:
    """
    Sends a list of PIL Images to Google Gemini and extracts handwritten text.
    Includes robust retries and model fallbacks for 503 Overloaded errors.
    """
    if not api_key:
        return "ERROR: Please set your GEMINI_API_KEY in the .env file!"
        
    try:
        # Initialize Google GenAI client
        client = genai.Client(api_key=api_key)
        
        prompt = (
            "I am providing you with multiple images representing pages of a scanned exam. "
            "Please transcribe all the handwritten text perfectly. "
            "Before transcribing each page, you MUST output '--- Page X ---' where X is the sequential page number (starting from 1). "
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
                        contents=[prompt] + images,
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
        
        images = []
        for i in range(len(doc)):
            print(f"Extracting image for page {i+1}...")
            # Render page to an image. Use 1.0 zoom to prevent massive payloads that slow down Gemini.
            pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.0, 1.0))
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            # Resize image for extremely fast Gemini API upload (max width 1024)
            if img.width > 1024:
                ratio = 1024 / img.width
                img = img.resize((1024, int(img.height * ratio)), Image.Resampling.LANCZOS)
            images.append(img)
            
        print(f"Sending {len(images)} pages to Gemini in a single multi-modal request...")
        full_text = extract_text_with_gemini(images)
        return full_text
    except Exception as e:
        traceback.print_exc()
        return f"ERROR processing PDF: {str(e)}"

def segment_answers_with_gemini(raw_text: str, questions_list: list) -> dict:
    """
    Takes the massive block of OCR text from multiple pages and uses Gemini to
    segment it into discrete answers mapped to specific question IDs.
    Uses the actual question text to contextually match answers in case the student
    mislabels their question numbers (e.g. writes '2a' instead of '2').
    """
    if not api_key:
        return {}
        
    try:
        client = genai.Client(api_key=api_key)
        
        question_ids = [q.get('id', str(i+1)) for i, q in enumerate(questions_list)]
        id_list_str = ", ".join([f'"{qid}"' for qid in question_ids])
        
        q_context = ""
        for i, q in enumerate(questions_list):
            q_id = q.get('id', str(i+1))
            q_text = q.get('question', '')
            q_context += f"- ID: '{q_id}' | Topic: {q_text}\n"
        
        prompt = (
            f"You are given the raw OCR text of a student's answer sheet. "
            f"There are exactly {len(question_ids)} questions in this exam.\n\n"
            f"Here are the exact Question IDs and their topics:\n{q_context}\n"
            f"Your task is to segment the OCR text by matching the student's answer to the correct question.\n"
            f"CRITICAL: Students often mislabel question numbers (e.g. writing '2a' instead of '2', or messing up the order). "
            f"You MUST read the actual content of their answer and use context clues to map it to the correct ID from the list above. "
            f"If the student did not attempt a specific question, leave its value completely empty.\n\n"
            f"You MUST return a strict JSON object mapping EXACTLY these keys: {id_list_str} to the student's text.\n"
            f"Example format:\n"
            f"{{\n"
            f'  "{question_ids[0] if len(question_ids)>0 else "1a"}": "student text...",\n'
            f'  "{question_ids[1] if len(question_ids)>1 else "1b"}": "",\n'
            f"}}\n\n"
            f"Do not return markdown, do not wrap in ```json, just return the raw JSON object.\n\n"
            f"--- RAW OCR TEXT ---\n{raw_text}"
        )
        
        models_to_try = ['gemini-3.5-flash', 'gemini-flash-latest', 'gemini-3.1-flash-lite']
        last_e = None
        text = ""
        
        for model_name in models_to_try:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[prompt],
                        config=types.GenerateContentConfig(temperature=0.0)
                    )
                    text = response.text.strip()
                    break
                except Exception as e:
                    last_e = e
                    if "503" in str(e) or "429" in str(e):
                        import time
                        time.sleep(2)
                        continue
                    break
            if text:
                break
                
        if not text:
            raise last_e
        
        import json
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        parsed = json.loads(text.strip())
        if isinstance(parsed, str):
            parsed = json.loads(parsed)
            
        if not isinstance(parsed, dict):
            raise ValueError("LLM returned non-dictionary JSON")
            
        return parsed
        
    except Exception as e:
        print(f"Error during Gemini Segmentation: {e}")
        fallback_key = questions_list[0].get('id', 'Q1') if questions_list else "Q1"
        return {fallback_key: raw_text}
