import fitz  # PyMuPDF
from PIL import Image
import io

def convert_pdf_to_images(pdf_path_or_bytes):
    """
    Converts a PDF file into a list of PIL Image objects.
    Accepts either a file path (string) or raw bytes.
    """
    images = []
    
    if isinstance(pdf_path_or_bytes, str):
        doc = fitz.open(pdf_path_or_bytes)
    else:
        doc = fitz.open(stream=pdf_path_or_bytes, filetype="pdf")
        
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # 200 DPI is a good balance between clarity for OCR and file size
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
        
        # Convert PyMuPDF pixmap to PIL Image
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        images.append(img)
        
    return images
