"""
PDF Extraction Service
Provides high-quality text extraction from PDFs for knowledge graph construction.
Uses PyPDF2 and pdfplumber for reliable PDF text extraction.
"""

import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    PDF extraction service using PyPDF2 and pdfplumber.
    Provides reliable text extraction from PDFs without external API dependencies.
    """
    
    def __init__(self):
        """Initialize PDF extractor."""
        pass
    
    async def extract_text(self, pdf_bytes: bytes, filename: Optional[str] = None) -> str:
        """
        Extract text from PDF using PyPDF2/pdfplumber.
        
        Args:
            pdf_bytes: PDF file content as bytes
            filename: Optional filename for logging
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If PDF extraction fails
        """
        # Use PyPDF2/pdfplumber for extraction
        return await self._extract_with_pypdf2(pdf_bytes, filename)
    
    async def _extract_with_pypdf2(
        self, pdf_bytes: bytes, filename: Optional[str] = None
    ) -> str:
        """
        Extract text using PyPDF2/pdfplumber (fallback method).
        
        Args:
            pdf_bytes: PDF file content as bytes
            filename: Optional filename for logging
            
        Returns:
            Extracted text content
        """
        pdf_file = io.BytesIO(pdf_bytes)
        text_parts = []
        
        # Try PyPDF2 first
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as page_error:
                    logger.warning(f"Error extracting text from PDF page {page_num}: {str(page_error)}")
                    continue
            
            if text_parts:
                return "\n\n".join(text_parts)
        except ImportError:
            logger.warning("PyPDF2 not available")
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
        
        # Fallback to pdfplumber
        try:
            import pdfplumber
            pdf_file.seek(0)  # Reset to beginning
            
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            if text_parts:
                return "\n\n".join(text_parts)
        except ImportError:
            logger.warning("pdfplumber not available")
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
        
        # If all methods fail
        if not text_parts:
            raise ValueError(
                f"Could not extract text from PDF '{filename or 'unknown'}'. "
                "The PDF may be image-based, corrupted, or require OCR."
            )
        
        return "\n\n".join(text_parts)


# Global instance
_pdf_extractor: Optional[PDFExtractor] = None


def get_pdf_extractor() -> PDFExtractor:
    """
    Get global PDF extractor instance.
    
    Returns:
        PDFExtractor instance
    """
    global _pdf_extractor
    if _pdf_extractor is None:
        _pdf_extractor = PDFExtractor()
    return _pdf_extractor

