"""
Qdrant Hybrid Collections Setup (Dense + Sparse Vectors)
Supports BM25 (sparse) + BGE-M3 (dense) hybrid search
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
    PayloadSchemaType,
)
import logging

from config.settings import (
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_API_KEY,
    EMBEDDING_DIMENSIONS,
)

logger = logging.getLogger(__name__)

# Hybrid collection names
COLLECTION_DOCUMENTS_HYBRID = "land_documents_hybrid"
COLLECTION_CHUNKS_HYBRID = "land_chunks_hybrid"


class QdrantHybridManager:
    """
    Manage Qdrant collections with hybrid search support.
    
    Uses named vectors:
    - "dense": BGE-M3 embeddings (1024 dims)
    - "sparse": BM25 sparse vectors
    """
    
    def __init__(self):
        """Initialize Qdrant client"""
        self.client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            api_key=QDRANT_API_KEY,
            https=False,
            timeout=30,
        )
        logger.info(f"Connected to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
    
    def create_hybrid_documents_collection(self):
        """
        Create hybrid collection for document-level vectors.
        
        Uses named vectors:
        - dense: BGE-M3 (1024 dims, COSINE)
        - sparse: BM25 (variable dims, DOT product)
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            if any(c.name == COLLECTION_DOCUMENTS_HYBRID for c in collections):
                logger.info(f"Collection {COLLECTION_DOCUMENTS_HYBRID} already exists")
                return
            
            # Create collection with named vectors
            self.client.create_collection(
                collection_name=COLLECTION_DOCUMENTS_HYBRID,
                vectors_config={
                    # Dense vector (BGE-M3)
                    "dense": VectorParams(
                        size=EMBEDDING_DIMENSIONS,
                        distance=Distance.COSINE,
                    ),
                },
                sparse_vectors_config={
                    # Sparse vector (BM25)
                    "sparse": SparseVectorParams(
                        index=SparseIndexParams(
                            on_disk=False,  # Keep in memory for speed
                        )
                    ),
                },
            )
            
            # Create payload indexes
            payload_indexes = {
                "document_type": PayloadSchemaType.KEYWORD,
                "metadata.version_info.version": PayloadSchemaType.KEYWORD,
                "metadata.categories.level1": PayloadSchemaType.KEYWORD,
                "metadata.categories.level2": PayloadSchemaType.KEYWORD,
                "metadata.categories.service_category": PayloadSchemaType.KEYWORD,
                "metadata.service.processing.standard.time_minutes": PayloadSchemaType.INTEGER,
                "metadata.service.requirements.requires_announcement": PayloadSchemaType.BOOL,
                "metadata.content_features.has_e_qlands": PayloadSchemaType.BOOL,
                "metadata.status.active": PayloadSchemaType.BOOL,
                "metadata.status.is_latest": PayloadSchemaType.BOOL,
            }
            
            for field, schema_type in payload_indexes.items():
                try:
                    self.client.create_payload_index(
                        collection_name=COLLECTION_DOCUMENTS_HYBRID,
                        field_name=field,
                        field_schema=schema_type,
                    )
                except Exception as e:
                    logger.warning(f"Could not create index on {field}: {e}")
            
            logger.info(f"✅ Created hybrid collection: {COLLECTION_DOCUMENTS_HYBRID}")
            
        except Exception as e:
            logger.error(f"Error creating hybrid documents collection: {e}")
            raise
    
    def create_hybrid_chunks_collection(self):
        """
        Create hybrid collection for chunk-level vectors.
        
        Uses named vectors:
        - dense: BGE-M3 (1024 dims, COSINE)
        - sparse: BM25 (variable dims, DOT product)
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            if any(c.name == COLLECTION_CHUNKS_HYBRID for c in collections):
                logger.info(f"Collection {COLLECTION_CHUNKS_HYBRID} already exists")
                return
            
            # Create collection with named vectors
            self.client.create_collection(
                collection_name=COLLECTION_CHUNKS_HYBRID,
                vectors_config={
                    # Dense vector (BGE-M3)
                    "dense": VectorParams(
                        size=EMBEDDING_DIMENSIONS,
                        distance=Distance.COSINE,
                    ),
                },
                sparse_vectors_config={
                    # Sparse vector (BM25)
                    "sparse": SparseVectorParams(
                        index=SparseIndexParams(
                            on_disk=False,
                        )
                    ),
                },
            )
            
            # Create payload indexes
            payload_indexes = {
                "parent_document_id": PayloadSchemaType.KEYWORD,
                "parent_chunk_id": PayloadSchemaType.KEYWORD,
                "hierarchy_level": PayloadSchemaType.INTEGER,
                "chunk_type": PayloadSchemaType.KEYWORD,
                "document_info.document_type": PayloadSchemaType.KEYWORD,
                "document_info.category_level1": PayloadSchemaType.KEYWORD,
                "context.section_title": PayloadSchemaType.TEXT,
                "importance.score": PayloadSchemaType.FLOAT,
                "importance.is_key_information": PayloadSchemaType.BOOL,
                "importance.is_requirement": PayloadSchemaType.BOOL,
                "importance.is_cost_info": PayloadSchemaType.BOOL,
                "content_analysis.has_table": PayloadSchemaType.BOOL,
                "content_analysis.has_list": PayloadSchemaType.BOOL,
                "content_analysis.has_legal_ref": PayloadSchemaType.BOOL,
            }
            
            for field, schema_type in payload_indexes.items():
                try:
                    self.client.create_payload_index(
                        collection_name=COLLECTION_CHUNKS_HYBRID,
                        field_name=field,
                        field_schema=schema_type,
                    )
                except Exception as e:
                    logger.warning(f"Could not create index on {field}: {e}")
            
            logger.info(f"✅ Created hybrid collection: {COLLECTION_CHUNKS_HYBRID}")
            
        except Exception as e:
            logger.error(f"Error creating hybrid chunks collection: {e}")
            raise
    
    def setup_hybrid_collections(self):
        """Setup all hybrid collections"""
        logger.info("Setting up Qdrant hybrid collections...")
        self.create_hybrid_documents_collection()
        self.create_hybrid_chunks_collection()
        logger.info("✅ All hybrid collections setup complete")
    
    def get_collection_info(self, collection_name: str):
        """Get information about a collection"""
        try:
            info = self.client.get_collection(collection_name)
            return info
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return None
    
    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if Qdrant is healthy"""
        try:
            collections = self.client.get_collections()
            logger.info(f"Qdrant health check OK. Collections: {len(collections.collections)}")
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
    
    def migrate_to_hybrid(self, source_collection: str, target_collection: str):
        """
        Migrate existing collection to hybrid collection.
        
        Note: This requires re-generating BM25 sparse vectors.
        Better to use the ETL pipeline to regenerate everything.
        """
        logger.warning("Migration requires re-running ETL pipeline with BM25 generation")
        logger.info(f"Please use hybrid_etl_pipeline.py to regenerate {target_collection}")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize and setup
    manager = QdrantHybridManager()
    
    # Health check
    if manager.health_check():
        # Setup hybrid collections
        manager.setup_hybrid_collections()
        
        # Show collection info
        for collection_name in [COLLECTION_DOCUMENTS_HYBRID, COLLECTION_CHUNKS_HYBRID]:
            info = manager.get_collection_info(collection_name)
            if info:
                print(f"\n📊 Collection: {collection_name}")
                print(f"   Vectors: {info.vectors_count if hasattr(info, 'vectors_count') else 'N/A'}")
                print(f"   Points: {info.points_count}")
                print(f"   Status: {info.status}")
                
                # Show vector configs
                if hasattr(info, 'config'):
                    print(f"   Vector configs:")
                    if hasattr(info.config, 'params'):
                        if hasattr(info.config.params, 'vectors'):
                            print(f"     - dense: {info.config.params.vectors}")
                        if hasattr(info.config.params, 'sparse_vectors'):
                            print(f"     - sparse: enabled")
