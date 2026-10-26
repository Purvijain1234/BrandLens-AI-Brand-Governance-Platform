import io
from typing import Dict, Any, List, Tuple
from PIL import Image

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"

def parse_docx_bytes(file_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts text and tables from DOCX files.
    """
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

    # Extract tables
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join([cell.text.strip() for cell in row.cells if cell.text.strip()])
            if row_text:
                paragraphs.append(row_text)

    full_text = "\n\n".join(paragraphs)
    return {
        "text": full_text,
        "paragraphs_count": len(paragraphs),
        "file_type": "docx",
    }

def parse_pdf_bytes(file_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts text from PDF files using pdfplumber.
    """
    import pdfplumber
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        pages_text = []
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                pages_text.append(text)

        full_text = "\n\n".join(pages_text)
        return {
            "text": full_text,
            "page_count": len(pdf.pages),
            "file_type": "pdf",
        }

def parse_image_bytes(file_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts OCR text, dominant colors, and image attributes using Pillow and pytesseract.
    """
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    width, height = image.size

    # OCR text extraction
    ocr_text = ""
    try:
        import pytesseract
        ocr_text = pytesseract.image_to_string(image).strip()
    except Exception as e:
        # Graceful fallback if tesseract OCR executable is not installed on host machine
        ocr_text = ""

    # Dominant color analysis (Quantize image to 8 colors)
    quantized = image.resize((150, 150)).quantize(colors=4)
    palette = quantized.getpalette()[:12]  # top 4 RGB triplets
    hex_colors = []
    for i in range(0, len(palette), 3):
        r, g, b = palette[i], palette[i+1], palette[i+2]
        hex_colors.append(rgb_to_hex(r, g, b))

    fg_color = hex_colors[0] if len(hex_colors) > 0 else "#1b2a49"
    bg_color = hex_colors[1] if len(hex_colors) > 1 else "#ffffff"

    return {
        "text": ocr_text,
        "width": width,
        "height": height,
        "dominant_colors": hex_colors,
        "fg_color": fg_color,
        "bg_color": bg_color,
        "has_image": True,
        "file_type": "image",
    }
