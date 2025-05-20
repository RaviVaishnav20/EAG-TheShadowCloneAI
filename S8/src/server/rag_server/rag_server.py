from mcp.server.fastmcp import FastMCP
import trafilatura
import sys
import faiss
import numpy as np
import uuid
from pathlib import Path
from tqdm import tqdm
from typing import Optional
import logging

# Path setup
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# Import project modules

from src.server.rag_server.schema.rag_model import UrlInput, FilePathInput
from src.server.rag_server.common.utils import (
    get_embedding, semantic_merge, replace_images_with_captions, load_index_and_metadata, file_hash, save_index_and_metadata, extract_title_from_content, determine_source_type
)
from src.server.rag_server.common.config.rag_config import DOC_PATH, INDEX_CACHE
from src.server.rag_server.common.content_extracter import extract_pdf, extract_webpage

mcp = FastMCP("RagServer")
logger = logging.getLogger("shadow_clone_agent")
def mcp_log(level, message):
    """Simplified logging helper that maps to logger methods"""
    if level == "INFO":
        logger.info(message)
    elif level == "ERROR":
        logger.error(message)
    elif level == "WARN":
        logger.warning(message)
    else:
        logger.info(f"[{level}] {message}")

from pydantic import BaseModel
class ProcessDoc_Input(BaseModel):
    input_path: Optional[str] = None


from src.server.rag_server.schema.rag_model import UrlInput, MarkdownOutput, FilePathInput
import trafilatura
import pymupdf4llm
import os
import re


from src.server.rag_server.common.config.rag_config import GLOBAL_IMAGE_DIR
from src.server.rag_server.common.utils import replace_images_with_captions
from src.common.logger.logger import get_logger

logger = get_logger()  

@mcp.tool() 
def extract_webpage(input: UrlInput) -> MarkdownOutput:
    """Extract and convert webpage content to markdown. Usage: extract_webpage|input={"url": "https://example.com"}"""
    
    downloaded = trafilatura.fetch_url(input.url)
    if not downloaded:
        return MarkdownOutput(markdown="Failed to download the webpage.")
    
    markdown = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=True,
        include_images=True,
        output_format='markdown'
    ) or ""
    
    markdown = replace_images_with_captions(markdown)
    return MarkdownOutput(markdown=markdown)

@mcp.tool()
def extract_pdf(input: FilePathInput) -> MarkdownOutput:
    """Convert PDF file content to markdown format. Usage: extract_pdf|input={"file_path": "documents/dlf.pdf"}"""

    if not os.path.exists(input.file_path):
        return MarkdownOutput(markdown=f"File not found: {input.file_path}")
    
    global_image_dir = GLOBAL_IMAGE_DIR
    global_image_dir.mkdir(parents=True, exist_ok=True)

    markdown = pymupdf4llm.to_markdown(
        input.file_path,
        write_images = True,
        image_path = str(global_image_dir)
    )

    #Re-point image links in the markdown
    markdown = re.sub(
        r'!\[\]\((.*?/images/)([^)]+)\)',
        r'![](images/\2)',
        markdown.replace("\\", "/")
    )
        
    markdown = replace_images_with_captions(markdown)
    return MarkdownOutput(markdown=markdown)


class SearchQuery(BaseModel):
    query: str
    top_k: int = 2
    include_context: bool = True
    min_score: float = 0.0  # Minimum similarity score threshold

