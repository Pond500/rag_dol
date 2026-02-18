"""
Query Engine for Land Department Documents

Features:
- Vector search with BGE-M3
- Metadata filtering
- Hierarchical retrieval (parent → children)
- Hybrid search (dense + metadata)
- Re-ranking
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.qdrant_client_setup import QdrantManager
from src.embedding_engine import EmbeddingEngine
from config.settings import COLLECTION_DOCUMENTS, COLLECTION_CHUNKS
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with metadata"""
    chunk_id: str
    text: str
    score: float
    hierarchy_level: int
    document_type: str
    title: str
    section_title: Optional[str]
    chunk_type: str
    importance_score: float
    parent_chunk_id: Optional[str]
    child_chunk_ids: List[str]
    # File source information
    file_name: Optional[str] = None
    filepath: Optional[str] = None
    relative_path: Optional[str] = None
    metadata: Dict[str, Any] = None


class QueryEngine:
    """
    Query Engine with hierarchical retrieval
    
    Search Modes:
    1. Basic vector search
    2. Filtered search (by document type, category, etc.)
    3. Hierarchical search (get parents/children)
    4. Hybrid search (vector + metadata + importance)
    """
    
    def __init__(
        self,
        device: str = "cpu",
    ):
        """Initialize query engine"""
        logger.info("Initializing Query Engine...")
        
        self.qdrant = QdrantManager()
        self.embedder = EmbeddingEngine(device=device)
        
        logger.info("✅ Query Engine ready")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        min_importance: float = 0.0,
        use_hierarchy: bool = True,
    ) -> List[SearchResult]:
        """
        Search for relevant chunks
        
        Args:
            query: Search query
            top_k: Number of results
            document_type: Filter by document type
            category: Filter by category
            min_importance: Minimum importance score
            use_hierarchy: Include parent/child context
            
        Returns:
            List of search results
        """
        logger.info(f"Searching: '{query}'")
        
        # 1. Generate query embedding
        query_vector = self.embedder.encode([query])[0]
        
        # 2. Build filters
        filters = self._build_filters(
            document_type=document_type,
            category=category,
            min_importance=min_importance,
        )
        
        # 3. Vector search
        search_results = self.qdrant.client.query_points(
            collection_name=COLLECTION_CHUNKS,
            query=query_vector,
            limit=top_k * 2,  # Get more for re-ranking
            query_filter=filters,
            with_payload=True,
        ).points
        
        # 4. Convert to SearchResult objects
        results = []
        for result in search_results:
            payload = result.payload
            
            search_result = SearchResult(
                chunk_id=payload.get('chunk_id'),
                text=payload.get('text'),
                score=result.score,
                hierarchy_level=payload.get('hierarchy_level'),
                document_type=payload.get('document_info', {}).get('document_type'),
                title=payload.get('document_info', {}).get('title'),
                section_title=payload.get('context', {}).get('section_title'),
                chunk_type=payload.get('chunk_type'),
                importance_score=payload.get('importance', {}).get('score', 0.5),
                parent_chunk_id=payload.get('parent_chunk_id'),
                child_chunk_ids=payload.get('child_chunk_ids', []),
                file_name=payload.get('document_info', {}).get('file_name'),
                filepath=payload.get('document_info', {}).get('filepath'),
                relative_path=payload.get('document_info', {}).get('relative_path'),
                metadata=payload,
            )
            results.append(search_result)
        
        # 5. Re-rank by combined score
        results = self._rerank_results(results)
        
        # 6. Add hierarchical context if requested
        if use_hierarchy:
            results = self._add_hierarchical_context(results)
        
        # 7. Return top_k
        return results[:top_k]
    
    def _build_filters(
        self,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        min_importance: float = 0.0,
    ) -> Optional[Filter]:
        """Build Qdrant filters"""
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
        
        if conditions:
            return Filter(must=conditions)
        
        return None
    
    def _rerank_results(
        self,
        results: List[SearchResult],
    ) -> List[SearchResult]:
        """
        Re-rank results by combined score
        
        Combined score = vector_score * 0.7 + importance_score * 0.3
        """
        for result in results:
            combined_score = (
                result.score * 0.7 +
                result.importance_score * 0.3
            )
            result.score = combined_score
        
        # Sort by combined score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def _add_hierarchical_context(
        self,
        results: List[SearchResult],
    ) -> List[SearchResult]:
        """
        Add parent and children context to results
        
        For each result, fetch:
        - Parent chunk (if exists)
        - Children chunks (if exists)
        """
        enriched_results = []
        
        for result in results:
            # Get parent if exists
            if result.parent_chunk_id:
                parent = self._get_chunk_by_id(result.parent_chunk_id)
                if parent:
                    result.metadata['parent_context'] = {
                        'text': parent.get('text', '')[:200],  # First 200 chars
                        'chunk_type': parent.get('chunk_type'),
                        'section_title': parent.get('context', {}).get('section_title'),
                    }
            
            # Get children if exists
            if result.child_chunk_ids and len(result.child_chunk_ids) > 0:
                children = []
                for child_id in result.child_chunk_ids[:3]:  # Max 3 children
                    child = self._get_chunk_by_id(child_id)
                    if child:
                        children.append({
                            'chunk_id': child_id,
                            'text': child.get('text', '')[:200],
                            'chunk_type': child.get('chunk_type'),
                        })
                
                if children:
                    result.metadata['children_context'] = children
            
            enriched_results.append(result)
        
        return enriched_results
    
    def _get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get chunk by chunk_id"""
        try:
            results = self.qdrant.client.scroll(
                collection_name=COLLECTION_CHUNKS,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="chunk_id",
                            match=MatchValue(value=chunk_id),
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
            )[0]
            
            if results:
                return results[0].payload
        except Exception as e:
            logger.error(f"Error fetching chunk {chunk_id}: {e}")
        
        return None
    
    def search_by_category(
        self,
        query: str,
        category: str,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Search within specific category"""
        return self.search(
            query=query,
            top_k=top_k,
            category=category,
            use_hierarchy=True,
        )
    
    def search_by_document_type(
        self,
        query: str,
        document_type: str,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Search within specific document type"""
        return self.search(
            query=query,
            top_k=top_k,
            document_type=document_type,
            use_hierarchy=True,
        )
    
    def get_chunk_hierarchy(
        self,
        chunk_id: str,
    ) -> Dict[str, Any]:
        """
        Get full hierarchy for a chunk
        
        Returns:
            - Current chunk
            - All parents (level 0 → current)
            - All children (if any)
        """
        chunk = self._get_chunk_by_id(chunk_id)
        
        if not chunk:
            return {"error": "Chunk not found"}
        
        hierarchy = {
            "current": chunk,
            "parents": [],
            "children": [],
        }
        
        # Traverse up to get all parents
        current_parent_id = chunk.get('parent_chunk_id')
        while current_parent_id:
            parent = self._get_chunk_by_id(current_parent_id)
            if parent:
                hierarchy["parents"].insert(0, parent)
                current_parent_id = parent.get('parent_chunk_id')
            else:
                break
        
        # Get all children
        child_ids = chunk.get('child_chunk_ids', [])
        for child_id in child_ids:
            child = self._get_chunk_by_id(child_id)
            if child:
                hierarchy["children"].append(child)
        
        return hierarchy
    
    def print_results(
        self,
        results: List[SearchResult],
        show_context: bool = True,
    ):
        """Pretty print search results"""
        print("\n" + "=" * 80)
        print(f"🔍 Found {len(results)} results")
        print("=" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"\n📄 Result {i}")
            print(f"Score: {result.score:.4f}")
            print(f"Document: {result.title[:80]}...")
            print(f"Type: {result.document_type} | Level: {result.hierarchy_level}")
            print(f"Chunk Type: {result.chunk_type}")
            
            # Show file source
            if result.file_name:
                print(f"📁 File: {result.file_name}")
            if result.relative_path:
                print(f"📂 Path: {result.relative_path}")
            
            if result.section_title:
                print(f"Section: {result.section_title[:60]}")
            
            print(f"\n💬 Content:")
            print(f"{result.text[:300]}...")
            
            if show_context:
                # Show parent context
                parent_context = result.metadata.get('parent_context')
                if parent_context:
                    print(f"\n⬆️  Parent ({parent_context['chunk_type']}):")
                    print(f"   {parent_context['text']}...")
                
                # Show children
                children_context = result.metadata.get('children_context', [])
                if children_context:
                    print(f"\n⬇️  Children ({len(children_context)}):")
                    for child in children_context:
                        print(f"   - {child['chunk_type']}: {child['text'][:80]}...")
            
            print("-" * 80)


def main():
    """Example usage"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize query engine
    engine = QueryEngine(device="cpu")
    
    # Example queries
    queries = [
        "จดทะเบียนโอนที่ดินต้องใช้เอกสารอะไรบ้าง",
        "ค่าธรรมเนียมการจดทะเบียนที่ดินเท่าไหร่",
        "วิธีการจำนองที่ดิน",
    ]
    
    for query in queries:
        print("\n" + "=" * 80)
        print(f"Query: {query}")
        print("=" * 80)
        
        # Search
        results = engine.search(
            query=query,
            top_k=3,
            use_hierarchy=True,
        )
        
        # Print results
        engine.print_results(results, show_context=True)
        
        input("\nPress Enter for next query...")


if __name__ == "__main__":
    main()
