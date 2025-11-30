"""
Vector database adapter supporting Chroma (local) and Pinecone (cloud).

Provides unified interface: upsert, query, delete.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)

# Try importing vector DB clients
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available. Install with: pip install chromadb")

try:
    import pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logger.warning("Pinecone not available. Install with: pip install pinecone-client")


class VectorDBAdapter:
    """Unified interface for vector database operations."""
    
    def __init__(self):
        self.provider = os.getenv("VECTOR_DB", "chroma").lower()
        self.client = None
        self.collection_name = "smart_hiring_embeddings"
        
        if self.provider == "chroma":
            self._init_chroma()
        elif self.provider == "pinecone":
            self._init_pinecone()
        else:
            logger.warning(f"Unknown vector DB provider: {self.provider}. Using Chroma.")
            self._init_chroma()
    
    def _init_chroma(self):
        """Initialize ChromaDB client."""
        if not CHROMA_AVAILABLE:
            logger.error("ChromaDB not available. Install with: pip install chromadb")
            self.client = None
            return
        
        try:
            chroma_dir = os.getenv("CHROMA_DIR", "./chroma")
            os.makedirs(chroma_dir, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=chroma_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            
            logger.info(f"Initialized ChromaDB at {chroma_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None
    
    def _init_pinecone(self):
        """Initialize Pinecone client."""
        if not PINECONE_AVAILABLE:
            logger.error("Pinecone not available. Install with: pip install pinecone-client")
            self.client = None
            return
        
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            logger.error("PINECONE_API_KEY not found. Falling back to Chroma.")
            self._init_chroma()
            return
        
        try:
            pinecone.init(api_key=api_key, environment=os.getenv("PINECONE_ENV", "us-east1-gcp"))
            index_name = os.getenv("PINECONE_INDEX_NAME", "smart-hiring")
            
            # Create index if it doesn't exist
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine"
                )
            
            self.client = pinecone.Index(index_name)
            logger.info(f"Initialized Pinecone index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            self.client = None
    
    def upsert(
        self,
        id: str,
        vector: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Upsert a vector with metadata.
        
        Args:
            id: Unique identifier
            vector: Embedding vector
            metadata: Metadata dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Vector DB client not initialized")
            return False
        
        try:
            if self.provider == "chroma":
                # Chroma expects list of ids, embeddings, and metadatas
                self.collection.upsert(
                    ids=[id],
                    embeddings=[vector],
                    metadatas=[metadata]
                )
            elif self.provider == "pinecone":
                # Pinecone expects list of tuples: (id, vector, metadata)
                self.client.upsert([(id, vector, metadata)])
            
            logger.debug(f"Upserted vector with id: {id}")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert vector: {e}")
            return False
    
    def query(
        self,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query similar vectors.
        
        Args:
            vector: Query embedding vector
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of results with id, score, and metadata
        """
        if not self.client:
            logger.error("Vector DB client not initialized")
            return []
        
        try:
            if self.provider == "chroma":
                where = filter if filter else None
                results = self.collection.query(
                    query_embeddings=[vector],
                    n_results=top_k,
                    where=where
                )
                
                # Format results
                formatted_results = []
                if results['ids'] and len(results['ids'][0]) > 0:
                    for i in range(len(results['ids'][0])):
                        formatted_results.append({
                            'id': results['ids'][0][i],
                            'score': 1 - results['distances'][0][i],  # Convert distance to similarity
                            'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                        })
                
                return formatted_results
            
            elif self.provider == "pinecone":
                results = self.client.query(
                    vector=vector,
                    top_k=top_k,
                    include_metadata=True,
                    filter=filter
                )
                
                # Format results
                formatted_results = []
                for match in results.matches:
                    formatted_results.append({
                        'id': match.id,
                        'score': match.score,
                        'metadata': match.metadata or {}
                    })
                
                return formatted_results
        
        except Exception as e:
            logger.error(f"Failed to query vectors: {e}")
            return []
    
    def delete(self, id: str) -> bool:
        """
        Delete a vector by id.
        
        Args:
            id: Vector identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Vector DB client not initialized")
            return False
        
        try:
            if self.provider == "chroma":
                self.collection.delete(ids=[id])
            elif self.provider == "pinecone":
                self.client.delete(ids=[id])
            
            logger.debug(f"Deleted vector with id: {id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete vector: {e}")
            return False
    
    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Get a vector by id.
        
        Args:
            id: Vector identifier
            
        Returns:
            Vector data with metadata, or None if not found
        """
        if not self.client:
            return None
        
        try:
            if self.provider == "chroma":
                results = self.collection.get(ids=[id], include=['embeddings', 'metadatas'])
                if results['ids']:
                    return {
                        'id': results['ids'][0],
                        'metadata': results['metadatas'][0] if results['metadatas'] else {}
                    }
            elif self.provider == "pinecone":
                results = self.client.fetch(ids=[id])
                if id in results.vectors:
                    vec_data = results.vectors[id]
                    return {
                        'id': id,
                        'metadata': vec_data.metadata or {}
                    }
        except Exception as e:
            logger.error(f"Failed to get vector by id: {e}")
        
        return None


# Global instance
_vector_db: Optional[VectorDBAdapter] = None


def get_vector_db() -> VectorDBAdapter:
    """Get or create the global vector DB instance."""
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDBAdapter()
    return _vector_db

