from fastapi import APIRouter, HTTPException
from typing import List, Dict
from app.db.chroma import chroma_db
from collections import Counter
import re

router = APIRouter()

@router.get("/{paper_id}")
async def get_knowledge_graph(paper_id: str) -> Dict:
    """
    Generate knowledge graph for a paper
    
    Returns nodes and edges for visualization
    """
    try:
        # Get all chunks for the paper
        chunks = chroma_db.get_paper_chunks(paper_id)
        
        if not chunks:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Extract concepts from chunks
        all_concepts = []
        concept_chunks = {}  # Map concepts to chunks they appear in
        
        for chunk in chunks:
            concepts = extract_concepts_from_text(chunk["text"])
            all_concepts.extend(concepts)
            
            for concept in concepts:
                if concept not in concept_chunks:
                    concept_chunks[concept] = []
                concept_chunks[concept].append(chunk["chunk_id"])
        
        # Get top concepts by frequency
        concept_freq = Counter(all_concepts)
        top_concepts = [concept for concept, _ in concept_freq.most_common(20)]
        
        # Build nodes
        nodes = [
            {
                "id": concept,
                "label": concept,
                "size": concept_freq[concept],
                "type": "concept"
            }
            for concept in top_concepts
        ]
        
        # Build edges (co-occurrence in same chunk)
        edges = []
        edge_set = set()
        
        for chunk in chunks:
            chunk_concepts = [c for c in extract_concepts_from_text(chunk["text"]) if c in top_concepts]
            
            # Create edges between concepts in same chunk
            for i, concept1 in enumerate(chunk_concepts):
                for concept2 in chunk_concepts[i+1:]:
                    edge_key = tuple(sorted([concept1, concept2]))
                    if edge_key not in edge_set:
                        edges.append({
                            "source": concept1,
                            "target": concept2,
                            "weight": 1
                        })
                        edge_set.add(edge_key)
                    else:
                        # Increment weight for existing edge
                        for edge in edges:
                            if (edge["source"] == edge_key[0] and edge["target"] == edge_key[1]) or \
                               (edge["source"] == edge_key[1] and edge["target"] == edge_key[0]):
                                edge["weight"] += 1
                                break
        
        return {
            "nodes": nodes,
            "edges": edges,
            "paper_id": paper_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph generation failed: {str(e)}")

def extract_concepts_from_text(text: str) -> List[str]:
    """Extract technical concepts from text"""
    # Extract capitalized multi-word terms and technical terms
    concepts = []
    
    # Pattern for capitalized phrases (2-4 words)
    pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
    matches = re.findall(pattern, text)
    concepts.extend(matches)
    
    # Pattern for hyphenated technical terms
    pattern = r'\b([a-z]+-[a-z]+(?:-[a-z]+)*)\b'
    matches = re.findall(pattern, text.lower())
    concepts.extend(matches)
    
    # Pattern for acronyms
    pattern = r'\b([A-Z]{2,})\b'
    matches = re.findall(pattern, text)
    concepts.extend(matches)
    
    # Clean and deduplicate
    concepts = [c.strip() for c in concepts if len(c) > 3]
    
    return concepts