@mcp.tool()
async def search_documents(query, top_k=5, include_context=True, min_score=0.8):
    """
    Search for information similar to the query in local documents and return the results.
    """
    try:
        # Load index and metadata
        index, metadata, _ = load_index_and_metadata()
        
        if index is None or index.ntotal == 0:
            return {"results": [], "query": query, "total_results": 0}
        
        logger.info(f"Successfully loaded index with {index.ntotal} vectors and {len(metadata)} metadata entries")
        
        # Get embedding for query
        query_embedding = get_embedding(query)
        query_embedding = np.array([query_embedding], dtype=np.float32)
        
        # Search
        k = min(top_k * 2, index.ntotal)  # Fetch more results than needed for filtering
        D, I = index.search(query_embedding, k)
        
        logger.info(f"Search returned {len(I[0])} initial results")
        
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
            if max_distance == min_distance:
                # All distances are the same
                score = 0.7  # Default reasonable score
            else:
                # Normalize to 0-1 range and invert (1 = closest match)
                score = float(1.0 - ((distance - min_distance) / distance_range))
            print(f"score: {score}")
            # Skip results below the minimum score threshold
            if score < min_score:
                logger.debug(f"Skipping result {i} due to low score: {score} < {min_score}")
                continue
            
            # Extract metadata for this result
            result_meta = metadata[idx].copy()
            
            # For HTML content, extract URL if available
            url = None
            if result_meta.get("source_type") == "html":
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
            if include_context:
                result["chunk"] = result_meta.get("chunk", "")
            
            results.append(result)
        
        # Sort by score and limit to requested number
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
        
        logger.info(f"Returning {len(results)} final filtered results")
        
        return {
            "results": results,
            "query": query,
            "total_results": len(results)
        }
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            "results": [], 
            "query": query, 
            "total_results": 0
        }
    
