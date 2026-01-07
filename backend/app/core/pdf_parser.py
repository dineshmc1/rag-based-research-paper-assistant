import fitz  # PyMuPDF
from typing import List, Dict, Optional
import re

class PDFParser:
    """Extracts text from PDFs with page-level fidelity"""
    
    @staticmethod
    def parse_pdf(pdf_path: str) -> List[Dict]:
        """
        Parse PDF and extract text with metadata
        
        Returns:
            List of dicts with {page_number, text, section}
        """
        doc = fitz.open(pdf_path)
        pages_data = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Detect section headers (simple heuristic)
            section = PDFParser._detect_section(text, page_num)
            
            pages_data.append({
                "page_number": page_num + 1,
                "text": text,
                "section": section
            })
        
        doc.close()
        return pages_data
    
    @staticmethod
    def _detect_section(text: str, page_num: int) -> str:
        """Detect section from text (simple pattern matching)"""
        text_lower = text.lower()
        
        # Common section patterns
        if "abstract" in text_lower and page_num < 2:
            return "Abstract"
        elif any(keyword in text_lower for keyword in ["introduction", "1. introduction"]):
            return "Introduction"
        elif any(keyword in text_lower for keyword in ["method", "approach", "architecture"]):
            return "Methods"
        elif any(keyword in text_lower for keyword in ["result", "experiment", "evaluation"]):
            return "Results"
        elif any(keyword in text_lower for keyword in ["discussion", "analysis"]):
            return "Discussion"
        elif any(keyword in text_lower for keyword in ["conclusion", "summary"]):
            return "Conclusion"
        elif any(keyword in text_lower for keyword in ["reference", "bibliography"]):
            return "References"
        else:
            return "Body"
    
    @staticmethod
    def should_skip_section(section: str) -> bool:
        """Skip certain sections from embedding (like References)"""
        return section.lower() == "references"
