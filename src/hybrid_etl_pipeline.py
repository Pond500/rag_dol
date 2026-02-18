"""
Hybrid ETL Pipeline for Land Department Documents
Generates both dense (BGE-M3) and sparse (BM25) vectors

Features:
- Load documents from disk
- Extract comprehensive metadata
- Hierarchical chunking with parent-child relationships  
- BGE-M3 embeddings (1024 dims) - Dense
- BM25 sparse vectors - Sparse
- Upload to Qdrant hybrid collections
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from tqdm import tqdm
import uuid
import time
import json
import pickle

from src.metadata_extractor import MetadataExtractor
from src.chunking_engine import ChunkingEngine, Chunk
from src.embedding_engine import EmbeddingEngine
from src.bm25_indexer import BM25Indexer
from src.qdrant_hybrid_setup import (
    QdrantHybridManager,
    COLLECTION_DOCUMENTS_HYBRID,
    COLLECTION_CHUNKS_HYBRID,
)
from config.settings import DATA_DIR
from qdrant_client.models import PointStruct, NamedVector, NamedSparseVector, SparseVector

logger = logging.getLogger(__name__)


class HybridETLPipeline:
    """
    Complete ETL Pipeline with Hybrid Search Support
    
    Pipeline:
    1. Load documents
    2. Extract metadata
    3. Chunk with hierarchy
    4. Generate dense embeddings (BGE-M3)
    5. Build BM25 vocabulary and sparse vectors
    6. Upload to Qdrant hybrid collections
    """
    
    def __init__(
        self,
        data_dir: Path = DATA_DIR,
        device: str = "cpu",
        vocabulary_save_path: str = "data/bm25_vocabulary.pkl",
    ):
        """Initialize Hybrid ETL pipeline"""
        self.data_dir = Path(data_dir)
        self.vocabulary_save_path = vocabulary_save_path
        
        logger.info("=" * 80)
        logger.info("Initializing Hybrid ETL Pipeline")
        logger.info("=" * 80)
        
        # Initialize components
        logger.info("Loading Metadata Extractor...")
        self.metadata_extractor = MetadataExtractor()
        
        logger.info("Loading Chunking Engine...")
        self.chunking_engine = ChunkingEngine()
        
        logger.info("Loading BGE-M3 Embedding Engine...")
        self.embedding_engine = EmbeddingEngine(device=device)
        
        logger.info("Loading BM25 Indexer...")
        self.bm25_indexer = BM25Indexer()
        
        logger.info("Connecting to Qdrant...")
        self.qdrant_manager = QdrantHybridManager()
        
        # Vocabulary for BM25
        self.vocabulary = None
        
        logger.info("✅ Hybrid ETL Pipeline initialized")
        logger.info("=" * 80)
    
    def _cleanup_text(self, text: str) -> str:
        """Clean up text to remove encoding issues"""
        import re
        
        replacements = {
            '�': '',
            '\x00': '',
            '\r\n': '\n',
            '\r': '\n',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        text = re.sub(r'\n\n\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def load_documents(
        self,
        folder_name: str = "คู่มือปชช.รายละเอียดเนื้อหา",
        limit: int = None,
        load_all: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Load documents from folder(s)
        
        Args:
            folder_name: Specific folder to load from (if load_all=False)
            limit: Maximum number of documents to load
            load_all: If True, load all .txt files from all folders recursively
        """
        if load_all:
            # Load all .txt files from entire data directory
            logger.info(f"Loading ALL documents from {self.data_dir} (recursive)")
            txt_files = list(self.data_dir.glob("**/*.txt"))
        else:
            # Load from specific folder only
            folder_path = self.data_dir / folder_name
            
            if not folder_path.exists():
                raise FileNotFoundError(f"Folder not found: {folder_path}")
            
            txt_files = list(folder_path.glob("*.txt"))
            logger.info(f"Loading documents from {folder_name}")
        
        if limit:
            txt_files = txt_files[:limit]
        
        logger.info(f"Found {len(txt_files)} documents")
        
        documents = []
        for file_path in txt_files:
            # Try multiple encodings
            text = None
            for encoding in ['utf-8', 'utf-8-sig', 'cp874', 'iso-8859-11']:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                        text = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if text is None:
                logger.warning(f"Could not read {file_path.name}")
                continue
            
            # Clean text
            text = self._cleanup_text(text)
            
            documents.append({
                "id": str(uuid.uuid4()),
                "filename": file_path.name,
                "filepath": str(file_path.absolute()),
                "relative_path": str(file_path.relative_to(self.data_dir)),
                "text": text,
                "document_type": folder_name,
            })
        
        logger.info(f"✅ Loaded {len(documents)} documents")
        return documents
    
    def load_all_documents(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Load documents from ALL folders in data directory recursively.
        
        Args:
            limit: Maximum total documents to load (across all folders)
            
        Returns:
            List of document dictionaries from all folders
        """
        logger.info(f"🔍 Scanning ALL folders in {self.data_dir}")
        
        # Find all .txt files recursively
        txt_files = list(self.data_dir.rglob("*.txt"))
        
        logger.info(f"📊 Found {len(txt_files)} total .txt files across all folders")
        
        if limit:
            txt_files = txt_files[:limit]
            logger.info(f"⚠️  Limited to {limit} files")
        
        documents = []
        for file_path in txt_files:
            # Try multiple encodings
            text = None
            for encoding in ['utf-8', 'utf-8-sig', 'cp874', 'iso-8859-11']:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                        text = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if text is None:
                logger.warning(f"Could not read {file_path.name}")
                continue
            
            # Clean text
            text = self._cleanup_text(text)
            
            # Get folder name as document type
            relative_path = file_path.relative_to(self.data_dir)
            folder_name = str(relative_path.parent)
            
            documents.append({
                "id": str(uuid.uuid4()),
                "filename": file_path.name,
                "filepath": str(file_path.absolute()),
                "relative_path": str(relative_path),
                "text": text,
                "document_type": folder_name,
            })
        
        logger.info(f"✅ Loaded {len(documents)} documents from all folders")
        return documents
    
    def build_bm25_vocabulary(self, chunks: List[Chunk]) -> Dict[str, int]:
        """
        Build BM25 vocabulary from all chunks.
        This must be done before generating sparse vectors.
        
        Args:
            chunks: All chunks from all documents
            
        Returns:
            Vocabulary mapping (term -> index)
        """
        logger.info("Building BM25 vocabulary from corpus...")
        
        # Extract all texts
        texts = [chunk.text for chunk in chunks]
        
        # Build vocabulary
        vocabulary = self.bm25_indexer.build_vocabulary(texts)
        
        # Fit BM25 on corpus
        self.bm25_indexer.fit(texts)
        
        # Save vocabulary
        vocab_path = Path(self.vocabulary_save_path)
        vocab_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(vocab_path, 'wb') as f:
            pickle.dump({
                'vocabulary': vocabulary,
                'idf_scores': self.bm25_indexer.idf_scores,
                'avg_doc_length': self.bm25_indexer.avg_doc_length,
                'doc_count': self.bm25_indexer.doc_count,
            }, f)
        
        logger.info(f"✅ Built vocabulary with {len(vocabulary)} terms")
        logger.info(f"💾 Saved to {vocab_path}")
        
        self.vocabulary = vocabulary
        return vocabulary
    
    def process_batch(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 4,
    ) -> Tuple[List[Dict[str, Any]], List[Chunk]]:
        """
        Process batch of documents through full pipeline.
        
        Returns:
            Tuple of (doc_records, chunk_records)
        """
        doc_records = []
        all_chunks = []
        
        # Track timing
        total_start = time.time()
        
        for doc in tqdm(documents, desc="Processing documents"):
            doc_start = time.time()
            
            # 1. Extract metadata
            metadata = self.metadata_extractor.extract_metadata(
                text=doc["text"],
                file_path=doc["filename"],
            )
            
            # 2. Chunk document with hierarchy
            chunks = self.chunking_engine.chunk_document(
                text=doc["text"],
                document_type=doc["document_type"],
                document_id=doc["id"],
            )
            
            all_chunks.extend(chunks)
            
            # Create document record
            doc_record = {
                "id": doc["id"],
                "filename": doc["filename"],
                "filepath": doc["filepath"],
                "relative_path": doc["relative_path"],
                "document_type": doc["document_type"],
                "metadata": metadata,
                "chunk_count": len(chunks),
            }
            doc_records.append(doc_record)
            
            doc_time = time.time() - doc_start
            logger.info(
                f"  ✓ {doc['filename'][:50]}: "
                f"{len(chunks)} chunks in {doc_time:.1f}s"
            )
        
        total_time = time.time() - total_start
        avg_time = total_time / len(documents) if documents else 0
        
        logger.info(f"\n📊 Batch Summary:")
        logger.info(f"   Documents: {len(documents)}")
        logger.info(f"   Total chunks: {len(all_chunks)}")
        logger.info(f"   Total time: {total_time/60:.1f} minutes")
        logger.info(f"   Avg per doc: {avg_time:.1f}s")
        
        return doc_records, all_chunks
    
    def generate_embeddings_batch(
        self,
        chunks: List[Chunk],
        batch_size: int = 16,
    ) -> List[List[float]]:
        """Generate dense embeddings (BGE-M3) for chunks"""
        logger.info(f"Generating dense embeddings for {len(chunks)} chunks...")
        
        texts = [chunk.text for chunk in chunks]
        embeddings = []
        
        for i in tqdm(range(0, len(texts), batch_size), desc="Embedding batches"):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.embedding_engine.encode_passages(batch)
            embeddings.extend(batch_embeddings)
        
        logger.info(f"✅ Generated {len(embeddings)} embeddings")
        return embeddings
    
    def generate_sparse_vectors_batch(
        self,
        chunks: List[Chunk],
    ) -> List[Dict[str, Any]]:
        """Generate sparse vectors (BM25) for chunks"""
        if self.vocabulary is None:
            raise ValueError("Vocabulary not built yet. Call build_bm25_vocabulary first.")
        
        logger.info(f"Generating BM25 sparse vectors for {len(chunks)} chunks...")
        
        sparse_vectors = []
        for chunk in tqdm(chunks, desc="BM25 vectors"):
            sparse_vec = self.bm25_indexer.get_sparse_vector(chunk.text, self.vocabulary)
            sparse_vectors.append(sparse_vec)
        
        logger.info(f"✅ Generated {len(sparse_vectors)} sparse vectors")
        return sparse_vectors
    
    def upload_to_qdrant(
        self,
        doc_records: List[Dict[str, Any]],
        chunks: List[Chunk],
        dense_embeddings: List[List[float]],
        sparse_vectors: List[Dict[str, Any]],
    ):
        """Upload documents and chunks to Qdrant hybrid collections"""
        logger.info("Uploading to Qdrant hybrid collections...")
        
        # Upload documents (just dense for now, can add sparse later)
        logger.info(f"Uploading {len(doc_records)} documents...")
        doc_points = []
        
        for doc_record in doc_records:
            # Generate embedding for document (use first chunk or summary)
            doc_embedding = self.embedding_engine.encode_passages([doc_record["metadata"].get("title", "Document")])
            
            point = PointStruct(
                id=doc_record["id"],
                vector={
                    "dense": doc_embedding[0],
                },
                payload={
                    "filename": doc_record["filename"],
                    "filepath": doc_record["filepath"],
                    "relative_path": doc_record["relative_path"],
                    "document_type": doc_record["document_type"],
                    "metadata": doc_record["metadata"],
                    "chunk_count": doc_record["chunk_count"],
                },
            )
            doc_points.append(point)
        
        self.qdrant_manager.client.upsert(
            collection_name=COLLECTION_DOCUMENTS_HYBRID,
            points=doc_points,
        )
        logger.info(f"✅ Uploaded {len(doc_points)} documents")
        
        # Upload chunks with both dense and sparse vectors
        logger.info(f"Uploading {len(chunks)} chunks...")
        chunk_points = []
        
        for chunk, dense_emb, sparse_vec in zip(chunks, dense_embeddings, sparse_vectors):
            # Get chunk ID from metadata or generate one
            chunk_id = chunk.metadata.get('chunk_id') if chunk.metadata else None
            if not chunk_id:
                chunk_id = str(uuid.uuid4())
            
            # Build combined vector dict with both dense and sparse
            # For named vectors: dense is list[float], sparse is SparseVector
            vectors = {
                "dense": dense_emb,
                "sparse": SparseVector(
                    indices=sparse_vec["indices"],
                    values=sparse_vec["values"],
                )
            }
            
            # Create point with both vectors
            point = PointStruct(
                id=chunk_id,
                vector=vectors,
                payload=chunk.to_payload(),
            )
            
            chunk_points.append(point)
        
        # Upload in batches
        batch_size = 100
        for i in tqdm(range(0, len(chunk_points), batch_size), desc="Uploading chunks"):
            batch = chunk_points[i:i + batch_size]
            self.qdrant_manager.client.upsert(
                collection_name=COLLECTION_CHUNKS_HYBRID,
                points=batch,
            )
        
        logger.info(f"✅ Uploaded {len(chunk_points)} chunks")
    
    def run(
        self,
        folder_name: str = "คู่มือปชช.รายละเอียดเนื้อหา",
        limit: int = None,
        load_all: bool = True,
    ):
        """
        Run complete hybrid ETL pipeline
        
        Args:
            folder_name: Specific folder (if load_all=False)
            limit: Limit number of documents
            load_all: Load all documents from all folders (default: True)
        """
        logger.info("\n" + "=" * 80)
        logger.info("STARTING HYBRID ETL PIPELINE")
        logger.info("=" * 80 + "\n")
        
        pipeline_start = time.time()
        
        try:
            # 1. Load documents
            if load_all:
                logger.info("📂 Loading from ALL folders...")
                documents = self.load_all_documents(limit)
            else:
                logger.info(f"📂 Loading from specific folder: {folder_name}")
                documents = self.load_documents(folder_name, limit)
            
            # 2. Process documents (metadata + chunking)
            doc_records, all_chunks = self.process_batch(documents)
            
            # 3. Build BM25 vocabulary
            self.build_bm25_vocabulary(all_chunks)
            
            # 4. Generate dense embeddings
            dense_embeddings = self.generate_embeddings_batch(all_chunks)
            
            # 5. Generate sparse vectors
            sparse_vectors = self.generate_sparse_vectors_batch(all_chunks)
            
            # 6. Upload to Qdrant
            self.upload_to_qdrant(doc_records, all_chunks, dense_embeddings, sparse_vectors)
            
            # Summary
            pipeline_time = time.time() - pipeline_start
            
            logger.info("\n" + "=" * 80)
            logger.info("HYBRID ETL PIPELINE COMPLETE")
            logger.info("=" * 80)
            logger.info(f"📊 Total documents: {len(documents)}")
            logger.info(f"📊 Total chunks: {len(all_chunks)}")
            logger.info(f"📊 Vocabulary size: {len(self.vocabulary)}")
            logger.info(f"⏱️  Total time: {pipeline_time/60:.1f} minutes")
            logger.info(f"⏱️  Avg per doc: {pipeline_time/len(documents):.1f}s")
            logger.info("=" * 80 + "\n")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run pipeline
    pipeline = HybridETLPipeline(device='cpu')
    
    # Process all documents from all folders
    print("\n🚀 Processing ALL documents from all folders...")
    print("This will take approximately 60-90 minutes")
    print()
    
    pipeline.run(
        load_all=True,  # Load from all folders
        limit=None,     # Process all 108 documents
    )
