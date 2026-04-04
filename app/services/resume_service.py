"""
Service module for resume PDF handling.

This module contains pure business logic for extracting text from PDF files.
It has NO dependency on HTTP or FastAPI — just takes input, returns output.
"""

import pdfplumber
from io import BytesIO


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract all text from a PDF file.

    Args:
        file_content: Raw bytes of the PDF file.

    Returns:
        str: Extracted text from all pages of the PDF.

    Raises:
        ValueError: If PDF is empty or cannot be read.
    """
    try:
        pdf_file = BytesIO(file_content)
        extracted_text = ""

        with pdfplumber.open(pdf_file) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError("PDF file is empty (no pages found).")

            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    extracted_text += f"\n--- Page {page_num} ---\n{text}"

        return extracted_text.strip()

    except pdfplumber.exceptions.PDFException as e:
        raise ValueError(f"Error reading PDF: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error while extracting text: {str(e)}")
