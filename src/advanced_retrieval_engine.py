"""
Advanced Retrieval Engine for Hybrid Search
Implements multi-stage retrieval with context expansion

Features:
1. Multi-stage pipeline: Hybrid Search → Reranker → Context Expansion
2. Adaptive retrieval strategy based on query type
3. Smart fusion (RRF) for BM25 + Dense
4. Query-specific optimization
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    SparseVector,
    NamedSparseVector,
)

from src.embedding_engine import EmbeddingEngine
from src.bm25_indexer import BM25Indexer
from src.reranker import BGEReranker
from src.qdrant_hybrid_setup import (
    COLLECTION_DOCUMENTS_HYBRID,
    COLLECTION_CHUNKS_HYBRID,
)

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Enhanced retrieval result with context"""
    chunk_id: str
    text: str
    score: float
    rerank_score: Optional[float] = None
    
    # Metadata
    chunk_type: str = None
    section_title: Optional[str] = None
    hierarchy_level: int = None
    
    # Source tracking
    filename: str = None
    filepath: str = None
    relative_path: str = None
    document_id: str = None
    
    # Hierarchical context
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = None
    parent_text: Optional[str] = None
    children_texts: List[str] = None
    
    # Fusion metadata
    bm25_score: Optional[float] = None
    dense_score: Optional[float] = None
    fusion_method: str = None


@dataclass
class QueryAnalysis:
    """Query analysis for adaptive retrieval"""
    query_type: str  # 'document', 'section', 'chunk', 'mixed'
    target_level: int  # 0, 1, or 2
    is_complex: bool  # Multiple concepts
    keywords: List[str]
    estimated_answer_length: str  # 'short', 'medium', 'long'


