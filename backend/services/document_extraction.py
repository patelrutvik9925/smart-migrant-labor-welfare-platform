"""
Document information extraction service.
Extracts structured data from uploaded documents (PDFs, images).
AI analysis is always stored separately — never overwrites originals.
"""
import structlog
from typing import Optional

log = structlog.get_logger()


async def extract_document_info(
    file_bytes: bytes,
    content_type: str,
    document_type: str,
) -> Optional[dict]:
    """
    Extract structured information from a document.
    Returns a dict of extracted fields, or None if extraction fails.
    """
    try:
        if "pdf" in content_type:
            return await _extract_from_pdf(file_bytes, document_type)
        elif content_type.startswith("image/"):
            return await _extract_from_image(file_bytes, document_type)
        else:
            log.info("Document extraction skipped — unsupported type", content_type=content_type)
            return None
    except Exception as e:
        log.error("Document extraction failed", document_type=document_type, error=str(e))
        return None


async def _extract_from_pdf(file_bytes: bytes, document_type: str) -> Optional[dict]:
    """Extract text from PDF using PyPDF2."""
    try:
        import io
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return {"raw_text": text[:5000], "document_type": document_type, "extraction_method": "pdf"}
    except Exception as e:
        log.warning("PDF extraction error", error=str(e))
        return None


async def _extract_from_image(file_bytes: bytes, document_type: str) -> Optional[dict]:
    """Extract text from image using pytesseract (OCR)."""
    try:
        import io
        from PIL import Image
        import pytesseract
        img = Image.open(io.BytesIO(file_bytes))
        # Support English, Hindi, Gujarati OCR
        text = pytesseract.image_to_string(img, lang="eng+hin+guj")
        return {"raw_text": text[:5000], "document_type": document_type, "extraction_method": "ocr"}
    except Exception as e:
        log.warning("OCR extraction error", error=str(e))
        return None
