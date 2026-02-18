"""
Complete ETL Pipeline for Land Department Documents

Features:
- Load documents from disk
- Extract comprehensive metadata
- Hierarchical chunking with parent-child relationships
- BGE-Multilingual-Gemma2 embeddings (3584 dims)
- Upload to Qdrant with full schema
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from tqdm import tqdm
import uuid
import time

from src.metadata_extractor import MetadataExtractor
from src.chunking_engine import ChunkingEngine, Chunk
from src.embedding_engine import EmbeddingEngine
from src.qdrant_client_setup import QdrantManager
from config.settings import (
    DATA_DIR,
    COLLECTION_DOCUMENTS,
    COLLECTION_CHUNKS,
)
from qdrant_client.models import PointStruct

logger = logging.getLogger(__name__)


class ETLPipeline:
    """
    Complete ETL Pipeline with hierarchical chunking
    
    Pipeline:
    1. Load documents
    2. Extract metadata
    3. Chunk with hierarchy (document → section → subsection)
    4. Generate embeddings
    5. Upload to Qdrant
    """
    
    def __init__(
        self,
        data_dir: Path = DATA_DIR,
        device: str = "cpu",
    ):
        """Initialize ETL pipeline"""
        self.data_dir = Path(data_dir)
        
        logger.info("Initializing ETL Pipeline...")
        
        # Initialize components
        self.metadata_extractor = MetadataExtractor()
        self.chunking_engine = ChunkingEngine()
        self.embedding_engine = EmbeddingEngine(device=device)
        self.qdrant_manager = QdrantManager()
        
        logger.info("✅ ETL Pipeline initialized")
    
    def _cleanup_text(self, text: str) -> str:
        """
        Clean up text to remove encoding issues and normalize
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        import re
        
        # Replace common encoding errors
        replacements = {
            '�': '',  # Remove replacement character
            '\x00': '',  # Remove null bytes
            '\r\n': '\n',  # Normalize line endings
            '\r': '\n',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove excessive whitespace but preserve paragraph breaks
        text = re.sub(r'\n\n\n+', '\n\n', text)  # Max 2 newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def load_documents(
        self,
        pattern: str = "**/*.txt",
        limit: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Load documents from data directory
        
        Args:
            pattern: Glob pattern for file matching
            limit: Maximum number of documents to load
            
        Returns:
            List of document dictionaries
        """
        logger.info(f"Loading documents from {self.data_dir}")
        
        files = list(self.data_dir.glob(pattern))
        
        if limit:
            files = files[:limit]
        
        logger.info(f"Found {len(files)} files")
        
        documents = []
        for file_path in files:
            try:
                # Try UTF-8 first, fallback to other encodings
                text = None
                encodings = ['utf-8', 'utf-8-sig', 'cp874', 'iso-8859-11']
                
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                            text = f.read()
                        break
                    except:
                        continue
                
                if text is None:
                    logger.error(f"Could not decode {file_path}")
                    continue
                
                # Clean up text
                text = self._cleanup_text(text)
                
                documents.append({
                    'file_path': str(file_path),
                    'filepath': str(file_path.absolute()),
                    'relative_path': str(file_path.relative_to(self.data_dir)),
                    'text': text,
                    'file_name': file_path.name,
                })
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        logger.info(f"✅ Loaded {len(documents)} documents")
        return documents
    
    def process_document(
        self,
        document: Dict[str, Any],
        document_id: str,
    ) -> Dict[str, Any]:
        """
        Process a single document through the pipeline
        
        Args:
            document: Document dictionary
            document_id: Unique document ID
            
        Returns:
            Processed document with metadata and chunks
        """
        start_time = time.time()
        text = document['text']
        file_path = document['file_path']
        
        # Step 1: Extract metadata
        metadata_start = time.time()
        logger.debug(f"Extracting metadata for {document_id}")
        metadata = self.metadata_extractor.extract_metadata(text, file_path)
        metadata_time = time.time() - metadata_start
        
        # Step 2: Chunk document with hierarchy
        chunk_start = time.time()
        logger.debug(f"Chunking document {document_id}")
        chunks = self.chunking_engine.chunk_document(
            text=text,
            document_type=metadata['document_type'],
            document_id=document_id,
        )
        chunk_time = time.time() - chunk_start
        
        # Step 3: Generate embeddings (batch process for efficiency)
        embed_start = time.time()
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        chunk_texts = [chunk.text for chunk in chunks]
        
        # Process in batches
        batch_size = 8  # Reasonable batch for bge-m3 on CPU
        embeddings = []
        
        for i in range(0, len(chunk_texts), batch_size):
            batch = chunk_texts[i:i + batch_size]
            batch_embeddings = self.embedding_engine.encode(
                batch,
                show_progress_bar=False,
            )
            embeddings.extend(batch_embeddings)
            logger.debug(f"  Embedded batch {i//batch_size + 1}/{(len(chunk_texts)-1)//batch_size + 1}")
        
        embed_time = time.time() - embed_start
        
        # Attach embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.metadata['embedding'] = embedding
        
        total_time = time.time() - start_time
        
        logger.info(f"⏱️  {document_id}: metadata={metadata_time:.1f}s, chunk={chunk_time:.1f}s, embed={embed_time:.1f}s, total={total_time:.1f}s")
        
        return {
            'document_id': document_id,
            'metadata': metadata,
            'chunks': chunks,
            'file_path': file_path,
            'processing_time': {
                'metadata': metadata_time,
                'chunking': chunk_time,
                'embedding': embed_time,
                'total': total_time,
            }
        }
    
    def upload_to_qdrant(
        self,
        processed_documents: List[Dict[str, Any]],
    ):
        """
        Upload processed documents to Qdrant
        
        Args:
            processed_documents: List of processed documents
        """
        upload_start = time.time()
        logger.info("Uploading to Qdrant...")
        
        # Prepare points for documents collection
        prepare_start = time.time()
        document_points = []
        chunk_points = []
        
        for doc in tqdm(processed_documents, desc="Preparing points"):
            doc_id = doc['document_id']
            metadata = doc['metadata']
            chunks = doc['chunks']
            
            # Get document-level chunk (hierarchy_level=0)
            doc_chunk = next((c for c in chunks if c.hierarchy_level == 0), None)
            
            if doc_chunk:
                # Document-level point
                doc_point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=doc_chunk.metadata['embedding'],
                    payload={
                        'document_id': doc_id,
                        'document_type': metadata['document_type'],
                        'title': metadata['title'],
                        'file_path': doc['file_path'],
                        'filepath': doc.get('filepath', doc['file_path']),
                        'relative_path': doc.get('relative_path', doc['file_path']),
                        'file_name': doc.get('file_name', Path(doc['file_path']).name),
                        'metadata': {
                            'file_info': metadata['file_info'],
                            'version_info': metadata['version_info'],
                            'categories': metadata['categories'],
                            'service': metadata['service'],
                            'legal_references': metadata['legal_references'],
                            'fees': metadata['fees'],
                            'required_documents': metadata['required_documents'],
                            'content_features': metadata['content_features'],
                            'search_optimization': metadata['search_optimization'],
                        },
                        'text': doc_chunk.text,
                        'created_at': datetime.now().isoformat(),
                    }
                )
                document_points.append(doc_point)
            
            # Chunk-level points
            for chunk in chunks:
                chunk_id = chunk.metadata.get('chunk_id', str(uuid.uuid4()))
                
                chunk_point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=chunk.metadata['embedding'],
                    payload={
                        'chunk_id': chunk_id,
                        'parent_document_id': doc_id,
                        'chunk_type': chunk.chunk_type,
                        'chunk_index': chunk.chunk_index,
                        'text': chunk.text,
                        'text_length': len(chunk.text),
                        'language': 'th',
                        
                        # Position
                        'position': {
                            'start_line': chunk.start_line,
                            'end_line': chunk.end_line,
                        },
                        
                        # Context
                        'context': {
                            'section_title': chunk.section_title,
                        },
                        
                        # Hierarchy (PageIndex-style)
                        'parent_chunk_id': chunk.parent_chunk_id,
                        'child_chunk_ids': chunk.child_chunk_ids,
                        'hierarchy_level': chunk.hierarchy_level,
                        
                        # Document info (inherited)
                        'document_info': {
                            'document_type': metadata['document_type'],
                            'category_level1': metadata['categories'].get('level1'),
                            'title': metadata['title'],
                            'file_name': doc.get('file_name', Path(doc['file_path']).name),
                            'filepath': doc.get('filepath', doc['file_path']),
                            'relative_path': doc.get('relative_path', doc['file_path']),
                        },
                        
                        # Importance
                        'importance': {
                            'score': chunk.importance_score,
                            'is_key_information': chunk.importance_score >= 0.9,
                        },
                        
                        # Timestamps
                        'created_at': datetime.now().isoformat(),
                    }
                )
                chunk_points.append(chunk_point)
        
        prepare_time = time.time() - prepare_start
        logger.info(f"⏱️  Prepared points in {prepare_time:.1f}s")
        
        # Upload to Qdrant
        doc_upload_start = time.time()
        logger.info(f"Uploading {len(document_points)} document points...")
        if document_points:
            self.qdrant_manager.client.upsert(
                collection_name=COLLECTION_DOCUMENTS,
                points=document_points,
            )
        doc_upload_time = time.time() - doc_upload_start
        
        chunk_upload_start = time.time()
        logger.info(f"Uploading {len(chunk_points)} chunk points...")
        if chunk_points:
            # Upload in batches
            batch_size = 100
            for i in range(0, len(chunk_points), batch_size):
                batch = chunk_points[i:i + batch_size]
                self.qdrant_manager.client.upsert(
                    collection_name=COLLECTION_CHUNKS,
                    points=batch,
                )
                logger.info(f"  Uploaded batch {i//batch_size + 1}/{(len(chunk_points)-1)//batch_size + 1}")
        
        chunk_upload_time = time.time() - chunk_upload_start
        total_upload_time = time.time() - upload_start
        
        logger.info(f"⏱️  Upload time: docs={doc_upload_time:.1f}s, chunks={chunk_upload_time:.1f}s, total={total_upload_time:.1f}s")
        logger.info("✅ Upload complete!")
    
    def run(
        self,
        pattern: str = "**/*.txt",
        limit: int = None,
    ):
        """
        Run complete ETL pipeline
        
        Args:
            pattern: Glob pattern for file matching
            limit: Maximum number of documents to process
        """
        pipeline_start = time.time()
        
        logger.info("=" * 60)
        logger.info("Starting ETL Pipeline")
        logger.info("=" * 60)
        
        # Step 1: Load documents
        load_start = time.time()
        documents = self.load_documents(pattern, limit)
        load_time = time.time() - load_start
        
        if not documents:
            logger.warning("No documents found!")
            return
        
        logger.info(f"⏱️  Loaded {len(documents)} documents in {load_time:.1f}s")
        
        # Step 2: Process documents
        process_start = time.time()
        logger.info(f"\nProcessing {len(documents)} documents...")
        processed_documents = []
        
        for i, doc in enumerate(tqdm(documents, desc="Processing"), 1):
            try:
                doc_id = f"doc_{i:04d}"
                processed_doc = self.process_document(doc, doc_id)
                processed_documents.append(processed_doc)
            except Exception as e:
                logger.error(f"Error processing document {i}: {e}")
                import traceback
                traceback.print_exc()
        
        process_time = time.time() - process_start
        logger.info(f"✅ Processed {len(processed_documents)} documents in {process_time:.1f}s")
        
        # Step 3: Upload to Qdrant
        self.upload_to_qdrant(processed_documents)
        
        # Step 4: Summary
        total_chunks = sum(len(doc['chunks']) for doc in processed_documents)
        pipeline_time = time.time() - pipeline_start
        
        # Calculate timing breakdown
        avg_times = {
            'metadata': sum(d['processing_time']['metadata'] for d in processed_documents) / len(processed_documents),
            'chunking': sum(d['processing_time']['chunking'] for d in processed_documents) / len(processed_documents),
            'embedding': sum(d['processing_time']['embedding'] for d in processed_documents) / len(processed_documents),
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("ETL Pipeline Complete!")
        logger.info("=" * 60)
        logger.info(f"📄 Documents processed: {len(processed_documents)}")
        logger.info(f"📦 Total chunks created: {total_chunks}")
        logger.info(f"📊 Average chunks per doc: {total_chunks / len(processed_documents):.1f}")
        logger.info(f"🗄️  Uploaded to Qdrant: {COLLECTION_DOCUMENTS} & {COLLECTION_CHUNKS}")
        logger.info("")
        logger.info("⏱️  Timing Breakdown:")
        logger.info(f"   Load:      {load_time:.1f}s")
        logger.info(f"   Process:   {process_time:.1f}s ({process_time/len(processed_documents):.1f}s per doc)")
        logger.info(f"     - Metadata:  {avg_times['metadata']:.1f}s avg")
        logger.info(f"     - Chunking:  {avg_times['chunking']:.1f}s avg")
        logger.info(f"     - Embedding: {avg_times['embedding']:.1f}s avg")
        logger.info(f"   Total:     {pipeline_time:.1f}s ({pipeline_time/60:.1f} minutes)")
        logger.info("=" * 60)


def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize pipeline
    pipeline = ETLPipeline(device="cpu")
    
    # Run with all documents
    pipeline.run(
        pattern="**/*.txt",  # รันทุก .txt file ในทุก folder
        limit=None,  # ไม่จำกัด รันทั้งหมด
    )


if __name__ == "__main__":
    main()
