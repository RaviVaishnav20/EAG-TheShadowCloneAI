from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, Union, List, Dict, Any
import requests
import numpy as np
import faiss
import json
import hashlib
import logging
import uuid
from pathlib import Path
import tempfile
import os
import io
import PyPDF2
from bs4 import BeautifulSoup
import httpx
from urllib.parse import urlparse
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Document Ingestion and Search API")

# Add CORS middleware for your Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your extension's origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 256
CHUNK_OVERLAP = 40
ROOT = Path(__file__).parent.resolve()
DOC_PATH = ROOT / "documents"
INDEX_CACHE = ROOT / "faiss_index"
INDEX_FILE = INDEX_CACHE / "index.bin"
METADATA_FILE = INDEX_CACHE / "metadata.json"
CACHE_FILE = INDEX_CACHE / "doc_index_cache.json"

# Create necessary directories
DOC_PATH.mkdir(exist_ok=True)
INDEX_CACHE.mkdir(exist_ok=True)

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

# Utility functions
def get_embedding(text: str):
    """Get embedding for text using local Ollama API"""
    response = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "prompt": text})
    response.raise_for_status()
    return np.array(response.json()["embedding"], dtype=np.float32)

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        chunks.append(" ".join(words[i:i+size]))
    return chunks

def file_hash(content):
    """Generate hash from content rather than file path"""
    return hashlib.md5(content.encode('utf-8') if isinstance(content, str) else content).hexdigest()

def load_index_and_metadata():
    """Load existing FAISS index and metadata"""
    metadata = json.loads(METADATA_FILE.read_text()) if METADATA_FILE.exists() else []
    index = faiss.read_index(str(INDEX_FILE)) if INDEX_FILE.exists() else None
    cache_meta = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    return index, metadata, cache_meta

