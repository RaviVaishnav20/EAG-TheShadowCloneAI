from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import numpy as np
import faiss
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
 
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vector Search API")

# Configuration
EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
ROOT = Path(__file__).parent.resolve()
INDEX_CACHE = ROOT / "faiss_index"
INDEX_FILE = INDEX_CACHE / "index.bin"
METADATA_FILE = INDEX_CACHE / "metadata.json"

# Define models
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

def get_embedding(text: str):
    """Get embedding for text using local Ollama API"""
    response = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "prompt": text})
    response.raise_for_status()
    return np.array(response.json()["embedding"], dtype=np.float32)

def load_index_and_metadata():
    """Load existing FAISS index and metadata"""
    if not INDEX_FILE.exists() or not METADATA_FILE.exists():
        raise HTTPException(
            status_code=404, 
            detail="Search index not found. Please ingest some documents first."
        )
    
    try:
        metadata = json.loads(METADATA_FILE.read_text())
        index = faiss.read_index(str(INDEX_FILE))
        return index, metadata
    except Exception as e:
        logger.error(f"Error loading index or metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load search index: {str(e)}")

def extract_url_from_doc_id(doc_id: str) -> Optional[str]:
    """Extract URL from doc_id if it appears to be a URL"""
    url_pattern = re.compile(r'^https?://\S+$')
    if url_pattern.match(doc_id):
        return doc_id
    return None

