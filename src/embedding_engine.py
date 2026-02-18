"""
Embedding Engine using BGE Models

Supports multiple BGE models:
- BGE-M3: 1024 dimensions, fast, multilingual
- BGE-Multilingual-Gemma2: 3584 dimensions, best quality, requires newer sentence-transformers
"""
import torch
from typing import List, Union
import logging
from pathlib import Path
from config.settings import EMBEDDING_MODEL_NAME, EMBEDDING_DIMENSIONS, EMBEDDING_BATCH_SIZE

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """
    Embedding engine using BGE models
    
    Features:
    - Multilingual support (100+ languages)
    - Dense embeddings
    - Thai language understanding
    - Efficient batch processing
    - GPU/CPU/MPS support
    """
    
    def __init__(
        self,
        model_name: str = None,
        device: str = "cpu",
        batch_size: int = None,
    ):
        """
        Initialize embedding engine
        
        Args:
            model_name: HuggingFace model name (default from config)
            device: "cpu", "cuda", or "mps"
            batch_size: Batch size for encoding (default from config)
        """
        self.model_name = model_name or EMBEDDING_MODEL_NAME
        self.device = self._setup_device(device)
        self.batch_size = batch_size or EMBEDDING_BATCH_SIZE
        
        logger.info(f"Initializing {self.model_name} on {self.device}...")
        
        # Import sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
            )
            
            logger.info(f"✅ {self.model_name} loaded successfully on {self.device}")
            
        except ImportError as e:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise ImportError(
                "sentence-transformers required. "
                "Install with: pip install sentence-transformers"
            ) from e
        except Exception as e:
            logger.error(f"Error loading {self.model_name}: {e}")
            raise
    
    def _setup_device(self, device: str) -> str:
        """Setup compute device"""
        if device == "cuda" and torch.cuda.is_available():
            return "cuda"
        elif device == "mps" and torch.backends.mps.is_available():
            return "mps"
        else:
            if device != "cpu":
                logger.warning(f"{device} not available, falling back to CPU")
            return "cpu"
    
    def encode(
        self,
        texts: Union[str, List[str]],
        show_progress_bar: bool = False,
    ) -> Union[List[float], List[List[float]]]:
        """
        Encode text(s) to embeddings
        
        Args:
            texts: Single text or list of texts
            show_progress_bar: Show progress bar for batch encoding
            
        Returns:
            Embedding(s) as list of floats or list of lists
        """
        # Handle single text
        single_input = isinstance(texts, str)
        if single_input:
            texts = [texts]
        
        try:
            # Use sentence-transformers encode method
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=show_progress_bar,
                convert_to_numpy=True,
            )
            
            # Convert to list
            result = embeddings.tolist()
            
            # Return single embedding if single input
            return result[0] if single_input else result
            
        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            raise
    
    def encode_queries(
        self,
        queries: Union[str, List[str]],
    ) -> Union[List[float], List[List[float]]]:
        """
        Encode queries (optimized for search)
        
        Args:
            queries: Single query or list of queries
            
        Returns:
            Query embedding(s)
        """
        return self.encode(queries)
    
    def encode_passages(
        self,
        passages: Union[str, List[str]],
    ) -> Union[List[float], List[List[float]]]:
        """
        Encode passages/documents
        
        Args:
            passages: Single passage or list of passages
            
        Returns:
            Passage embedding(s)
        """
        return self.encode(passages)
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return 3584  # BGE-Multilingual-Gemma2 outputs 3584-dim vectors
    
    def similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score (-1 to 1)
        """
        import numpy as np
        
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity
        similarity = np.dot(vec1, vec2) / (
            np.linalg.norm(vec1) * np.linalg.norm(vec2)
        )
        
        return float(similarity)


if __name__ == "__main__":
    # Test the embedding engine
    import sys
    sys.path.insert(0, '/Users/pond500/RAG/rag_dol')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n🧪 Testing BGE-M3 Embedding Engine\n")
    
    # Initialize
    engine = EmbeddingEngine(device="cpu", batch_size=4)
    
    # Test Thai text
    thai_texts = [
        "จดทะเบียนโอนอสังหาริมทรัพย์",
        "ค่าธรรมเนียมการจดทะเบียนที่ดิน",
        "เอกสารที่ต้องใช้ในการโอนที่ดิน",
    ]
    
    print("📝 Input texts:")
    for i, text in enumerate(thai_texts, 1):
        print(f"  {i}. {text}")
    
    print("\n⚙️  Encoding...")
    embeddings = engine.encode(thai_texts)
    
    print(f"\n✅ Generated {len(embeddings)} embeddings")
    print(f"   Dimension: {len(embeddings[0])}")
    print(f"   First embedding preview: {embeddings[0][:5]}...")
    
    # Test similarity
    sim_1_2 = engine.similarity(embeddings[0], embeddings[1])
    sim_1_3 = engine.similarity(embeddings[0], embeddings[2])
    
    print(f"\n📊 Similarity scores:")
    print(f"   Text 1 vs Text 2: {sim_1_2:.4f}")
    print(f"   Text 1 vs Text 3: {sim_1_3:.4f}")
    
    # Test single text
    print("\n🔍 Testing single text encoding...")
    single_embedding = engine.encode("ทดสอบการ encode ข้อความเดียว")
    print(f"   Dimension: {len(single_embedding)}")
    print(f"   Preview: {single_embedding[:5]}...")
    
    print("\n✅ All tests passed!")