class AdvancedRetrievalEngine:
    """
    Advanced Hybrid Retrieval Engine with Multi-Stage Pipeline
    
    Pipeline:
    1. Query Analysis (determine strategy)
    2. Hybrid Search (BM25 + Dense with RRF)
    3. Reranking (Cross-encoder refinement)
    4. Context Expansion (Hierarchical enrichment)
    5. Post-processing (Deduplication, formatting)
    """
    
    def __init__(
        self,
        qdrant_client: QdrantClient,
        embedding_engine: EmbeddingEngine,
        bm25_indexer: BM25Indexer,
        reranker: BGEReranker,
        vocabulary: Dict[str, int],
    ):
        """Initialize Advanced Retrieval Engine"""
        self.client = qdrant_client
        self.embedding_engine = embedding_engine
        self.bm25_indexer = bm25_indexer
        self.reranker = reranker
        self.vocabulary = vocabulary
        
        logger.info("✅ Advanced Retrieval Engine initialized")
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze query to determine optimal retrieval strategy
        
        Args:
            query: User query
            
        Returns:
            QueryAnalysis with recommended strategy
        """
        query_lower = query.lower()
        
        # Detect query type based on keywords
        document_keywords = ['คืออะไร', 'ทำไง', 'ขั้นตอน', 'วิธีการ', 'กระบวนการ']
        section_keywords = ['ค่าธรรมเนียม', 'เอกสาร', 'หลักฐาน', 'คุณสมบัติ']
        chunk_keywords = ['เท่าไหร่', 'กี่', 'ใช้อะไร', 'ต้องมี']
        
        # Determine query type
        if any(kw in query_lower for kw in document_keywords):
            query_type = 'document'
            target_level = 0
        elif any(kw in query_lower for kw in section_keywords):
            query_type = 'section'
            target_level = 1
        elif any(kw in query_lower for kw in chunk_keywords):
            query_type = 'chunk'
            target_level = 2
        else:
            query_type = 'mixed'
            target_level = 2  # Default to chunk level
        
        # Detect complexity
        is_complex = len(query.split()) > 10 or 'และ' in query or 'หรือ' in query
        
        # Extract keywords (simple tokenization)
        keywords = self.bm25_indexer.tokenize(query)
        
        # Estimate answer length
        if any(kw in query_lower for kw in ['เท่าไหร่', 'กี่', 'ใช่หรือไม่']):
            estimated_length = 'short'
        elif any(kw in query_lower for kw in ['คืออะไร', 'อธิบาย']):
            estimated_length = 'long'
        else:
            estimated_length = 'medium'
        
        analysis = QueryAnalysis(
            query_type=query_type,
            target_level=target_level,
            is_complex=is_complex,
            keywords=keywords,
            estimated_answer_length=estimated_length,
        )
        
        logger.info(f"📊 Query Analysis: type={query_type}, level={target_level}, complex={is_complex}")
        return analysis
    
    def _reciprocal_rank_fusion(
        self,
        bm25_results: List[Tuple[str, float]],
        dense_results: List[Tuple[str, float]],
        k: int = 60,
        alpha: float = 0.5,
    ) -> List[Tuple[str, float]]:
        """
        Reciprocal Rank Fusion (RRF) for combining BM25 and Dense results
        
        RRF Score = alpha * (1/(k + rank_bm25)) + (1-alpha) * (1/(k + rank_dense))
        
        Args:
            bm25_results: List of (id, score) from BM25
            dense_results: List of (id, score) from Dense
            k: Constant for RRF (default: 60)
            alpha: Weight for BM25 (0.5 = balanced, >0.5 = favor BM25)
            
        Returns:
            Fused results sorted by RRF score
        """
        # Build rank maps
        bm25_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(bm25_results)}
        dense_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(dense_results)}
        
        # Get all unique document IDs
        all_doc_ids = set(bm25_ranks.keys()) | set(dense_ranks.keys())
        
        # Calculate RRF scores
        rrf_scores = {}
        for doc_id in all_doc_ids:
            bm25_rank = bm25_ranks.get(doc_id, len(bm25_results) + k)
            dense_rank = dense_ranks.get(doc_id, len(dense_results) + k)
            
            rrf_score = (
                alpha * (1 / (k + bm25_rank)) +
                (1 - alpha) * (1 / (k + dense_rank))
            )
            rrf_scores[doc_id] = rrf_score
        
        # Sort by RRF score
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        logger.info(f"🔀 RRF Fusion: {len(bm25_results)} BM25 + {len(dense_results)} Dense → {len(sorted_results)} unique")
        return sorted_results
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = 20,
        alpha: float = 0.5,
        target_level: Optional[int] = None,
        collection_name: str = COLLECTION_CHUNKS_HYBRID,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search with RRF fusion
        
        Args:
            query: Search query
            top_k: Number of results to return
            alpha: Weight for BM25 vs Dense (0.5 = balanced)
            target_level: Filter by hierarchy level (0, 1, or 2)
            collection_name: Qdrant collection to search
            
        Returns:
            List of search results with scores
        """
        logger.info(f"🔍 Hybrid Search: query='{query[:50]}...', top_k={top_k}, alpha={alpha}")
        
        # Build filter for target level
        query_filter = None
        if target_level is not None:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="hierarchy_level",
                        match=MatchValue(value=target_level),
                    )
                ]
            )
        
        # 1. Dense search (semantic)
        query_embedding = self.embedding_engine.encode_queries([query])[0]
        
        dense_results = self.client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            using="dense",
            query_filter=query_filter,
            limit=top_k * 2,  # Get more candidates for fusion
            with_payload=True,
        ).points
        
        # 2. Sparse search (BM25)
        sparse_vector_dict = self.bm25_indexer.get_sparse_vector(query, self.vocabulary)
        sparse_vector = SparseVector(
            indices=sparse_vector_dict["indices"],
            values=sparse_vector_dict["values"],
        )
        
        sparse_results = self.client.query_points(
            collection_name=collection_name,
            query=sparse_vector,
            using="sparse",
            query_filter=query_filter,
            limit=top_k * 2,
            with_payload=True,
        ).points
        
        # 3. Prepare results for RRF
        dense_candidates = [(str(r.id), r.score) for r in dense_results]
        sparse_candidates = [(str(r.id), r.score) for r in sparse_results]
        
        # 4. Apply RRF fusion
        fused_results = self._reciprocal_rank_fusion(
            sparse_candidates,
            dense_candidates,
            alpha=alpha,
        )[:top_k]
        
        # 5. Fetch full payloads for fused results
        result_ids = [doc_id for doc_id, _ in fused_results]
        score_map = {doc_id: score for doc_id, score in fused_results}
        
        # Create lookup maps for original scores
        dense_score_map = {str(r.id): r.score for r in dense_results}
        sparse_score_map = {str(r.id): r.score for r in sparse_results}
        
        # Retrieve points
        points = self.client.retrieve(
            collection_name=collection_name,
            ids=result_ids,
            with_payload=True,
        )
        
        # Build final results
        final_results = []
        for point in points:
            point_id = str(point.id)
            payload = point.payload
            
            final_results.append({
                'id': point_id,
                'text': payload.get('text', ''),
                'score': score_map[point_id],
                'bm25_score': sparse_score_map.get(point_id),
                'dense_score': dense_score_map.get(point_id),
                'fusion_method': 'RRF',
                'payload': payload,
            })
        
        # Sort by score (should already be sorted, but ensure)
        final_results.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"✅ Retrieved {len(final_results)} results")
        return final_results
    
    def rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Rerank results using cross-encoder
        
        Args:
            query: Original query
            results: Results from hybrid search
            top_k: Number of top results to return after reranking
            
        Returns:
            Reranked results
        """
        if not results:
            return []
        
        logger.info(f"🎯 Reranking {len(results)} results...")
        
        # Extract texts
        texts = [r['text'] for r in results]
        
        # Rerank
        reranked_results = self.reranker.rerank(
            query=query,
            documents=texts,
            top_k=top_k,
        )
        
        # Map back to original results and add rerank scores
        reranked_final = []
        for rerank_item in reranked_results:
            original_result = results[rerank_item['index']]
            original_result['rerank_score'] = rerank_item['score']
            original_result['rerank_index'] = rerank_item['index']
            reranked_final.append(original_result)
        
        logger.info(f"✅ Reranked to top {len(reranked_final)} results")
        return reranked_final
    
    def expand_context(
        self,
        results: List[Dict[str, Any]],
        include_parent: bool = True,
        include_children: bool = True,
        include_siblings: bool = False,
    ) -> List[RetrievalResult]:
        """
        Expand context by fetching parent, children, and siblings
        
        Args:
            results: Search results with payloads
            include_parent: Include parent chunk text
            include_children: Include children chunks texts
            include_siblings: Include sibling chunks texts
            
        Returns:
            Enhanced results with context
        """
        logger.info(f"🔗 Expanding context for {len(results)} results...")
        
        enhanced_results = []
        
        for result in results:
            payload = result['payload']
            
            # Extract hierarchical IDs
            parent_id = payload.get('parent_chunk_id')
            child_ids = payload.get('child_chunk_ids', [])
            
            # Fetch parent
            parent_text = None
            if include_parent and parent_id:
                try:
                    parent_points = self.client.retrieve(
                        collection_name=COLLECTION_CHUNKS_HYBRID,
                        ids=[parent_id],
                        with_payload=True,
                    )
                    if parent_points:
                        parent_text = parent_points[0].payload.get('text', '')
                except Exception as e:
                    logger.warning(f"Could not fetch parent {parent_id}: {e}")
            
            # Fetch children
            children_texts = []
            if include_children and child_ids:
                try:
                    children_points = self.client.retrieve(
                        collection_name=COLLECTION_CHUNKS_HYBRID,
                        ids=child_ids,
                        with_payload=True,
                    )
                    children_texts = [p.payload.get('text', '') for p in children_points]
                except Exception as e:
                    logger.warning(f"Could not fetch children: {e}")
            
            # Build enhanced result
            enhanced = RetrievalResult(
                chunk_id=result['id'],
                text=result['text'],
                score=result['score'],
                rerank_score=result.get('rerank_score'),
                chunk_type=payload.get('chunk_type'),
                section_title=payload.get('section_title'),
                hierarchy_level=payload.get('hierarchy_level'),
                filename=payload.get('file_name'),
                filepath=payload.get('file_path'),
                relative_path=payload.get('relative_path'),
                document_id=payload.get('document_id'),
                parent_chunk_id=parent_id,
                child_chunk_ids=child_ids,
                parent_text=parent_text,
                children_texts=children_texts,
                bm25_score=result.get('bm25_score'),
                dense_score=result.get('dense_score'),
                fusion_method=result.get('fusion_method'),
            )
            
            enhanced_results.append(enhanced)
        
        logger.info(f"✅ Context expanded for {len(enhanced_results)} results")
        return enhanced_results
    
    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        enable_reranker: bool = True,
        enable_context_expansion: bool = True,
        alpha: float = 0.5,
        adaptive: bool = True,
    ) -> List[RetrievalResult]:
        """
        Complete multi-stage retrieval pipeline
        
        Args:
            query: User query
            top_k: Number of final results
            enable_reranker: Use reranker for Stage 2
            enable_context_expansion: Add hierarchical context in Stage 3
            alpha: BM25 vs Dense weight (0.5 = balanced)
            adaptive: Use query analysis for strategy selection
            
        Returns:
            Final retrieval results with context
        """
        logger.info("=" * 80)
        logger.info("🚀 STARTING MULTI-STAGE RETRIEVAL")
        logger.info("=" * 80)
        logger.info(f"Query: {query}")
        logger.info(f"Config: top_k={top_k}, reranker={enable_reranker}, "
                   f"context={enable_context_expansion}, alpha={alpha}, adaptive={adaptive}")
        
        # Stage 0: Query Analysis (if adaptive)
        target_level = None
        query_analysis = None
        if adaptive:
            query_analysis = self.analyze_query(query)
            target_level = query_analysis.target_level
            logger.info(f"📊 Adaptive mode: targeting level {target_level}")
            # Store for external access
            self.last_query_analysis = query_analysis
        else:
            self.last_query_analysis = None
        
        # Stage 1: Hybrid Search with RRF
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 1: HYBRID SEARCH (BM25 + Dense + RRF)")
        logger.info("=" * 80)
        
        search_top_k = top_k * 3 if enable_reranker else top_k
        results = self.hybrid_search(
            query=query,
            top_k=search_top_k,
            alpha=alpha,
            target_level=target_level,
        )
        
        # Stage 2: Reranking (optional)
        if enable_reranker and results:
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 2: RERANKING (Cross-Encoder)")
            logger.info("=" * 80)
            
            results = self.rerank_results(
                query=query,
                results=results,
                top_k=top_k,
            )
        
        # Stage 3: Context Expansion (optional)
        if enable_context_expansion:
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 3: CONTEXT EXPANSION (Hierarchical)")
            logger.info("=" * 80)
            
            results = self.expand_context(
                results=results,
                include_parent=True,
                include_children=True,
            )
        else:
            # Convert to RetrievalResult format
            results = [
                RetrievalResult(
                    chunk_id=r['id'],
                    text=r['text'],
                    score=r['score'],
                    rerank_score=r.get('rerank_score'),
                    chunk_type=r['payload'].get('chunk_type'),
                    section_title=r['payload'].get('section_title'),
                    hierarchy_level=r['payload'].get('hierarchy_level'),
                    filename=r['payload'].get('file_name'),
                    filepath=r['payload'].get('file_path'),
                    relative_path=r['payload'].get('relative_path'),
                    document_id=r['payload'].get('document_id'),
                    parent_chunk_id=r['payload'].get('parent_chunk_id'),
                    child_chunk_ids=r['payload'].get('child_chunk_ids'),
                    parent_text=None,
                    children_texts=None,
                    bm25_score=r.get('bm25_score'),
                    dense_score=r.get('dense_score'),
                    fusion_method=r.get('fusion_method'),
                )
                for r in results
            ]
        
        logger.info("\n" + "=" * 80)
        logger.info(f"✅ RETRIEVAL COMPLETE: {len(results)} results")
        logger.info("=" * 80)
        
        return results
    
    def format_results(
        self,
        results: List[RetrievalResult],
        include_scores: bool = True,
        include_context: bool = True,
    ) -> str:
        """
        Format results for display
        
        Args:
            results: Retrieval results
            include_scores: Show scores
            include_context: Show parent/children context
            
        Returns:
            Formatted string
        """
        output = []
        output.append("=" * 80)
        output.append(f"📊 RETRIEVAL RESULTS ({len(results)} items)")
        output.append("=" * 80)
        
        for i, result in enumerate(results, 1):
            output.append(f"\n{'='*80}")
            output.append(f"Result #{i}")
            output.append(f"{'='*80}")
            
            # Source info
            output.append(f"📄 Source: {result.filename or 'Unknown'}")
            if result.section_title:
                output.append(f"📑 Section: {result.section_title}")
            output.append(f"🏷️  Type: {result.chunk_type} (Level {result.hierarchy_level})")
            
            # Scores
            if include_scores:
                output.append(f"\n📊 Scores:")
                if result.rerank_score is not None:
                    output.append(f"   Rerank: {result.rerank_score:.4f}")
                output.append(f"   Final: {result.score:.4f}")
                if result.bm25_score:
                    output.append(f"   BM25: {result.bm25_score:.4f}")
                if result.dense_score:
                    output.append(f"   Dense: {result.dense_score:.4f}")
            
            # Main text
            output.append(f"\n📝 Content:")
            output.append(f"{result.text[:500]}...")
            
            # Context
            if include_context:
                if result.parent_text:
                    output.append(f"\n⬆️  Parent Context:")
                    output.append(f"{result.parent_text[:300]}...")
                
                if result.children_texts:
                    output.append(f"\n⬇️  Children ({len(result.children_texts)}):")
                    for j, child_text in enumerate(result.children_texts[:2], 1):
                        output.append(f"   {j}. {child_text[:200]}...")
        
        output.append("\n" + "=" * 80)
        return "\n".join(output)
