# Ollama v0.6.4+ uses the chat API only
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_MODEL = "gemma3:latest"  # Using latest tag as shown in available models
# GEMMA_MODEL = "gemma3:4b"  # "moondream" #"gemma3:12b"
PHI_MODEL = "phi3:latest"

EMBED_URL = f"{OLLAMA_BASE_URL}/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50



import os
from pathlib import Path

# Configuration
ROOT = Path(__file__).resolve().parents[5]
DOC_PATH = ROOT / "resources" / "documents"
INDEX_CACHE = ROOT / "resources" / "faiss_index"
INDEX_FILE = INDEX_CACHE / "index.bin"
METADATA_FILE = INDEX_CACHE / "metadata.json"
CACHE_FILE = INDEX_CACHE / "doc_index_cache.json"
GLOBAL_IMAGE_DIR = ROOT / "resources"/ "documents" / "images" / "pdf_images"
# Create necessary directories
DOC_PATH.mkdir(exist_ok=True, parents=True)
INDEX_CACHE.mkdir(exist_ok=True, parents=True)

# Embedding configuration
EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_MODEL = "llama3"

# Text chunking configuration
CHUNK_SIZE = 512  # Increased from 256
CHUNK_OVERLAP = 40

# Image processing configuration
MAX_IMAGE_SIZE = 1600
IMAGE_QUALITY = 85