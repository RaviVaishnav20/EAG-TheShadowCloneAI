import requests
import base64
import json
import re
from io import BytesIO
from PIL import Image  # Add pillow dependency
import hashlib
import numpy as np
import time
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.server.rag_server.common.config.rag_config import OLLAMA_BASE_URL, OLLAMA_CHAT_URL, OLLAMA_GENERATE_URL, OLLAMA_MODEL,CHUNK_OVERLAP,CHUNK_SIZE,EMBED_MODEL,EMBED_URL
from src.common.logger.logger import get_logger

logger = get_logger()

##========= Text extraction from image
def resize_image(image_data, max_size=1600, quality=85):
    """Resize image if it's too large."""
    try:
        img = Image.open(BytesIO(image_data))
        
        # Only resize if either dimension is larger than max_size
        if max(img.width, img.height) > max_size:
            # Preserve aspect ratio
            if img.width > img.height:
                new_width = max_size
                new_height = int(img.height * (max_size / img.width))
            else:
                new_height = max_size
                new_width = int(img.width * (max_size / img.height))
            
            img = img.resize((new_width, new_height), Image.LANCZOS)
            logger.info(f"Resized image from {img.width}x{img.height} to {new_width}x{new_height}")
        
        # Convert to RGB if image has alpha channel (RGBA)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Save to BytesIO
        output = BytesIO()
        img.save(output, format="JPEG", quality=quality)
        return output.getvalue()
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        return image_data  # Return original if resize fails

def caption_image(img_url_or_path: str, max_retries=1) -> str:
    logger.info(f"🖼️ Attempting to caption image: {img_url_or_path}")
    
    try:
        # Get the image data either from URL or local file
        if img_url_or_path.startswith("http"):
            # For URLs, download the image
            response = requests.get(img_url_or_path)
            if response.status_code != 200:
                logger.error(f"❌ Failed to download image: HTTP {response.status_code}")
                return f"[Image download failed: {img_url_or_path}]"
            image_data = response.content
        else:
            # For local files
            full_path = ROOT / "resources" / "documents" / img_url_or_path
            full_path = full_path.resolve()
            if not full_path.exists():
                logger.error(f"❌ Image file not found: {full_path}")
                return f"[Image file not found: {img_url_or_path}]"
                
            with open(full_path, "rb") as img_file:
                image_data = img_file.read()
        
        # Check if Ollama is running
        try:
            check_response = requests.get(f"{OLLAMA_BASE_URL}/api/version")
            if check_response.status_code != 200:
                logger.error(f"❌ Ollama service not available: HTTP {check_response.status_code}")
                return "[Ollama service not available]"
        except requests.exceptions.ConnectionError:
            logger.error("❌ Failed to connect to Ollama service. Is it running?")
            return "[Failed to connect to Ollama service. Is it running?]"
        
        # Progressive image processing with retries
        sizes = [1600, 1200, 800, 600]  # Progressive downsampling sizes
        
        for attempt in range(max_retries):
            try:
                # If not first attempt, resize the image
                if attempt > 0:
                    max_size = sizes[min(attempt, len(sizes)-1)]
                    image_data = resize_image(image_data, max_size=max_size)
                    logger.info(f"Retry {attempt+1}/{max_retries} with max size {max_size}px")
                
                # Encode the image
                encoded_image = base64.b64encode(image_data).decode("utf-8")
                
                # Prepare the request for chat API
                chat_request_data = {
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": "If there is lot of text in the image, then ONLY reply back with exact text in the image, else describe the image such that your response can replace 'alt-text' for it. Only explain the contents of the image and provide no further explanation.",
                            "images": [encoded_image]
                        }
                    ],
                    "stream": True
                }
                
                # Send the request
                logger.info(f"Using Ollama chat API with model {OLLAMA_MODEL}...")
                with requests.post(OLLAMA_CHAT_URL, json=chat_request_data, stream=True) as response:
                    if response.status_code != 200:
                        error_text = response.text
                        logger.error(f"❌ Ollama API error: HTTP {response.status_code}, Response: {error_text}")
                        # Continue to next retry if not the last attempt
                        if attempt < max_retries - 1:
                            time.sleep(1)  # Add small delay between retries
                            continue
                        return f"[LLM API error: {response.status_code}] - {error_text[:100]}"
                    
                    # Process successful response
                    caption_parts = []
                    for line in response.iter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                caption_parts.append(data["message"]["content"])
                            elif "response" in data:
                                caption_parts.append(data["response"])
                            
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                    
                    caption = "".join(caption_parts).strip()
                    logger.info(f"✅ Caption generated: {caption}")
                    return caption if caption else "[No caption returned]"
                    
            except Exception as e:
                logger.error(f"⚠️ Error during attempt {attempt+1}: {e}", exc_info=True)
                if attempt == max_retries - 1:
                    return f"[Image could not be processed: {img_url_or_path}]"
                time.sleep(1)  # Small delay between retries
                
    except Exception as e:
        logger.error(f"⚠️ Failed to caption image {img_url_or_path}: {e}", exc_info=True)
        return f"[Image could not be processed: {img_url_or_path}]"

