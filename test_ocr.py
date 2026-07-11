import os
import sys
from PIL import Image

# Import our new core modules
from core.ocr_engine import extract_text_with_gemini

# Force UTF-8 output for Windows PowerShell so printing extracted symbols doesn't crash
sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("--- Handwriting Evaluation System v2: OCR Test ---")
    
    # Let's see if the .env file has a real key
    api_key = os.getenv("GITHUB_TOKEN")
    if not api_key or api_key == "your_github_token_here":
        print("\n[!] ERROR: Please paste your GitHub Token into the .env file first!")
        sys.exit(1)
        
    print("\n1. Looking for a test image...")
    # Try to copy the test image from the old v1 repo to test it here
    old_test_img_path = r"c:\Handwritten-Eval-System\test_handwriting.png"
    
    if not os.path.exists(old_test_img_path):
        print(f"[!] Could not find test image at {old_test_img_path}")
        print("Please place any handwritten image in this folder and rename it to 'test.png'")
        sys.exit(1)
        
    print(f"   Found test image: {old_test_img_path}")
    
    try:
        img = Image.open(old_test_img_path)
        print("\n2. Sending image to GitHub Models (GPT-4o) for extraction...")
        print("   (This usually takes 1-2 seconds)\n")
        
        extracted_text = extract_text_with_gemini(img)
        
        print("="*50)
        print("--- EXTRACTED TEXT ---")
        print("="*50)
        print(extracted_text)
        print("="*50)
        
    except Exception as e:
        print(f"\n[!] Error during testing: {e}")

if __name__ == "__main__":
    main()
