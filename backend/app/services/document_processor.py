"""Document Processing Service - Extract text from PDFs and DOCX files"""
from typing import Dict, Any, Optional
from pypdf import PdfReader
from docx import Document
import io
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process PDF and DOCX documents"""

    @staticmethod
    async def extract_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)
            
            text_content = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
            
            return "\n".join(text_content)
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            raise

    @staticmethod
    async def extract_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX"""
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text_content.append(paragraph.text)
            
            # Also extract from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text:
                            row_text.append(cell.text)
                    if row_text:
                        text_content.append(" | ".join(row_text))
            
            return "\n".join(text_content)
        except Exception as e:
            logger.error(f"DOCX extraction failed: {str(e)}")
            raise

    @staticmethod
    async def extract_from_file(filename: str, file_content: bytes) -> str:
        """Extract text from file based on extension"""
        try:
            filename_lower = filename.lower()
            
            if filename_lower.endswith(".pdf"):
                return await DocumentProcessor.extract_from_pdf(file_content)
            elif filename_lower.endswith(".docx"):
                return await DocumentProcessor.extract_from_docx(file_content)
            else:
                raise ValueError(f"Unsupported file type: {filename}")
        except Exception as e:
            logger.error(f"File extraction failed for {filename}: {str(e)}")
            raise

    @staticmethod
    def summarize_text(text: str, max_chars: int = 1000) -> str:
        """Summarize extracted text to max characters"""
        if len(text) <= max_chars:
            return text
        
        # Simple truncation with ellipsis
        return text[:max_chars] + "..."


# Singleton instance
_doc_processor = None


def get_document_processor() -> DocumentProcessor:
    """Get or create document processor singleton"""
    global _doc_processor
    if _doc_processor is None:
        _doc_processor = DocumentProcessor()
    return _doc_processor
