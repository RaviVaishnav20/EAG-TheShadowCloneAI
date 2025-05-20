from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import numpy as np
import hashlib
from pathlib import Path
import tempfile
import os
import re
import json
import faiss
from PIL import Image  # Add pillow dependency
import trafilatura
import pymupdf4llm

from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[4]  # This gets /Users/ravi/EAG-TheShadowCloneAI/S8

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.server.rag_server.common.utils import get_embedding, replace_images_with_captions, load_index_and_metadata
from src.web.api.v1.common.processing import process_content
from src.server.rag_server.common.config.rag_config import GLOBAL_IMAGE_DIR
from src.common.logger.logger import get_logger

logger = get_logger()

app = FastAPI(title="Document Ingestion and Search API")

# Add CORS middleware for your Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your extension's origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        index, metadata, _ = load_index_and_metadata()
        # Load index and metadata
        if index is None or index.ntotal == 0:
            return SearchResponse(results=[], query=query_params.query, total_results=0)
        
        try:
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
        
        # Find max and min distances to normalize scores
        if len(D[0]) > 0:
            max_distance = max(D[0])
            min_distance = min(D[0])
            distance_range = max(max_distance - min_distance, 0.001)  # Prevent division by zero
        else:
            max_distance = 1.0
            min_distance = 0.0
            distance_range = 1.0
            
        results = []
        for i, (distance, idx) in enumerate(zip(D[0], I[0])):
            if idx >= len(metadata) or idx < 0:
                logger.warning(f"Invalid index {idx} found in search results (metadata length: {len(metadata)})")
                continue
            
            # Calculate normalized score (1.0 is best, 0.0 is worst)
            # Inverting because smaller distance is better
            if max_distance == min_distance:
                # All distances are the same
                score = 0.7  # Default reasonable score
            else:
                # Normalize to 0-1 range and invert (1 = closest match)
                score = float(1.0 - ((distance - min_distance) / distance_range))
                
                # Alternative: use exponential decay formula
                # score = float(math.exp(-distance))
            
            logger.info(f"Result {i}: distance={distance}, score={score}, min_score={query_params.min_score}")
            
            # Skip results below the minimum score threshold
            effective_min_score = query_params.min_score
            if score < effective_min_score:
                logger.info(f"Skipping result {i} due to low score: {score} < {effective_min_score}")
                continue
            
            # Extract metadata for this result
            result_meta = metadata[idx].copy()
            
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
# @app.post("/search", response_model=SearchResponse)
# async def search(query_params: SearchQuery):
#     """
#     Search for documents similar to the query
    
#     - **query**: The search query text
#     - **top_k**: Maximum number of results to return (default: 5)
#     - **include_context**: Whether to include the text chunks in results (default: true)
#     - **min_score**: Minimum similarity score threshold (default: 0.0)
#     """
    
    
    
#     try:
#         index, metadata, _ = load_index_and_metadata()
#         # Load index and metadata
#         if index is None or index.ntotal == 0:
#             return SearchResponse(results=[], query=query_params.query, total_results=0)
        
#         try:
          
            
#             logger.info(f"Successfully loaded index with {index.ntotal} vectors and {len(metadata)} metadata entries")
            
#             if index.ntotal == 0:
#                 logger.warning("Index exists but contains no vectors")
#                 return SearchResponse(results=[], query=query_params.query, total_results=0)
                
#         except Exception as e:
#             logger.error(f"Error loading index or metadata: {e}")
#             return SearchResponse(
#                 results=[], 
#                 query=query_params.query, 
#                 total_results=0
#             )
        
#         # Get embedding for query
#         try:
#             query_embedding = get_embedding(query_params.query)
#             query_embedding = np.array([query_embedding], dtype=np.float32)
#         except Exception as e:
#             logger.error(f"Error getting query embedding: {e}")
#             return SearchResponse(
#                 results=[], 
#                 query=query_params.query, 
#                 total_results=0
#             )
        
#         # Search
#         k = min(query_params.top_k * 2, index.ntotal)  # Fetch more results than needed for filtering
#         D, I = index.search(query_embedding, k)
        
#         logger.info(f"Search returned {len(I[0])} initial results")
#         logger.info(f"Raw distances: {D[0]}")  # Log the raw distances for debugging
        
#         results = []
#         for i, (distance, idx) in enumerate(zip(D[0], I[0])):
#             if idx >= len(metadata) or idx < 0:
#                 logger.warning(f"Invalid index {idx} found in search results (metadata length: {len(metadata)})")
#                 continue
            
            
#             score = float(1.0 / (1.0 + distance))
            
#             logger.info(f"Result {i}: distance={distance}, score={score}, min_score={query_params.min_score}")
            
#             # Skip results below the minimum score threshold, but with safety checks
#             # Lower the default threshold to ensure results come through
#             effective_min_score =0.0
#             # effective_min_score = query_params.min_score
#             if score < effective_min_score:
#                 logger.info(f"Skipping result {i} due to low score: {score} < {effective_min_score}")
#                 continue
            
#             # Extract metadata for this result
#             result_meta = metadata[idx].copy()
#             print(result_meta)
#             print("==========================")
#             print(result_meta.get("source_type"))
#             # For HTML content, extract URL from doc_id if it's a URL
#             url = None
#             if result_meta.get("source_type") == "html":
#                 # First check if doc_id is a URL
#                 url = result_meta.get("url", "")
            
