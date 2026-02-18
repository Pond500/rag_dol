"""
BM25 Indexer for Thai Language Text
Generates sparse vectors for BM25 keyword search
"""
import logging
from typing import List, Dict, Any, Tuple
from collections import Counter
import math
from pythainlp.tokenize import word_tokenize
from pythainlp import corpus
import numpy as np

logger = logging.getLogger(__name__)


class BM25Indexer:
    """
    BM25 (Best Matching 25) indexer for Thai language text.
    
    Generates sparse vector representations suitable for Qdrant.
    Uses pythainlp for Thai tokenization.
    
    Parameters:
    -----------
    k1 : float
        Term frequency saturation parameter (default: 1.5)
        Controls how quickly term frequency influence saturates
    b : float
        Length normalization parameter (default: 0.75)
        0 = no normalization, 1 = full normalization
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        
        # Statistics
        self.doc_count = 0
        self.avg_doc_length = 0.0
        self.doc_lengths: List[int] = []
        
        # IDF scores for terms
        self.idf_scores: Dict[str, float] = {}
        
        # Thai stopwords
        self.stopwords = set(corpus.thai_stopwords())
        
        logger.info(f"BM25Indexer initialized with k1={k1}, b={b}")
        logger.info(f"Loaded {len(self.stopwords)} Thai stopwords")
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize Thai text and remove stopwords.
        
        Args:
            text: Input text string
            
        Returns:
            List of tokens (words)
        """
        # Tokenize using pythainlp (newmm engine - best for Thai)
        tokens = word_tokenize(text, engine='newmm', keep_whitespace=False)
        
        # Clean and filter
        tokens = [
            token.lower().strip()
            for token in tokens
            if token.strip() and token.lower() not in self.stopwords
        ]
        
        return tokens
    
    def fit(self, documents: List[str]) -> None:
        """
        Fit BM25 model on a corpus of documents.
        Calculates IDF scores and document statistics.
        
        Args:
            documents: List of text documents
        """
        self.doc_count = len(documents)
        
        # Tokenize all documents
        tokenized_docs = [self.tokenize(doc) for doc in documents]
        
        # Calculate document lengths
        self.doc_lengths = [len(tokens) for tokens in tokenized_docs]
        self.avg_doc_length = sum(self.doc_lengths) / self.doc_count if self.doc_count > 0 else 0
        
        # Calculate document frequencies (DF)
        df_counter = Counter()
        for tokens in tokenized_docs:
            unique_tokens = set(tokens)
            df_counter.update(unique_tokens)
        
        # Calculate IDF scores
        # IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
        for term, df in df_counter.items():
            idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)
            self.idf_scores[term] = idf
        
        logger.info(f"BM25 fitted on {self.doc_count} documents")
        logger.info(f"Average document length: {self.avg_doc_length:.2f} tokens")
        logger.info(f"Vocabulary size: {len(self.idf_scores)} unique terms")
    
    def get_bm25_scores(self, query_tokens: List[str], doc_tokens: List[str], doc_length: int) -> float:
        """
        Calculate BM25 score for a single document given query tokens.
        
        Args:
            query_tokens: Tokenized query
            doc_tokens: Tokenized document
            doc_length: Length of document in tokens
            
        Returns:
            BM25 score (float)
        """
        # Count term frequencies in document
        tf_counter = Counter(doc_tokens)
        
        score = 0.0
        for term in query_tokens:
            if term not in self.idf_scores:
                continue
            
            # Get term frequency
            tf = tf_counter.get(term, 0)
            if tf == 0:
                continue
            
            # Get IDF
            idf = self.idf_scores[term]
            
            # BM25 formula
            # score(D,Q) = Σ IDF(qi) * (f(qi,D) * (k1 + 1)) / (f(qi,D) + k1 * (1 - b + b * |D| / avgdl))
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
            
            score += idf * (numerator / denominator)
        
        return score
    
    def get_sparse_vector(self, text: str, vocabulary_mapping: Dict[str, int]) -> Dict[str, Any]:
        """
        Generate sparse vector representation for Qdrant.
        
        Qdrant sparse vectors format:
        {
            "indices": [1, 5, 10],  # vocabulary indices
            "values": [0.8, 0.6, 0.4]  # BM25 scores
        }
        
        Args:
            text: Input text
            vocabulary_mapping: Dict mapping terms to indices
            
        Returns:
            Sparse vector dict with "indices" and "values"
        """
        tokens = self.tokenize(text)
        tf_counter = Counter(tokens)
        doc_length = len(tokens)
        
        indices = []
        values = []
        
        for term, tf in tf_counter.items():
            if term not in vocabulary_mapping:
                continue
            
            if term not in self.idf_scores:
                continue
            
            # Calculate BM25 score for this term
            idf = self.idf_scores[term]
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
            term_score = idf * (numerator / denominator)
            
            indices.append(vocabulary_mapping[term])
            values.append(float(term_score))
        
        return {
            "indices": indices,
            "values": values
        }
    
    def build_vocabulary(self, documents: List[str]) -> Dict[str, int]:
        """
        Build vocabulary mapping from corpus.
        Each unique term gets an integer index.
        
        Args:
            documents: List of text documents
            
        Returns:
            Dict mapping term to index
        """
        # Tokenize all documents
        all_tokens = []
        for doc in documents:
            tokens = self.tokenize(doc)
            all_tokens.extend(tokens)
        
        # Get unique terms
        unique_terms = sorted(set(all_tokens))
        
        # Create mapping
        vocabulary = {term: idx for idx, term in enumerate(unique_terms)}
        
        logger.info(f"Built vocabulary with {len(vocabulary)} unique terms")
        
        return vocabulary
    
    def encode_documents(
        self, 
        documents: List[str],
        vocabulary_mapping: Dict[str, int] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Encode multiple documents into sparse vectors.
        
        Args:
            documents: List of text documents
            vocabulary_mapping: Optional pre-built vocabulary
            
        Returns:
            Tuple of (sparse_vectors, vocabulary_mapping)
        """
        # Build vocabulary if not provided
        if vocabulary_mapping is None:
            vocabulary_mapping = self.build_vocabulary(documents)
        
        # Fit BM25 on documents
        self.fit(documents)
        
        # Generate sparse vectors
        sparse_vectors = []
        for doc in documents:
            sparse_vec = self.get_sparse_vector(doc, vocabulary_mapping)
            sparse_vectors.append(sparse_vec)
        
        logger.info(f"Encoded {len(sparse_vectors)} documents into sparse vectors")
        
        return sparse_vectors, vocabulary_mapping
    
    def encode_query(self, query: str, vocabulary_mapping: Dict[str, int]) -> Dict[str, Any]:
        """
        Encode query into sparse vector.
        
        Args:
            query: Query string
            vocabulary_mapping: Vocabulary mapping (from training)
            
        Returns:
            Sparse vector dict
        """
        return self.get_sparse_vector(query, vocabulary_mapping)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get BM25 indexer statistics"""
        return {
            "doc_count": self.doc_count,
            "avg_doc_length": self.avg_doc_length,
            "vocabulary_size": len(self.idf_scores),
            "stopwords_count": len(self.stopwords),
            "k1": self.k1,
            "b": self.b,
        }


def test_bm25():
    """Test BM25 indexer with Thai text"""
    documents = [
        "การจดทะเบียนที่ดินต้องเตรียมเอกสารหลายอย่าง เช่น บัตรประชาชน ทะเบียนบ้าน",
        "ค่าธรรมเนียมการโอนที่ดินคำนวณจากราคาประเมิน",
        "จดทะเบียนจำนองที่ดินกับธนาคารต้องใช้เวลา 1-2 วัน",
    ]
    
    indexer = BM25Indexer()
    
    # Build vocabulary and fit
    vocabulary = indexer.build_vocabulary(documents)
    indexer.fit(documents)
    
    print(f"Vocabulary size: {len(vocabulary)}")
    print(f"Stats: {indexer.get_stats()}")
    
    # Test query
    query = "จดทะเบียนที่ดินใช้เอกสารอะไร"
    query_vec = indexer.encode_query(query, vocabulary)
    
    print(f"\nQuery: {query}")
    print(f"Sparse vector: {len(query_vec['indices'])} non-zero terms")
    print(f"Indices: {query_vec['indices'][:5]}")
    print(f"Values: {query_vec['values'][:5]}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_bm25()