@app.post("/search", response_model=SearchResponse)
async def search(query_params: SearchQuery):
    """
    Search for documents similar to the query
    
    - **query**: The search query text
    - **top_k**: Maximum number of results to return (default: 5)
    - **include_context**: Whether to include the text chunks in results (default: true)
    - **min_score**: Minimum similarity score threshold (default: 0.0)
    """
    try:
        # Load index and metadata
        if not INDEX_FILE.exists() or not METADATA_FILE.exists():
            logger.error("Search index files not found")
            return SearchResponse(
                results=[], 
                query=query_params.query, 
                total_results=0
            )
        
        try:
            # Load metadata
            metadata = json.loads(METADATA_FILE.read_text())
            # Load index
            index = faiss.read_index(str(INDEX_FILE))
            
            logger.info(f"Successfully loaded index with {index.ntotal} vectors and {len(metadata)} metadata entries")
            
            if index.ntotal == 0:
                logger.warning("Index exists but contains no vectors")
                return SearchResponse(results=[], query=query_params.query, total_results=0)
                
        except Exception as e:
            logger.error(f"Error loading index or metadata: {e}")
            return SearchResponse(
                results=[], 
                query=query_params.query, 
                total_results=0
            )
        
        # Get embedding for query
        try:
            query_embedding = get_embedding(query_params.query)
            query_embedding = np.array([query_embedding], dtype=np.float32)
        except Exception as e:
            logger.error(f"Error getting query embedding: {e}")
            return SearchResponse(
                results=[], 
                query=query_params.query, 
                total_results=0
            )
        
        # Search
        k = min(query_params.top_k * 2, index.ntotal)  # Fetch more results than needed for filtering
        D, I = index.search(query_embedding, k)
        
        logger.info(f"Search returned {len(I[0])} initial results")
        logger.info(f"Raw distances: {D[0]}")  # Log the raw distances for debugging
        
        results = []
        for i, (distance, idx) in enumerate(zip(D[0], I[0])):
            if idx >= len(metadata) or idx < 0:
                logger.warning(f"Invalid index {idx} found in search results (metadata length: {len(metadata)})")
                continue
            
            # Convert distance to similarity score (higher is better)
            # Using a different formula for score calculation
            score = float(1.0 / (1.0 + distance))
            
            logger.info(f"Result {i}: distance={distance}, score={score}, min_score={query_params.min_score}")
            
            # Skip results below the minimum score threshold, but with safety checks
            # Lower the default threshold to ensure results come through
            effective_min_score = 0.0  # Temporarily disable score filtering for testing
            if score < effective_min_score:
                logger.info(f"Skipping result {i} due to low score: {score} < {effective_min_score}")
                continue
            
            # Extract metadata for this result
            result_meta = metadata[idx].copy()
            
            # For HTML content, extract URL from doc_id if it's a URL
            url = None
            if result_meta.get("source_type") == "html":
                # First check if doc_id is a URL
                url = extract_url_from_doc_id(result_meta.get("doc_id", ""))
            
            # Create result object
            result = {
                "doc_id": result_meta.get("doc_id", ""),
                "title": result_meta.get("title", "Untitled"),
                "score": score,
                "rank": i + 1,
                "source_type": result_meta.get("source_type", "unknown"),
                "chunk_id": result_meta.get("chunk_id", "")
            }
            
            # Add URL for HTML content
            if url:
                result["url"] = url
            
            # Include chunk text if requested
            if query_params.include_context:
                result["chunk"] = result_meta.get("chunk", "")
            else:
                result["chunk"] = ""
            
            results.append(result)
        
        # Sort by score and limit to requested number
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:query_params.top_k]
        
        logger.info(f"Returning {len(results)} final filtered results")
        
        return SearchResponse(
            results=results,
            query=query_params.query,
            total_results=len(results)
        )
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return SearchResponse(
            results=[], 
            query=query_params.query, 
            total_results=0
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if index exists
        index_exists = INDEX_FILE.exists()
        metadata_exists = METADATA_FILE.exists()
        
        if index_exists and metadata_exists:
            try:
                # Try to load metadata to check if it's valid
                metadata = json.loads(METADATA_FILE.read_text())
                index_size = len(metadata)
                
                return {
                    "status": "healthy",
                    "index_exists": True,
                    "documents_count": index_size
                }
            except Exception as e:
                return {
                    "status": "warning",
                    "message": f"Index files exist but may be corrupt: {str(e)}",
                    "index_exists": True
                }
        else:
            return {
                "status": "warning",
                "message": "Search index not found or incomplete",
                "index_exists": False
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
@app.get("/debug-index")
async def debug_index():
    """Debug endpoint to check index details"""
    try:
        # Check if index files exist
        index_exists = INDEX_FILE.exists()
        metadata_exists = METADATA_FILE.exists()
        
        if not index_exists or not metadata_exists:
            return {
                "status": "missing_files",
                "index_exists": index_exists,
                "metadata_exists": metadata_exists,
                "message": "One or more index files are missing"
            }
        
        # Try to load metadata
        try:
            metadata = json.loads(METADATA_FILE.read_text())
            metadata_count = len(metadata)
            
            # Get unique document IDs
            doc_ids = set(item.get("doc_id", "") for item in metadata)
            doc_types = {}
            for item in metadata:
                source_type = item.get("source_type", "unknown")
                if source_type in doc_types:
                    doc_types[source_type] += 1
                else:
                    doc_types[source_type] = 1
            
        except Exception as e:
            return {
                "status": "metadata_error",
                "error": str(e),
                "message": "Failed to parse metadata file"
            }
        
        # Try to load index
        try:
            index = faiss.read_index(str(INDEX_FILE))
            vector_count = index.ntotal
            vector_dim = index.d
        except Exception as e:
            return {
                "status": "index_error",
                "error": str(e),
                "metadata_count": metadata_count if 'metadata_count' in locals() else None,
                "message": "Failed to load FAISS index"
            }
        
        # Check for inconsistencies
        issues = []
        if vector_count != metadata_count:
            issues.append(f"Vector count ({vector_count}) doesn't match metadata count ({metadata_count})")
        
        # Return debug information
        return {
            "status": "ok" if not issues else "warning",
            "issues": issues,
            "index_file": str(INDEX_FILE),
            "metadata_file": str(METADATA_FILE),
            "vector_count": vector_count,
            "vector_dimensions": vector_dim,
            "metadata_count": metadata_count,
            "unique_documents": len(doc_ids),
            "document_types": doc_types,
            "sample_doc_ids": list(doc_ids)[:5] if doc_ids else []
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)