#             # Create result object
#             result = {
#                 "doc_id": result_meta.get("doc_id", ""),
#                 "title": result_meta.get("title", "Untitled"),
#                 "score": score,
#                 "rank": i + 1,
#                 "source_type": result_meta.get("source_type", "unknown"),
#                 "chunk_id": result_meta.get("chunk_id", "")
#             }
            
#             # Add URL for HTML content
#             if url:
#                 result["url"] = url
            
#             # Include chunk text if requested
#             if query_params.include_context:
#                 result["chunk"] = result_meta.get("chunk", "")
#                 # if url:
#                 #  result["chunk"] = result["chunk"]+'\n'+url
#             else:
#                 result["chunk"] = ""
            
#             results.append(result)
        
#         # Sort by score and limit to requested number
#         results = sorted(results, key=lambda x: x["score"], reverse=True)[:query_params.top_k]
        
#         logger.info(f"Returning {len(results)} final filtered results")
        
#         return SearchResponse(
#             results=results,
#             query=query_params.query,
#             total_results=len(results)
#         )
    
#     except Exception as e:
#         logger.error(f"Search error: {e}")
#         return SearchResponse(
#             results=[], 
#             query=query_params.query, 
#             total_results=0
#         )


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
    """Ingest content from a URL using trafilatura for better extraction"""
    try:
        # Log the URL being processed
        logger.info(f"Processing URL: {url_input.url}")
        
        # Fetch using trafilatura instead of BeautifulSoup
        downloaded = trafilatura.fetch_url(str(url_input.url))
        if not downloaded:
            raise HTTPException(status_code=400, detail="Failed to download the webpage")
        
        # Extract using trafilatura
        markdown = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            include_images=True,
            output_format='markdown'
        ) or ""
        
        # Process any images in the markdown
        markdown = replace_images_with_captions(markdown)
        
        if not markdown.strip():
            raise HTTPException(status_code=400, detail="No text content could be extracted from URL")
        
        # Extract title
        title_match = re.search(r'^# (.*?)$', markdown, re.MULTILINE)
        extracted_title = title_match.group(1) if title_match else None
        
        if not extracted_title:
            # Try to extract from HTML if markdown title extraction fails
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(downloaded, 'html.parser')
                title_tag = soup.find('title')
                extracted_title = title_tag.get_text() if title_tag else None
            except:
                extracted_title = None
                
        # Use provided title, extracted title, or domain name
        from urllib.parse import urlparse
        final_title = url_input.title or extracted_title or urlparse(str(url_input.url)).netloc
        
        # Generate a unique ID instead of using the URL directly
        unique_id = hashlib.md5(str(url_input.url).encode()).hexdigest()
        
        # Store the URL in metadata but use the hash as the ID
        background_tasks.add_task(
            process_content, 
            markdown, 
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
    """Ingest content from PDF file using pymupdf4llm for better extraction"""
    if not pdf_file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Create a temporary file to store the uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        # Write content to temp file
        pdf_bytes = await pdf_file.read()
        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="PDF file is empty")
        tmp.write(pdf_bytes)
        tmp_path = tmp.name
    
    try:
        # Create image directory
        global_image_dir = GLOBAL_IMAGE_DIR
        global_image_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract PDF to markdown using pymupdf4llm
        markdown = pymupdf4llm.to_markdown(
            tmp_path,
            write_images=True,
            image_path=str(global_image_dir)
        )
        
        # Re-point image links in the markdown
        markdown = re.sub(
            r'!\[\]\((.*?/images/)([^)]+)\)',
            r'![](images/\2)',
            markdown.replace("\\", "/")
        )
        
        # Process images with captioning
        markdown = replace_images_with_captions(markdown)
        
        if not markdown.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Use provided title or filename
        final_title = title or pdf_file.filename
        
        # Process the content with our semantic merge chunking
        background_tasks.add_task(
            process_content, 
            markdown, 
            final_title, 
            "pdf",
            filename=pdf_file.filename
        )
        
        return {"status": "processing", "message": "PDF is being processed", "title": final_title}
    
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    finally:
        # Clean up the temp file
        try:
            os.unlink(tmp_path)
        except:
            pass

@app.post("/ingest/universal")
async def ingest_universal(
    background_tasks: BackgroundTasks,
    content_type: str = Form(...),
    title: Optional[str] = Form(None),
    text_content: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """Universal ingestion endpoint that handles all content types with improved techniques"""
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
        # Redirect to the dedicated URL endpoint for better handling
        from fastapi.responses import JSONResponse
        url_input = UrlInput(url=url, title=title)
        response = await ingest_url(background_tasks, url_input)
        return JSONResponse(content=response)
    
    elif content_type == "pdf" and file:
        # Redirect to the dedicated PDF endpoint for better handling
        return await ingest_pdf(background_tasks, file, title)
    
    else:
        raise HTTPException(
            status_code=400, 
            detail="Invalid request. Please provide valid content_type and corresponding data"
        )

@app.get("/status")
async def check_status():
    """Check the status of the ingestion system"""
    try:
        index, metadata, cache_meta = load_index_and_metadata()
        
        document_count = len(set(meta.get("doc_id", "") for meta in metadata)) if metadata else 0
        chunk_count = len(metadata) if metadata else 0
        
        return {
            "status": "online",
            "documents_indexed": document_count,
            "chunks_indexed": chunk_count,
            "index_exists": index is not None,
            "metadata_exists": metadata is not None and len(metadata) > 0,
            "cache_entries": len(cache_meta) if cache_meta else 0
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)