import os
import glob
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.pdf_handler import convert_pdf_to_images

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "raw_pdfs")
    output_dir = os.path.join(base_dir, "extracted_pages")
    
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    pdfs = glob.glob(os.path.join(input_dir, "*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {input_dir}.")
        print("Please place your 12 PDFs in 'data/raw_pdfs/' and run again.")
        return
        
    print(f"Found {len(pdfs)} PDFs. Extracting pages...")
    for pdf_path in pdfs:
        filename = os.path.basename(pdf_path).replace(".pdf", "")
        print(f"Processing {filename}...")
        try:
            images = convert_pdf_to_images(pdf_path)
            for i, img in enumerate(images):
                # Ensure 3 digits for proper sorting (e.g., page_001.png)
                out_path = os.path.join(output_dir, f"{filename}_page_{i+1:03d}.png")
                img.save(out_path, "PNG")
            print(f"  -> Extracted {len(images)} pages.")
        except Exception as e:
            print(f"  -> Error: {str(e)}")
            
    print(f"Done! All images saved to {output_dir}")

if __name__ == "__main__":
    main()
