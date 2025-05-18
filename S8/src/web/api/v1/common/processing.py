from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import numpy as np
import faiss
import uuid
from pathlib import Path
import sys
from PIL import Image  # Add pillow dependency
from io import BytesIO

# Import trafilatura and pymupdf4llm for better extraction
import trafilatura
import pymupdf4llm

from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[4]  # This gets /Users/ravi/EAG-TheShadowCloneAI/S8

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.common.logger.logger import get_logger

logger = get_logger()


from src.server.rag_server.common.config.rag_config import DOC_PATH, INDEX_CACHE

# Define models
class TextInput(BaseModel):
    content: str
    title: Optional[str] = None
    source_type: str = "text"

class UrlInput(BaseModel):
    url: HttpUrl
    title: Optional[str] = None

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5
    include_context: bool = True
    min_score: float = 0.0  # Minimum similarity score threshold

class SearchResult(BaseModel):
    doc_id: str
    title: str
    chunk: str
    chunk_id: str
    score: float
    rank: int
    source_type: str
    url: Optional[str] = None  # Will be filled for HTML content

class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_results: int

from src.server.rag_server.common.utils import get_embedding, replace_images_with_captions,semantic_merge,file_hash, load_index_and_metadata, save_index_and_metadata, extract_title_from_content, determine_source_type


async def process_content(content, title, source_type, doc_id=None, url=None, filename=None):
    """Process content and add to vector DB using improved chunking"""
    # Generate unique ID if not provided
    if not doc_id:
        doc_id = str(uuid.uuid4())
    
    # Create a content hash for cache checking
    content_hash = file_hash(content)
    
    # Load existing index and metadata
    index, metadata, cache_meta = load_index_and_metadata()
    
    # Check if we've already processed this content
    if doc_id in cache_meta and cache_meta[doc_id] == content_hash:
        return {"status": "skipped", "message": f"Content already exists in index with ID {doc_id}", "doc_id": doc_id}
    
    # Create chunks using semantic merge instead of simple chunking
    if len(content.split()) < 10:
        logger.warning(f"Content too short for semantic merge - using as single chunk")
        chunks = [content.strip()]
    else:
        logger.info(f"Running semantic merge with {len(content.split())} words")
        chunks = semantic_merge(content)
    
    if not chunks:
        raise HTTPException(status_code=400, detail="Content too short to process")
    
    # Get embeddings for chunks
    embeddings = []
    new_metadata = []
    
    for i, chunk in enumerate(chunks):
        try:
            embedding = get_embedding(chunk)
            embeddings.append(embedding)
            
            chunk_metadata = {
                "doc_id": doc_id,
                "title": title,
                "source_type": source_type,
                "chunk": chunk,
                "chunk_id": f"{doc_id}_{i}",
            }
            
            # Add URL only if it exists
            if url:
                chunk_metadata["url"] = url
                
            new_metadata.append(chunk_metadata)
        except Exception as e:
            logger.error(f"Failed to get embedding for chunk {i}: {e}")
    
    if not embeddings:
        raise HTTPException(status_code=500, detail="Failed to generate any embeddings")
    
    # Initialize index if needed
    if index is None:
        dim = len(embeddings[0])
        index = faiss.IndexFlatL2(dim)
    
    # Add embeddings to index
    embeddings_array = np.stack(embeddings)
    index.add(embeddings_array)
    
    # Update metadata
    metadata.extend(new_metadata)
    
    # Update cache
    cache_meta[doc_id] = content_hash
    
    # Save index and metadata
    save_index_and_metadata(index, metadata, cache_meta)
    
    # If it's a file type we want to save locally, save it
    if source_type in ["pdf", "html"]:
        # Create a safe filename by replacing invalid characters
        safe_filename = "".join(c if c.isalnum() or c in "-_." else "_" for c in doc_id)
        # Truncate if too long (filesystem limits)
        if len(safe_filename) > 200:
            safe_filename = safe_filename[:200]
        
        # Save content to file
        try:
            with open(DOC_PATH / f"{safe_filename}.txt", "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to save content file: {e}")
            # We won't raise an exception here, as the index was already updated
    
    return {
        "status": "success", 
        "message": f"Added {len(chunks)} chunks to the index", 
        "doc_id": doc_id,
        "title": title,
        "source_type": source_type
    }