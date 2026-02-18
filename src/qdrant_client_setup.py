"""
Qdrant Client and Schema Setup
"""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    PayloadSchemaType,
)
from typing import Optional
import logging

from config.settings import (
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_API_KEY,
    COLLECTION_DOCUMENTS,
    COLLECTION_CHUNKS,
    EMBEDDING_DIMENSIONS,
)

logger = logging.getLogger(__name__)


class QdrantManager:
    """Manage Qdrant collections and operations"""
    
    def __init__(self):
        """Initialize Qdrant client"""
        self.client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            api_key=QDRANT_API_KEY,
            https=False,  # Use HTTP not HTTPS for local
            timeout=30,
        )
        logger.info(f"Connected to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
    
    def create_documents_collection(self):
        """
        Create collection for document-level vectors
        
        Schema based on schema_design_v2_comprehensive.md
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            if any(c.name == COLLECTION_DOCUMENTS for c in collections):
                logger.info(f"Collection {COLLECTION_DOCUMENTS} already exists")
                return
            
            # Create collection
            self.client.create_collection(
                collection_name=COLLECTION_DOCUMENTS,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSIONS,
                    distance=Distance.COSINE,
                ),
            )
            
            # Create payload indexes for filtering
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
                        collection_name=COLLECTION_DOCUMENTS,
                        field_name=field,
                        field_schema=schema_type,
                    )
                    logger.info(f"Created index on {field}")
                except Exception as e:
                    logger.warning(f"Could not create index on {field}: {e}")
            
            logger.info(f"✅ Created collection: {COLLECTION_DOCUMENTS}")
            
        except Exception as e:
            logger.error(f"Error creating documents collection: {e}")
            raise
    
    def create_chunks_collection(self):
        """
        Create collection for chunk-level vectors
        
        Schema based on schema_design_v2_comprehensive.md
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            if any(c.name == COLLECTION_CHUNKS for c in collections):
                logger.info(f"Collection {COLLECTION_CHUNKS} already exists")
                return
            
            # Create collection
            self.client.create_collection(
                collection_name=COLLECTION_CHUNKS,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSIONS,
                    distance=Distance.COSINE,
                ),
            )
            
            # Create payload indexes
            payload_indexes = {
                "parent_document_id": PayloadSchemaType.KEYWORD,
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
                        collection_name=COLLECTION_CHUNKS,
                        field_name=field,
                        field_schema=schema_type,
                    )
                    logger.info(f"Created index on {field}")
                except Exception as e:
                    logger.warning(f"Could not create index on {field}: {e}")
            
            logger.info(f"✅ Created collection: {COLLECTION_CHUNKS}")
            
        except Exception as e:
            logger.error(f"Error creating chunks collection: {e}")
            raise
    
    def setup_collections(self):
        """Setup all collections"""
        logger.info("Setting up Qdrant collections...")
        self.create_documents_collection()
        self.create_chunks_collection()
        logger.info("✅ All collections setup complete")
    
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


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize and setup
    manager = QdrantManager()
    
    # Health check
    if manager.health_check():
        # Setup collections
        manager.setup_collections()
        
        # Show collection info
        for collection_name in [COLLECTION_DOCUMENTS, COLLECTION_CHUNKS]:
            info = manager.get_collection_info(collection_name)
            if info:
                print(f"\n📊 Collection: {collection_name}")
                print(f"   Vectors: {info.vectors_count}")
                print(f"   Points: {info.points_count}")
                print(f"   Status: {info.status}")
