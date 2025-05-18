import numpy as np
import faiss
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import os
import json
import logging
import pickle

# For embeddings - choose one approach based on your setup
# Option 1: Local model through ollama
import requests
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[4]  # This gets /Users/ravi/EAG-TheShadowCloneAI/S8

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))


from src.common.logger.logger import get_logger
logger = get_logger()


class MemoryItem(BaseModel):
    text: str
    type: Literal["preferences", "tool_output", "fact", "query", "system"] = "fact"
    timestamp: Optional[str] = None
    tool_name: Optional[str] = None
    user_query: Optional[str] = None
    tags: List[str] = []
    session_id: Optional[str] = None
    
    def __init__(self, **data):
        if "timestamp" not in data or data["timestamp"] is None:
            data["timestamp"] = datetime.now().isoformat()
        super().__init__(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "type": self.type,
            "timestamp": self.timestamp,
            "tool_name": self.tool_name,
            "user_query": self.user_query,
            "tags": self.tags,
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        return cls(**data)


class MemoryManager:
    def __init__(self, 
                 embedding_model_url="http://localhost:11434/api/embeddings",
                 model_name="nomic-embed-text",
                 collection_name="agent_memory",
                 dimension=768,  # Default dimension for embeddings
                 save_path=ROOT / "resources" / "memory_store"):
        """
        Initialize the MemoryManager with Faiss vector database
        
        Args:
            embedding_model_url: URL for the embedding model API (if using Ollama)
            model_name: Name of the embedding model to use
            collection_name: Name of the collection/index
            dimension: Dimension of embeddings
            save_path: Directory to save the Faiss index and metadata
        """
        self.embedding_model_url = embedding_model_url
        self.model_name = model_name
        self.collection_name = collection_name
        self.dimension = dimension
        self.save_path = Path(save_path)
        
        # Create save directory if it doesn't exist
        self.save_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Faiss index and metadata store
        self._initialize_index()
        
        # For sentence-transformers (alternative embedding approach)
        # self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def _initialize_index(self):
        """Initialize or load the Faiss index and metadata"""
        index_path = self.save_path / f"{self.collection_name}_index.faiss"
        metadata_path = self.save_path / f"{self.collection_name}_metadata.pkl"
        
        if index_path.exists() and metadata_path.exists():
            # Load existing index and metadata
            try:
                self.index = faiss.read_index(str(index_path))
                with open(metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                logger.info(f"Loaded existing index with {self.index.ntotal} entries")
            except Exception as e:
                logger.error(f"Error loading index: {str(e)}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new Faiss index and metadata store"""
        # Create a flat L2 index - you can use other index types for better performance
        self.index = faiss.IndexFlatL2(self.dimension)
        # Alternative: IVF index for better scaling with large collections
        # quantizer = faiss.IndexFlatL2(self.dimension)
        # self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)  # 100 centroids
        # self.index.train(np.random.random((1000, self.dimension)).astype('float32'))
        
        # Metadata will store our MemoryItems by ID
        self.metadata = {}
        logger.info(f"Created new Faiss index for {self.collection_name}")
    
    def _save_index(self):
        """Save the index and metadata to disk"""
        try:
            index_path = self.save_path / f"{self.collection_name}_index.faiss"
            metadata_path = self.save_path / f"{self.collection_name}_metadata.pkl"
            
            faiss.write_index(self.index, str(index_path))
            with open(metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            logger.info(f"Saved index with {self.index.ntotal} entries")
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding vector for text using the embedding model"""
        try:
            # Option 1: Using Ollama or similar API service
            response = requests.post(
                self.embedding_model_url,
                json={"model": self.model_name, "prompt": text}
            )
            response.raise_for_status()
            embedding = np.array(response.json()["embedding"], dtype=np.float32)
            
            # Option 2: Using sentence-transformers
            # embedding = self.model.encode([text])[0].astype(np.float32)
            
            # Make sure it's the right shape
            if embedding.shape[0] != self.dimension:
                logger.warning(f"Embedding dimension mismatch. Expected {self.dimension}, got {embedding.shape[0]}")
                self.dimension = embedding.shape[0]
                # Reinitialize index if dimension changed
                if self.index.ntotal == 0:
                    self._create_new_index()
                else:
                    logger.error("Cannot change dimension of non-empty index")
                    return np.zeros(self.dimension, dtype=np.float32)
            
            return embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            # Return empty embedding if failed
            return np.zeros(self.dimension, dtype=np.float32)
    
    def retrieve(
            self,
            query: str,
            top_k: int = 3,
            type_filter: Optional[str] = None,
            tag_filter: Optional[List[str]] = None,
            session_filter: Optional[str] = None
    ) -> List[MemoryItem]:
        """
        Retrieve relevant memories from vector database
        
        Args:
            query: Search query text
            top_k: Number of results to return
            type_filter: Filter by memory type
            tag_filter: Filter by tags
            session_filter: Filter by session ID
            
        Returns:
            List of MemoryItem objects
        """
        if self.index.ntotal == 0:
            return []
            
        try:
            # Get embedding for query
            query_vector = self._get_embedding(query)
            
            # Convert to the format Faiss expects
            query_vector = query_vector.reshape(1, -1)
            
            # Perform search - get more results than needed to allow for filtering
            search_k = min(top_k * 5, self.index.ntotal)  # Get more to allow for filtering
            distances, indices = self.index.search(query_vector, search_k)
            
            # Flatten results
            indices = indices[0]
            distances = distances[0]
            
            # Filter and convert results
            memory_items = []
            for idx, distance in zip(indices, distances):
                if idx < 0:  # Faiss returns -1 for padded results
                    continue
                    
                # Get memory item from metadata
                item_id = str(idx)
                if item_id not in self.metadata:
                    logger.warning(f"Index {idx} not found in metadata")
                    continue
                    
                item_data = self.metadata[item_id]
                
                # Apply filters
                if type_filter and item_data.get("type") != type_filter:
                    continue
                    
                if tag_filter:
                    item_tags = set(item_data.get("tags", []))
                    if not any(tag in item_tags for tag in tag_filter):
                        continue
                        
                if session_filter and item_data.get("session_id") != session_filter:
                    continue
                
                # Create memory item
                try:
                    memory_item = MemoryItem.from_dict(item_data)
                    memory_items.append(memory_item)
                    
                    if len(memory_items) >= top_k:
                        break
                except Exception as e:
                    logger.error(f"Error processing memory result: {str(e)}")
                    continue
                    
            return memory_items
            
        except Exception as e:
            logger.error(f"Error retrieving from Faiss: {str(e)}")
            return []
    
    def add(self, item: MemoryItem):
        """
        Add a memory item to the vector database
        
        Args:
            item: MemoryItem to add
        """
        try:
            # Get embedding for text
            vector = self._get_embedding(item.text)
            
            # Add to Faiss index
            vector = vector.reshape(1, -1)  # Reshape to 2D for Faiss
            
            # Get the current index size as the ID
            item_id = str(self.index.ntotal)
            
            # Add to index
            self.index.add(vector)
            
            # Store metadata
            self.metadata[item_id] = item.to_dict()
            
            # Save index periodically (can be optimized to save less frequently)
            self._save_index()
            
            logger.info(f"Added memory item to Faiss: {item.text[:30]}...")
            
        except Exception as e:
            logger.error(f"Error adding to Faiss: {str(e)}")
    
    def bulk_add(self, items: List[MemoryItem]):
        """
        Add multiple memory items in bulk
        
        Args:
            items: List of MemoryItem objects to add
        """
        if not items:
            return
            
        try:
            # Prepare vectors and metadata
            vectors = []
            
            for item in items:
                vector = self._get_embedding(item.text)
                vectors.append(vector)
            
            # Convert to numpy array
            vectors_array = np.array(vectors, dtype=np.float32)
            
            # Get starting item ID
            start_id = self.index.ntotal
            
            # Add to index
            self.index.add(vectors_array)
            
            # Store metadata
            for i, item in enumerate(items):
                item_id = str(start_id + i)
                self.metadata[item_id] = item.to_dict()
            
            # Save index
            self._save_index()
            
            logger.info(f"Bulk added {len(items)} memory items to Faiss")
            
        except Exception as e:
            logger.error(f"Error bulk adding to Faiss: {str(e)}")
            # Fallback to individual adds if bulk fails
            for item in items:
                try:
                    self.add(item)
                except Exception as e2:
                    logger.error(f"Error in fallback add: {str(e2)}")

    def delete_by_session(self, session_id: str):
        """
        Delete all memory items for a specific session
        
        Args:
            session_id: Session ID to delete
            
        Note: Faiss doesn't support direct deletion. We need to rebuild the index.
        """
        try:
            # Find items to keep (not matching session_id)
            items_to_keep = []
            new_metadata = {}
            
            for item_id, item_data in self.metadata.items():
                if item_data.get("session_id") != session_id:
                    items_to_keep.append(MemoryItem.from_dict(item_data))
            
            # Count how many items we're removing
            removed_count = len(self.metadata) - len(items_to_keep)
            
            if removed_count > 0:
                # Create a new index
                self._create_new_index()
                
                # Re-add all items to keep
                self.bulk_add(items_to_keep)
                
                logger.info(f"Deleted {removed_count} memory items for session {session_id}")
            else:
                logger.info(f"No items found for session {session_id}")
                
        except Exception as e:
            logger.error(f"Error deleting session memories: {str(e)}")