def replace_images_with_captions(markdown: str) -> str:
    def replace(match):
        alt, src = match.group(1), match.group(2)
        try:
            caption = caption_image(src)
            logger.info(f"Generated caption: {caption}")
            
            # Attempt to delete only if local and file exists
            if not src.startswith("http"):
                img_path = ROOT / "resources" / "documents" / src
                if img_path.exists():
                    img_path.unlink()
                    logger.info(f"🗑️ Deleted image after captioning: {img_path}")
            
            return f"**Image** {caption}"
        except Exception as e:
            logger.warning(f"Image processing failed: {e}")
            return f"[Image could not be processed: {src}]"
    
    return re.sub(r'!\[(.*?)\]\((.*?)\)', replace, markdown)

# === Embedding and Text Processing Functions ===

def get_embedding(text: str):
    """Get embedding for text using local Ollama API"""
    response = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "prompt": text})
    response.raise_for_status()
    return np.array(response.json()["embedding"], dtype=np.float32)

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Simple chunking by splitting text into overlapping segments of words."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        chunks.append(" ".join(words[i:i+size]))
    return chunks

def semantic_merge(text: str) -> list[str]:
    """Splits text semantically using LLM: detects second topic and reuses leftover intelligently."""
    WORD_LIMIT = 512
    words = text.split()
    i = 0
    final_chunks = []

    while i < len(words):
        logger.info(f"Chunking from {i} to {i + WORD_LIMIT}")
        # Take next chunk of words
        chunk_words = words[i:i + WORD_LIMIT]
        chunk_text = " ".join(chunk_words).strip()

        prompt = f"""
     You are a markdown document segmenter.

     Here is a portion of a markdown document:

     ---
     {chunk_text}
     ---

     If this chunk clearly contains **more than one distinct topic or section**, reply ONLY with the **second part**, starting from the first sentence or heading of the new topic.

     If it's only one topic, reply with NOTHING.

     Keep markdown formatting intact.
    """
        try:
            response = requests.post(OLLAMA_GENERATE_URL, json={
                "model": OLLAMA_MODEL,
                "message": [{"role": "user", "content": prompt}],
                "stream": False
            })
            
            reply = response.json().get("message", {}).get("content", "").strip()

            if reply:
                # If LLM returned second part, separate it
                split_point = chunk_text.find(reply)

                if split_point != -1:
                    first_part = chunk_text[:split_point].strip()
                    second_part = reply.strip()

                    final_chunks.append(first_part)

                    # Get remaining words from second_part and re-use them in next batch
                    leftover_words = second_part.split()
                    words = leftover_words + words[i + WORD_LIMIT:]
                    
                    i = 0  # restart loop with leftover + remaining
                    continue
                else:
                    # fallback: if split point not found
                    final_chunks.append(chunk_text)
            else:
                final_chunks.append(chunk_text)    
        except Exception as e:
            logger.error(f"Semantic chunking LLM error: {e}", exc_info=True)
            final_chunks.append(chunk_text)

        i += WORD_LIMIT

    return final_chunks
#==============
import faiss
from src.server.rag_server.common.config.rag_config import METADATA_FILE, INDEX_FILE, CACHE_FILE 

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
        logger.info(f"SAVE, Successfully saved FAISS index and metadata")

def extract_title_from_content(content, file_name):
    """Try to extract a title from markdown content or fallback to file name"""
    # Look for markdown heading at the start
    title_match = re.search(r'^#\s+(.*?)$', content, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    
    # Try first line if it seems like a title (shorter than 100 chars)
    first_line = content.strip().split('\n')[0]
    if len(first_line) < 100 and not first_line.startswith('#'):
        return first_line
    
    # Fallback to file name without extension
    return Path(file_name).stem

def determine_source_type(file_ext):
    """Map file extension to a canonical source type"""
    if file_ext == ".pdf":
        return "pdf"
    elif file_ext in [".html", ".htm"]:
        return "html"
    elif file_ext == ".url":
        return "webpage"
    elif file_ext == ".md":
        return "markdown"
    elif file_ext == ".txt":
        return "text"
    else:
        return "document"
# # Example usage:
if __name__ == "__main__":
    # # Test with a sample image
    # image_path = "test_image.jpg"  # Update this with your test image path
    # result = process_image_text(image_path)
    # print(f"Result: {result}")
    text_input = """ """

    print(semantic_merge(text_input))