import fitz  # PyMuPDF
import os
from typing import Dict, Any

class PDFParser:
    @staticmethod
    def extract_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extract basic metadata from a PDF file.
        For deep analysis (questions, marks), we will rely on the AI model
        processing the document directly as it has multimodal capabilities.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found.")
            
        doc = fitz.open(file_path)
        
        metadata = {
            "page_count": doc.page_count,
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "is_encrypted": doc.is_encrypted
        }
        
        doc.close()
        return metadata

pdf_parser = PDFParser()
