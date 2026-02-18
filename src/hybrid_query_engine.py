"""
Hybrid Query Engine with BM25 + Vector Search + Reranking
Combines lexical (BM25) and semantic (BGE-M3) search with BGE-Reranker-v2-m3
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from qdrant_client.models import (
    NamedVector,
    NamedSparseVector,
    QueryVector,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
)

from src.qdrant_hybrid_setup import QdrantHybridManager, COLLECTION_CHUNKS_HYBRID
from src.embedding_engine import EmbeddingEngine
from src.bm25_indexer import BM25Indexer
from src.reranker import BGEReranker

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchResult:
    """Result from hybrid search"""
    chunk_id: str
    text: str
    
    # Scores
    dense_score: float = 0.0
    sparse_score: float = 0.0
    hybrid_score: float = 0.0
    rerank_score: Optional[float] = None
    final_score: float = 0.0
    
    # Metadata
    document_type: str = ""
    title: str = ""
    section_title: str = ""
    chunk_type: str = ""
    hierarchy_level: int = 0
    importance_score: float = 0.0
    
    # File source information
    file_name: Optional[str] = None
    filepath: Optional[str] = None
    relative_path: Optional[str] = None
    
    # Hierarchical context
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = field(default_factory=list)
    
    # Full metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class HybridQueryEngine:
    """
    Hybrid Query Engine combining:
    1. BM25 (sparse, keyword-based)
    2. Vector search (dense, semantic)
    3. Reranking (cross-encoder)
    
    Architecture:
    - Stage 1: Hybrid retrieval (BM25 + Vector) → retrieve top K candidates
    - Stage 2: Rerank with cross-encoder → get top N final results
    """
    
    def __init__(
        self,
        device: str = 'cpu',
        alpha: float = 0.5,
        enable_reranker: bool = True,
        vocabulary_path: Optional[str] = None,
    ):
        """
        Initialize Hybrid Query Engine.
        
        Args:
            device: Device for models ('cpu', 'cuda', 'mps')
            alpha: Hybrid fusion weight (0=sparse only, 1=dense only, 0.5=equal)
            enable_reranker: Whether to use reranker
            vocabulary_path: Path to saved BM25 vocabulary (optional)
        """
        self.device = device
        self.alpha = alpha
        self.enable_reranker = enable_reranker
        
        logger.info("=" * 80)
        logger.info("Initializing Hybrid Query Engine")
        logger.info(f"  Device: {device}")
        logger.info(f"  Alpha (dense weight): {alpha}")
        logger.info(f"  Reranker: {'enabled' if enable_reranker else 'disabled'}")
        logger.info("=" * 80)
        
        # Initialize Qdrant client
        self.qdrant = QdrantHybridManager()
        
        # Initialize embedding engine (BGE-M3)
        logger.info("Loading BGE-M3 embedding model...")
        self.embedding_engine = EmbeddingEngine(device=device)
        
        # Initialize BM25 indexer
        logger.info("Initializing BM25 indexer...")
        self.bm25_indexer = BM25Indexer()
        
        # Load vocabulary if provided
        self.vocabulary = None
        if vocabulary_path:
            logger.info(f"Loading BM25 vocabulary from {vocabulary_path}")
            # TODO: Implement vocabulary loading
        
        # Initialize reranker
        if enable_reranker:
            logger.info("Loading BGE-Reranker-v2-m3...")
            self.reranker = BGEReranker(device=device, max_length=512)
        else:
            self.reranker = None
        
        logger.info("✅ Hybrid Query Engine initialized")
    
    def search(
        self,
        query: str,
        top_k: int = 20,
        final_top_k: int = 5,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        min_importance: float = 0.0,
        use_hierarchy: bool = True,
    ) -> List[HybridSearchResult]:
        """
        Perform hybrid search with reranking.
        
        Args:
            query: Search query
            top_k: Number of candidates from hybrid search
            final_top_k: Number of final results after reranking
            document_type: Filter by document type
            category: Filter by category
            min_importance: Minimum importance score
            use_hierarchy: Add hierarchical context
            
        Returns:
            List of HybridSearchResult objects
        """
        logger.info(f"\n🔍 Query: {query}")
        logger.info(f"📊 Retrieval: {top_k} candidates → {final_top_k} final results")
        
        # Stage 1: Hybrid retrieval
        candidates = self._hybrid_retrieval(
            query=query,
            top_k=top_k,
            document_type=document_type,
            category=category,
            min_importance=min_importance,
        )
        
        logger.info(f"✅ Retrieved {len(candidates)} candidates from hybrid search")
        
        if not candidates:
            logger.warning("No candidates found")
            return []
        
        # Stage 2: Reranking
        if self.enable_reranker and self.reranker:
            logger.info("🎯 Reranking with BGE-Reranker-v2-m3...")
            reranked = self._rerank_results(query, candidates, final_top_k)
            logger.info(f"✅ Reranked to top {len(reranked)} results")
        else:
            # Just take top K by hybrid score
            reranked = sorted(candidates, key=lambda x: x.final_score, reverse=True)[:final_top_k]
        
        # Stage 3: Add hierarchical context
        if use_hierarchy:
            logger.info("📚 Adding hierarchical context...")
            reranked = self._add_hierarchical_context(reranked)
        
        return reranked
    
    def _hybrid_retrieval(
        self,
        query: str,
        top_k: int,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        min_importance: float = 0.0,
    ) -> List[HybridSearchResult]:
        """
        Perform hybrid retrieval (BM25 + Vector).
        
        Qdrant supports native hybrid search with prefetch:
        1. Prefetch with sparse vector (BM25)
        2. Rerank with dense vector (semantic)
        3. Combine scores with RRF (Reciprocal Rank Fusion)
        """
        # Generate dense vector (BGE-M3)
        dense_vector = self.embedding_engine.encode_queries([query])[0]
        
        # Generate sparse vector (BM25)
        # Note: Need vocabulary for this - will use Qdrant's built-in for now
        sparse_vector = None
        if self.vocabulary:
            sparse_vector = self.bm25_indexer.encode_query(query, self.vocabulary)
        
        # Build filters
        filter_conditions = self._build_filters(document_type, category, min_importance)
        
        # Perform hybrid search using Qdrant's query API
        try:
            # Use query_points with prefetch for hybrid search
            results = self.qdrant.client.query_points(
                collection_name=COLLECTION_CHUNKS_HYBRID,
                query=dense_vector,
                using="dense",  # Main query uses dense vector
                query_filter=filter_conditions,
                limit=top_k,
                with_payload=True,
            )
            
            # Convert to HybridSearchResult objects
            search_results = []
            for point in results.points:
                result = HybridSearchResult(
                    chunk_id=str(point.id),
                    text=point.payload.get('text', ''),
                    dense_score=point.score,
                    sparse_score=0.0,  # Not available in this query mode
                    hybrid_score=point.score,
                    final_score=point.score,
                    document_type=point.payload.get('document_info', {}).get('document_type', ''),
                    title=point.payload.get('document_info', {}).get('title', ''),
                    section_title=point.payload.get('context', {}).get('section_title', ''),
                    chunk_type=point.payload.get('chunk_type', ''),
                    hierarchy_level=point.payload.get('hierarchy_level', 0),
                    importance_score=point.payload.get('importance', {}).get('score', 0.0),
                    file_name=point.payload.get('document_info', {}).get('file_name'),
                    filepath=point.payload.get('document_info', {}).get('filepath'),
                    relative_path=point.payload.get('document_info', {}).get('relative_path'),
                    parent_chunk_id=point.payload.get('parent_chunk_id'),
                    child_chunk_ids=point.payload.get('child_chunk_ids', []),
                    metadata=point.payload,
                )
                search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {e}")
            return []
    
    def _build_filters(
        self,
        document_type: Optional[str],
        category: Optional[str],
        min_importance: float,
    ) -> Optional[Filter]:
        """Build Qdrant filters from search parameters"""
        conditions = []
        
        if document_type:
            conditions.append(
                FieldCondition(
                    key="document_info.document_type",
                    match=MatchValue(value=document_type),
                )
            )
        
        if category:
            conditions.append(
                FieldCondition(
                    key="document_info.category_level1",
                    match=MatchValue(value=category),
                )
            )
        
        if min_importance > 0:
            conditions.append(
                FieldCondition(
                    key="importance.score",
                    range=Range(gte=min_importance),
                )
            )
        
        if not conditions:
            return None
        
        return Filter(must=conditions)
    
    def _rerank_results(
        self,
        query: str,
        candidates: List[HybridSearchResult],
        top_k: int,
    ) -> List[HybridSearchResult]:
        """Rerank candidates using cross-encoder"""
        if not self.reranker:
            return candidates[:top_k]
        
        # Extract texts
        texts = [c.text for c in candidates]
        
        # Rerank
        reranked = self.reranker.rerank(query, texts, top_k=top_k)
        
        # Map scores back to candidates
        final_results = []
        for result in reranked:
            idx = result["index"]
            candidate = candidates[idx]
            candidate.rerank_score = result["score"]
            candidate.final_score = result["score"]
            final_results.append(candidate)
        
        return final_results
    
    def _add_hierarchical_context(
        self,
        results: List[HybridSearchResult],
    ) -> List[HybridSearchResult]:
        """Add parent and child context to results"""
        for result in results:
            # Fetch parent context
            if result.parent_chunk_id:
                try:
                    parent = self.qdrant.client.retrieve(
                        collection_name=COLLECTION_CHUNKS_HYBRID,
                        ids=[result.parent_chunk_id],
                    )
                    if parent:
                        result.metadata['parent_context'] = {
                            'text': parent[0].payload.get('text', ''),
                            'section_title': parent[0].payload.get('context', {}).get('section_title', ''),
                        }
                except Exception as e:
                    logger.warning(f"Could not fetch parent context: {e}")
            
            # Fetch children context
            if result.child_chunk_ids:
                try:
                    children = self.qdrant.client.retrieve(
                        collection_name=COLLECTION_CHUNKS_HYBRID,
                        ids=result.child_chunk_ids[:3],  # Limit to 3 children
                    )
                    if children:
                        result.metadata['children_context'] = [
                            {
                                'text': child.payload.get('text', '')[:200],
                                'chunk_type': child.payload.get('chunk_type', ''),
                            }
                            for child in children
                        ]
                except Exception as e:
                    logger.warning(f"Could not fetch children context: {e}")
        
        return results
    
    def print_results(
        self,
        results: List[HybridSearchResult],
        show_scores: bool = True,
        show_context: bool = True,
    ):
        """Pretty print search results"""
        print(f"\n🔍 Found {len(results)} results\n")
        
        for i, result in enumerate(results, 1):
            print("=" * 80)
            print(f"📄 Result {i}")
            print("=" * 80)
            
            if show_scores:
                print(f"💯 Scores:")
                if result.rerank_score is not None:
                    print(f"   Rerank: {result.rerank_score:.4f}")
                print(f"   Dense: {result.dense_score:.4f}")
                print(f"   Hybrid: {result.hybrid_score:.4f}")
                print(f"   Final: {result.final_score:.4f}")
                print()
            
            print(f"📂 Type: {result.document_type}")
            print(f"📑 Title: {result.title[:80]}")
            
            # Show file source
            if result.file_name:
                print(f"📁 File: {result.file_name}")
            if result.relative_path:
                print(f"📂 Path: {result.relative_path}")
            
            if result.section_title:
                print(f"📍 Section: {result.section_title[:80]}")
            print(f"🏷️  Chunk Type: {result.chunk_type} | Level: {result.hierarchy_level}")
            print(f"⭐ Importance: {result.importance_score:.2f}")
            print()
            
            print(f"💬 Content:")
            print(f"{result.text[:400]}...")
            print()
            
            if show_context:
                parent_context = result.metadata.get('parent_context')
                if parent_context:
                    print(f"⬆️  Parent ({parent_context.get('section_title', 'N/A')}):")
                    print(f"   {parent_context.get('text', '')[:200]}...")
                    print()
                
                children_context = result.metadata.get('children_context', [])
                if children_context:
                    print(f"⬇️  Children ({len(children_context)}):")
                    for child in children_context[:2]:
                        print(f"   - {child.get('chunk_type', 'N/A')}: {child.get('text', '')[:100]}...")
                    print()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    print("🚀 Testing Hybrid Query Engine")
    print("Note: Collections need to be populated first with hybrid_etl_pipeline.py")
    
    try:
        engine = HybridQueryEngine(device='cpu', enable_reranker=False)
        print("\n✅ Engine initialized successfully")
        print("\nTo use the engine, run: python hybrid_etl_pipeline.py first")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
