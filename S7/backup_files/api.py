from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, Union, List
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

app = FastAPI(title="Document Ingestion API")

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


# Utility functions
def get_embedding(text: str):
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

async def process_content(content, title, source_type, doc_id=None):
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
                "chunk_id": f"{doc_id}_{i}"
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

def extract_url_from_doc_id(doc_id: str) -> Optional[str]:
    """Extract URL from doc_id if it appears to be a URL"""
    url_pattern = re.compile(r'^https?://\S+$')
    if url_pattern.match(doc_id):
        return doc_id
    return None

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
            doc_id=unique_id
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

# # Search endpoint (you mentioned you already have one, but including for completeness)
# @app.post("/search")
# async def search(query: SearchQuery):
#     """Search for documents similar to the query"""
#     try:
#         # Load index and metadata
#         index, metadata, _ = load_index_and_metadata()
        
#         if not index or index.ntotal == 0:
#             return {"results": [], "message": "No documents in the index"}
        
#         # Get embedding for query
#         query_embedding = get_embedding(query.query)
#         query_embedding = np.array([query_embedding], dtype=np.float32)
        
#         # Search
#         D, I = index.search(query_embedding, min(query.top_k, index.ntotal))
        
#         results = []
#         for i, (distance, idx) in enumerate(zip(D[0], I[0])):
#             if idx >= len(metadata) or idx < 0:
#                 continue
                
#             result = metadata[idx].copy()
#             result["score"] = float(1.0 / (1.0 + distance))  # Convert distance to similarity score
#             result["rank"] = i + 1
#             results.append(result)
        
#         return {"results": results}
    
#     except Exception as e:
#         logger.error(f"Search error: {e}")
#         raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Ensure directories exist on startup"""
    DOC_PATH.mkdir(exist_ok=True)
    INDEX_CACHE.mkdir(exist_ok=True)
    logger.info("Application started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)