def save_index_and_metadata(index, metadata, cache_meta):
    """Save FAISS index and metadata"""
    METADATA_FILE.write_text(json.dumps(metadata, indent=2))
    CACHE_FILE.write_text(json.dumps(cache_meta, indent=2))
    if index and index.ntotal > 0:
        faiss.write_index(index, str(INDEX_FILE))
        logger.info("Successfully saved FAISS index and metadata")

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF bytes"""
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to process PDF: {str(e)}")
    return text

def fetch_and_parse_html(url):
    """Fetch and parse HTML content from URL"""
    try:
        logger.info(f"Fetching URL: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = httpx.get(url, headers=headers, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        
        logger.info(f"Successfully fetched URL: {url}, status code: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style tags
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
        
        # Get text content
        text = soup.get_text(separator=' ', strip=True)
        
        # Try to get the title
        title = soup.find('title')
        title_text = title.get_text() if title else urlparse(url).netloc
        
        logger.info(f"Extracted title: {title_text[:50]}...")
        logger.info(f"Extracted {len(text)} characters of text")
        
        return text, title_text
    except Exception as e:
        logger.error(f"Failed to fetch or parse URL {url}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to process URL: {str(e)}")

def extract_url_from_doc_id(doc_id: str) -> Optional[str]:
    """Extract URL from doc_id if it appears to be a URL"""
    url_pattern = re.compile(r'^https?://\S+$')
    if url_pattern.match(doc_id):
        return doc_id
    return None

async def process_content(content, title, source_type, doc_id=None, url=None):
    """Process content and add to vector DB"""
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
    
    # Create chunks
    chunks = chunk_text(content)
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
                "url": url
            }
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
    
    return {"status": "success", "message": f"Added {len(chunks)} chunks to the index", "doc_id": doc_id}

# Endpoints
@app.post("/ingest/text")
async def ingest_text(background_tasks: BackgroundTasks, text_input: TextInput):
    """Ingest plain text content"""
    if not text_input.content.strip():
        raise HTTPException(status_code=400, detail="Text content cannot be empty")
    
    title = text_input.title or "Untitled Text Document"
    
    background_tasks.add_task(
        process_content, 
        text_input.content, 
        title, 
        "text"
    )
    
    return {"status": "processing", "message": "Text content is being processed"}

@app.post("/ingest/url")
async def ingest_url(background_tasks: BackgroundTasks, url_input: UrlInput):
    """Ingest content from a URL"""
    try:
        # Log the URL being processed
        logger.info(f"Processing URL: {url_input.url}")
        
        # Fetch and parse HTML
        text, title = fetch_and_parse_html(str(url_input.url))
        
        # Log the text length obtained
        logger.info(f"Extracted {len(text)} characters from URL")
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text content could be extracted from URL")
        
        # Use provided title or extracted title
        final_title = url_input.title or title
        
        # Generate a unique ID instead of using the URL directly
        unique_id = hashlib.md5(str(url_input.url).encode()).hexdigest()
        
        # Store the URL in metadata but use the hash as the ID
        background_tasks.add_task(
            process_content, 
            text, 
            final_title, 
            "html", 
            doc_id=unique_id,
            url=str(url_input.url)
        )
        
        # Return response with the original URL for reference
        return {
            "status": "processing", 
            "message": "URL content is being processed", 
            "title": final_title,
            "url": str(url_input.url),
            "doc_id": unique_id
        }
    except Exception as e:
        logger.error(f"Error processing URL {url_input.url}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process URL: {str(e)}")
    
@app.post("/ingest/pdf")
async def ingest_pdf(
    background_tasks: BackgroundTasks,
    pdf_file: UploadFile = File(...),
    title: Optional[str] = Form(None)
):
    """Ingest content from PDF file"""
    if not pdf_file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    pdf_bytes = await pdf_file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="PDF file is empty")
    
    text = extract_text_from_pdf(pdf_bytes)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")
    
    # Use provided title or filename
    final_title = title or pdf_file.filename
    
    background_tasks.add_task(
        process_content, 
        text, 
        final_title, 
        "pdf"
    )
    
    return {"status": "processing", "message": "PDF is being processed", "title": final_title}

@app.post("/ingest/universal")
async def ingest_universal(
    background_tasks: BackgroundTasks,
    content_type: str = Form(...),
    title: Optional[str] = Form(None),
    text_content: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """Universal ingestion endpoint that handles all content types"""
    if content_type == "text" and text_content:
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Text content cannot be empty")
        
        final_title = title or "Untitled Text Document"
        
        background_tasks.add_task(
            process_content, 
            text_content, 
            final_title, 
            "text"
        )
        
        return {"status": "processing", "message": "Text content is being processed", "title": final_title}
    
    elif content_type == "url" and url:
        try:
            text, extracted_title = fetch_and_parse_html(url)
            final_title = title or extracted_title
            
            background_tasks.add_task(
                process_content, 
                text, 
                final_title, 
                "html", 
                doc_id=url
            )
            
            return {"status": "processing", "message": "URL content is being processed", "title": final_title}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    elif content_type == "pdf" and file:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        pdf_bytes = await file.read()
        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="PDF file is empty")
        
        text = extract_text_from_pdf(pdf_bytes)
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        final_title = title or file.filename
        
        background_tasks.add_task(
            process_content, 
            text, 
            final_title, 
            "pdf"
        )
        
        return {"status": "processing", "message": "PDF is being processed", "title": final_title}
    
    else:
        raise HTTPException(
            status_code=400, 
            detail="Invalid request. Please provide valid content_type and corresponding data"
        )

# Enhanced Search endpoint from search_api.py
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
            effective_min_score =0.0
            # effective_min_score = query_params.min_score
            if score < effective_min_score:
                logger.info(f"Skipping result {i} due to low score: {score} < {effective_min_score}")
                continue
            
            # Extract metadata for this result
            result_meta = metadata[idx].copy()
            print(result_meta)
            print("==========================")
            print(result_meta.get("source_type"))
            # For HTML content, extract URL from doc_id if it's a URL
            url = None
            if result_meta.get("source_type") == "html":
                # First check if doc_id is a URL
                url = result_meta.get("url", "")
            
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
                # if url:
                #  result["chunk"] = result["chunk"]+'\n'+url
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

# Additional diagnostic endpoints from search_api.py
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

@app.on_event("startup")
async def startup_event():
    """Ensure directories exist on startup"""
    DOC_PATH.mkdir(exist_ok=True)
    INDEX_CACHE.mkdir(exist_ok=True)
    logger.info("Application started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)