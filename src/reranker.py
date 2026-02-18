"""
Cross-Encoder Reranker using BAAI/bge-reranker-v2-m3
Re-ranks search results for better relevance
"""
import logging
from typing import List, Tuple, Dict, Any
import torch
from sentence_transformers import CrossEncoder
import numpy as np

logger = logging.getLogger(__name__)


class BGEReranker:
    """
    BGE Reranker v2-m3 for cross-lingual reranking.
    
    This model uses a cross-encoder architecture that jointly encodes
    query and document to compute relevance scores directly.
    Much more accurate than bi-encoder (vector similarity) but slower.
    
    Model: BAAI/bge-reranker-v2-m3
    - Multilingual support (100+ languages including Thai)
    - Context length: 8192 tokens
    - Trained on 200M+ pairs
    """
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        device: str = None,
        max_length: int = 1024,
    ):
        """
        Initialize BGE Reranker.
        
        Args:
            model_name: HuggingFace model name
            device: Device to run on ('cpu', 'cuda', 'mps', or None for auto)
            max_length: Maximum sequence length
        """
        self.model_name = model_name
        self.max_length = max_length
        
        # Auto-detect device if not specified
        if device is None:
            if torch.cuda.is_available():
                device = 'cuda'
            elif torch.backends.mps.is_available():
                device = 'mps'
            else:
                device = 'cpu'
        
        self.device = device
        
        logger.info(f"Loading BGE Reranker: {model_name}")
        logger.info(f"Device: {device}")
        
        # Load cross-encoder model
        self.model = CrossEncoder(
            model_name,
            max_length=max_length,
            device=device,
        )
        
        logger.info("✓ BGE Reranker loaded successfully")
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on relevance to query.
        
        Args:
            query: Search query
            documents: List of document texts to rerank
            top_k: Return top K results (None = all)
            
        Returns:
            List of dicts with keys:
            - index: Original index in documents list
            - score: Relevance score (higher = more relevant)
            - text: Document text
        """
        if not documents:
            return []
        
        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]
        
        # Get relevance scores
        # Returns logits (unbounded scores)
        scores = self.model.predict(pairs, convert_to_tensor=True)
        
        # Convert to numpy if tensor
        if torch.is_tensor(scores):
            scores = scores.cpu().numpy()
        
        # Create results with original indices
        results = [
            {
                "index": idx,
                "score": float(score),
                "text": doc,
            }
            for idx, (score, doc) in enumerate(zip(scores, documents))
        ]
        
        # Sort by score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top K if specified
        if top_k is not None:
            results = results[:top_k]
        
        return results
    
    def rerank_with_metadata(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        text_key: str = "text",
        top_k: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates with metadata preservation.
        
        Args:
            query: Search query
            candidates: List of candidate dicts (must have text_key field)
            text_key: Key for text field in candidate dicts
            top_k: Return top K results
            
        Returns:
            Reranked list of candidate dicts with added 'rerank_score' field
        """
        if not candidates:
            return []
        
        # Extract texts
        texts = [c[text_key] for c in candidates]
        
        # Get rerank results
        rerank_results = self.rerank(query, texts, top_k=None)
        
        # Map scores back to original candidates
        reranked_candidates = []
        for result in rerank_results:
            idx = result["index"]
            candidate = candidates[idx].copy()
            candidate["rerank_score"] = result["score"]
            reranked_candidates.append(candidate)
        
        # Return top K
        if top_k is not None:
            reranked_candidates = reranked_candidates[:top_k]
        
        return reranked_candidates
    
    def compute_score(self, query: str, document: str) -> float:
        """
        Compute relevance score for a single query-document pair.
        
        Args:
            query: Search query
            document: Document text
            
        Returns:
            Relevance score (float)
        """
        scores = self.model.predict([[query, document]])
        return float(scores[0])
    
    def batch_rerank(
        self,
        queries: List[str],
        documents_list: List[List[str]],
        top_k: int = None,
    ) -> List[List[Dict[str, Any]]]:
        """
        Rerank multiple queries with their respective document lists.
        
        Args:
            queries: List of queries
            documents_list: List of document lists (one per query)
            top_k: Return top K per query
            
        Returns:
            List of reranked results (one list per query)
        """
        results = []
        for query, docs in zip(queries, documents_list):
            reranked = self.rerank(query, docs, top_k=top_k)
            results.append(reranked)
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "max_length": self.max_length,
            "model_type": "cross-encoder",
        }


def test_reranker():
    """Test reranker with Thai documents"""
    query = "จดทะเบียนโอนที่ดินต้องใช้เอกสารอะไร"
    
    documents = [
        "ค่าธรรมเนียมการจดทะเบียนโอนที่ดินคำนวณจากราคาประเมิน 2%",
        "เอกสารที่ต้องใช้ในการจดทะเบียนโอนที่ดิน ได้แก่ บัตรประชาชน ทะเบียนบ้าน โฉนดที่ดิน",
        "การจดทะเบียนจำนองที่ดินต้องไปที่สำนักงานที่ดิน",
        "ขั้นตอนการจดทะเบียนโอนที่ดิน เริ่มจากตรวจสอบเอกสาร",
        "ที่ดินประเภทนส.3 ไม่สามารถโอนได้",
    ]
    
    print("🔄 Loading BGE Reranker...")
    reranker = BGEReranker(device='cpu')
    
    print(f"\n🔍 Query: {query}\n")
    print("📄 Original documents:")
    for i, doc in enumerate(documents, 1):
        print(f"  {i}. {doc[:60]}...")
    
    print("\n🎯 Reranking...")
    results = reranker.rerank(query, documents, top_k=3)
    
    print("\n✅ Top 3 after reranking:")
    for i, result in enumerate(results, 1):
        print(f"\n  {i}. Score: {result['score']:.4f}")
        print(f"     Original index: {result['index'] + 1}")
        print(f"     Text: {result['text'][:80]}...")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_reranker()
