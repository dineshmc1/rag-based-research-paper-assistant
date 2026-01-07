from typing import List, Dict
import uuid
import re

class SemanticChunker:
    """Sentence-aware chunking with sliding window"""
    
    def __init__(self, chunk_size: int = 400, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str, page_number: int, section: str, paper_id: str) -> List[Dict]:
        """
        Create semantic chunks from text
        
        Returns:
            List of chunks with metadata
        """
        # Split into sentences
        sentences = self._split_sentences(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            # If adding this sentence exceeds chunk size
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append(self._create_chunk(
                    chunk_text, page_number, section, paper_id
                ))
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(current_chunk)
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(self._create_chunk(
                chunk_text, page_number, section, paper_id
            ))
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        text = text.replace('\n', ' ')
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """Get last N sentences for overlap"""
        total_words = 0
        overlap_sentences = []
        
        for sentence in reversed(sentences):
            word_count = len(sentence.split())
            if total_words + word_count > self.overlap:
                break
            overlap_sentences.insert(0, sentence)
            total_words += word_count
        
        return overlap_sentences
    
    def _create_chunk(self, text: str, page_number: int, section: str, paper_id: str) -> Dict:
        """Create chunk with metadata"""
        return {
            "chunk_id": str(uuid.uuid4()),
            "text": text,
            "page_number": page_number,
            "section": section,
            "paper_id": paper_id
        }