async def process_documents(path :ProcessDoc_Input):
    """
    Process and index documents for retrieval augmented generation (RAG) using a unified multimodal approach.
    
    This tool indexes documents by extracting text content, chunking it semantically, generating embeddings,
    and storing them in a FAISS vector database. It supports multiple document types and intelligently handles
    processing based on file format.
    
    Capabilities:
    - Indexes PDF, TXT, MD, HTML, and URL files
    - Extract text with specialized extractors for each file type
    - Creates semantic chunks of content
    - Generates vector embeddings for each chunk
    - Builds searchable FAISS vector index
    - Caches results to avoid reprocessing unchanged documents
    
    Args:
        input_path (Optional[str]): Path to specific file or directory to process. 
                             If None, processes all supported files in the configured document directory.
                             Path can be absolute or relative to document directory.
    
    Returns:
        dict: A dictionary containing:
            - status: "success", "error", or "info"
            - message: A summary of the operation
            - details (when successful): Dictionary with:
                - processed: Number of files processed
                - skipped: Number of unchanged files skipped
                - errors: Number of files that failed processing
                - results: List of dictionaries with per-file results
    
    Examples:
        # Process all documents in the configured directory
        process_documents()
        
        # Process a specific PDF file
        process_documents("my_document.pdf")
        
        # Process all files in a subdirectory
        process_documents("project_docs/")
    """
    mcp_log("INFO", "Indexing documents with unified RAG pipeline...")
    
    # Ensure directories exist
    DOC_PATH.mkdir(exist_ok=True, parents=True)
    INDEX_CACHE.mkdir(exist_ok=True)
    
    # Load cache and existing data
    index, metadata, cache_meta = load_index_and_metadata()
    
    # Determine which files to process
    if path.input_path:
        target_path = Path(path.input_path)
        if not target_path.is_absolute():
            target_path = DOC_PATH / target_path
            
        if target_path.is_file():
            files_to_process = [target_path]
        elif target_path.is_dir():
            files_to_process = list(target_path.glob("*.*"))
        else:
            mcp_log("ERROR", f"Path not found: {path.input_path}")
            return {"status": "error", "message": f"Path not found: {path.input_path}"}
    else:
        # Process all files in DOC_PATH
        files_to_process = list(DOC_PATH.glob("*.*"))
    
    # Filter out unsupported file types
    supported_extensions = ['.pdf', '.txt', '.md', '.html', '.htm', '.url']
    files_to_process = [f for f in files_to_process if f.suffix.lower() in supported_extensions]
    
    if not files_to_process:
        mcp_log("WARN", "No supported files found to process")
        return {"status": "info", "message": "No supported files found to process"}
    
    mcp_log("INFO", f"Found {len(files_to_process)} files to process")
    
    # Process files one by one
    processed_count = 0
    skipped_count = 0
    error_count = 0
    results = []
    
    for file in tqdm(files_to_process, desc="Processing documents"):
        # Check cache first
        fhash = file_hash(file)
        if file.name in cache_meta and cache_meta[file.name] == fhash:
            mcp_log("SKIP", f"Skipping unchanged file: {file.name}")
            skipped_count += 1
            continue
        
        mcp_log("PROC", f"Processing: {file.name}")
        try:
            ext = file.suffix.lower()
            markdown = ""
            url = None  # Initialize URL as None

            if ext == ".pdf":
                mcp_log("INFO", f"Using MuPDF4LLM to extract {file.name}")
                markdown = extract_pdf(FilePathInput(file_path=str(file))).markdown

            elif ext in [".html", ".htm", ".url"]:
                mcp_log("INFO", f"Using Trafilatura to extract {file.name}")
                if ext == ".url":
                    with open(file, 'r', encoding='utf-8') as f:
                        url = f.readline().strip()
                    markdown = extract_webpage(UrlInput(url=url)).markdown
                else:
                    # For local HTML files, we need to read them first
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        html_content = f.read()
                    # Then use trafilatura to process the HTML content
                    markdown = trafilatura.extract(
                        html_content,
                        include_comments=False,
                        include_tables=True,
                        include_images=True,
                        output_format='markdown'
                    ) or ""
                    markdown = replace_images_with_captions(markdown)

            else:
                # For TXT and MD files, just read the content
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    markdown = f.read()

            if not markdown.strip():
                mcp_log("WARN", f"No content extracted from {file.name}")
                continue

            # Generate enhanced metadata fields
            doc_id = str(uuid.uuid4())  # Generate unique doc_id
            source_type = determine_source_type(ext)
            title = extract_title_from_content(markdown, file.name)

            if len(markdown.split()) < 10:
                mcp_log("WARN", f"Content too short for semantic merge in {file.name} → Skipping chunking.")
                chunks = [markdown.strip()]
            else:
                mcp_log("INFO", f"Running semantic merge on {file.name} with {len(markdown.split())} words")
                chunks = semantic_merge(markdown)

            # Process embeddings for this file
            embeddings_for_file = []
            new_metadata = []
            for i, chunk in enumerate(tqdm(chunks, desc=f"Embedding {file.name}")):
                embedding = get_embedding(chunk)
                embeddings_for_file.append(embedding)
                
                # Enhanced metadata with all the requested fields
                chunk_metadata = {
                    "doc": file.name,  # Keep original field
                    "doc_id": doc_id,  # New field: unique document ID
                    "title": title,    # New field: extracted or fallback title
                    "source_type": source_type,  # New field: type of document
                    "chunk": chunk,    # Original field: the actual content
                    "chunk_id": f"{doc_id}_{i}"  # Modified to use doc_id instead of file.stem
                }
                
                # Add URL only if it exists
                if url:
                    chunk_metadata["url"] = url
                
                new_metadata.append(chunk_metadata)

            if embeddings_for_file:
                if index is None:
                    dim = len(embeddings_for_file[0])
                    index = faiss.IndexFlatL2(dim)
                
                # Add embeddings to index
                index.add(np.stack(embeddings_for_file))
                metadata.extend(new_metadata)
                cache_meta[file.name] = fhash
                
                # Immediately save index and metadata
                save_index_and_metadata(index, metadata, cache_meta)
                mcp_log("SAVE", f"Saved FAISS index and metadata after processing {file.name}")
                
                results.append({
                    "file": file.name,
                    "doc_id": doc_id,
                    "title": title,
                    "status": "success",
                    "chunks": len(chunks)
                })
                processed_count += 1
            
        except Exception as e:
            mcp_log("ERROR", f"Failed to process {file.name}: {str(e)}")
            error_count += 1
            results.append({
                "file": file.name,
                "status": "error",
                "error": str(e)
            })
    
    # Final save (though likely not needed since we save after each file)
    save_index_and_metadata(index, metadata, cache_meta)
    
    # Summary
    mcp_log("INFO", f"Processing complete. Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}")
    
    return {
        "status": "success",
        "message": f"Successfully processed {processed_count} files",
        "details": {
            "processed": processed_count,
            "skipped": skipped_count,
            "errors": error_count,
            "results": results
        }
    }

if __name__ == "__main__":
    print("rag_server.py starting")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
            mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
        print("\nShutting down...")

# # For command-line usage
# if __name__ == "__main__":
#     if len(sys.argv) > 1:
#         path = sys.argv[1]
#         result = asyncio.run(process_documents(path))
#     else:
#         result = asyncio.run(process_documents())
        
#     print(json.dumps(result, indent=2))



    