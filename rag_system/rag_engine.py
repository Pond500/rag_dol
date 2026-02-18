"""
Complete RAG Engine for Land Department Documents

Combines all components:
- Advanced Retrieval (Hybrid Search + Reranker + Context Expansion)
- LLM Generation (with context management)
- Answer Formatting with source citations
- Conversation Memory for multi-turn conversations
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import pickle
from pathlib import Path

from qdrant_client import QdrantClient
from src.advanced_retrieval_engine import AdvancedRetrievalEngine, RetrievalResult
from src.embedding_engine import EmbeddingEngine
from src.bm25_indexer import BM25Indexer
from src.reranker import BGEReranker
from rag_system.memory import ConversationBufferMemory

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Complete RAG response with answer and metadata"""
    answer: str
    query: str
    retrieved_chunks: List[RetrievalResult]
    sources: List[Dict[str, str]]
    metadata: Dict[str, Any]


class LandDepartmentRAG:
    """
    Complete RAG System for Land Department Documents
    
    Features:
    - Multi-stage retrieval (Hybrid + Reranker + Context Expansion)
    - Adaptive strategy based on query analysis
    - Context-aware LLM generation
    - Source citation and formatting
    - Conversation memory for multi-turn conversations
    """
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        vocabulary_path: str = "data/bm25_vocabulary.pkl",
        llm_model: str = "gpt-4",  # Can be replaced with any LLM
        device: str = "cpu",
        enable_memory: bool = True,
        memory_max_messages: int = 20,
    ):
        """
        Initialize RAG system
        
        Args:
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
            vocabulary_path: Path to BM25 vocabulary
            llm_model: LLM model name
            device: Device for embeddings (cpu/cuda)
            enable_memory: Enable conversation memory
            memory_max_messages: Maximum messages in memory buffer
        """
        logger.info("=" * 80)
        logger.info("🚀 Initializing Land Department RAG System")
        logger.info("=" * 80)
        
        # Load vocabulary
        logger.info("Loading BM25 vocabulary...")
        with open(vocabulary_path, 'rb') as f:
            vocab_data = pickle.load(f)
        
        self.vocabulary = vocab_data['vocabulary']
        logger.info(f"✅ Loaded vocabulary: {len(self.vocabulary)} terms")
        
        # Initialize components
        logger.info("Initializing retrieval components...")
        
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.embedding_engine = EmbeddingEngine(device=device)
        
        self.bm25_indexer = BM25Indexer()
        self.bm25_indexer.vocabulary = self.vocabulary
        self.bm25_indexer.idf_scores = vocab_data['idf_scores']
        self.bm25_indexer.avg_doc_length = vocab_data['avg_doc_length']
        self.bm25_indexer.doc_count = vocab_data['doc_count']
        
        self.reranker = BGEReranker()
        
        # Initialize Advanced Retrieval Engine
        self.retrieval_engine = AdvancedRetrievalEngine(
            qdrant_client=self.qdrant_client,
            embedding_engine=self.embedding_engine,
            bm25_indexer=self.bm25_indexer,
            reranker=self.reranker,
            vocabulary=self.vocabulary,
        )
        
        # LLM configuration (placeholder - can be replaced with actual LLM)
        self.llm_model = llm_model
        
        # Initialize conversation memory
        self.enable_memory = enable_memory
        if enable_memory:
            self.memory = ConversationBufferMemory(max_messages=memory_max_messages)
            logger.info(f"✅ Conversation memory enabled (max_messages={memory_max_messages})")
        else:
            self.memory = None
            logger.info("ℹ️  Conversation memory disabled")
        
        logger.info("✅ RAG System initialized successfully")
        logger.info("=" * 80)
    
    def _build_context(
        self,
        results: List[RetrievalResult],
        max_context_length: int = 3000,
    ) -> str:
        """
        Build context string from retrieval results
        
        Args:
            results: Retrieved chunks
            max_context_length: Maximum context length in characters
            
        Returns:
            Formatted context string
        """
        context_parts = []
        current_length = 0
        
        for i, result in enumerate(results, 1):
            # Build chunk context
            chunk_text = f"[เอกสารที่ {i}]\n"
            
            # Add source info
            if result.filename:
                chunk_text += f"📄 ที่มา: {result.filename}\n"
            if result.section_title:
                chunk_text += f"📑 หัวข้อ: {result.section_title}\n"
            
            chunk_text += f"\n{result.text}\n"
            
            # Add parent context if available
            if result.parent_text:
                chunk_text += f"\n[บริบทเพิ่มเติม]\n{result.parent_text[:500]}...\n"
            
            # Check length
            if current_length + len(chunk_text) > max_context_length:
                break
            
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
        
        return "\n---\n\n".join(context_parts)
    
    def _generate_answer_with_llm(
        self,
        query: str,
        context: str,
        conversation_history: Optional[str] = None,
    ) -> str:
        """
        Generate answer using LLM
        
        Args:
            query: User query
            context: Retrieved context
            conversation_history: Previous conversation context
            
        Returns:
            Generated answer
        """
        # Build prompt with conversation history
        prompt_parts = ["คุณเป็นผู้ช่วยตอบคำถามเกี่ยวกับการจดทะเบียนที่ดินของกรมที่ดิน\n"]
        prompt_parts.append("ใช้ข้อมูลจากเอกสารที่ให้มาเท่านั้นในการตอบคำถาม อย่าแต่งหรือใช้ความรู้ภายนอก\n")
        
        # Add conversation history if available
        if conversation_history:
            prompt_parts.append(f"\nประวัติการสนทนา:\n{conversation_history}\n")
        
        prompt_parts.append(f"\nเอกสารอ้างอิง:\n{context}\n")
        prompt_parts.append(f"\nคำถาม: {query}\n")
        prompt_parts.append("\nคำตอบ (ตอบเป็นภาษาไทย ชัดเจน กระชับ พร้อมอ้างอิงแหล่งที่มา):\n")
        
        prompt = "".join(prompt_parts)
        
        # TODO: Replace with actual LLM call
        # For now, return a placeholder
        answer = f"""[คำตอบจาก LLM จะอยู่ตรงนี้]

สำหรับการ integrate กับ LLM จริง สามารถใช้:
1. OpenAI API: openai.ChatCompletion.create(model="{self.llm_model}", messages=[...])
2. Claude API: anthropic.Anthropic().messages.create(...)
3. Local LLM: ollama, llama.cpp, vLLM

ตอนนี้ใช้ context จากการค้นหาเท่านั้น:

{context[:500]}...
"""
        
        return answer
    
    def _extract_sources(
        self,
        results: List[RetrievalResult],
    ) -> List[Dict[str, str]]:
        """Extract source citations from results"""
        sources = []
        seen_files = set()
        
        for result in results:
            if result.filename and result.filename not in seen_files:
                sources.append({
                    'filename': result.filename,
                    'section': result.section_title or 'ทั่วไป',
                    'type': result.chunk_type or 'unknown',
                    'score': f"{result.rerank_score or result.score:.4f}",
                })
                seen_files.add(result.filename)
        
        return sources
    
    def query(
        self,
        query: str,
        top_k: int = 5,
        enable_reranker: bool = True,
        enable_context_expansion: bool = True,
        alpha: float = 0.5,
        use_llm: bool = False,
        include_conversation_history: bool = True,
        max_history_turns: int = 3,
    ) -> RAGResponse:
        """
        Complete RAG pipeline: Retrieve + Generate + Format
        
        Args:
            query: User question
            top_k: Number of chunks to retrieve
            enable_reranker: Use reranker for better ranking
            enable_context_expansion: Add parent/children context
            alpha: BM25 vs Dense weight (0.5 = balanced)
            use_llm: Use LLM for answer generation
            include_conversation_history: Include conversation history in context
            max_history_turns: Maximum conversation turns to include
            
        Returns:
            RAGResponse with answer, sources, and metadata
        """
        logger.info("\n" + "=" * 80)
        logger.info(f"📝 RAG Query: {query}")
        logger.info("=" * 80)
        
        # Stage 1: Retrieval
        logger.info("\n🔍 Stage 1: Advanced Retrieval")
        retrieved_chunks = self.retrieval_engine.retrieve(
            query=query,
            top_k=top_k,
            enable_reranker=enable_reranker,
            enable_context_expansion=enable_context_expansion,
            alpha=alpha,
            adaptive=True,
        )
        
        logger.info(f"✅ Retrieved {len(retrieved_chunks)} relevant chunks")
        
        # Stage 2: Build context
        logger.info("\n📚 Stage 2: Building Context")
        context = self._build_context(retrieved_chunks)
        logger.info(f"✅ Context built: {len(context)} characters")
        
        # Get conversation history if enabled
        conversation_history = None
        if self.enable_memory and include_conversation_history and self.memory is not None:
            conversation_history = self.memory.get_context_window(max_turns=max_history_turns)
            if conversation_history:
                logger.info(f"💬 Including conversation history ({len(conversation_history)} chars)")
        
        # Stage 3: Generate answer (optional)
        if use_llm:
            logger.info("\n🤖 Stage 3: LLM Generation")
            answer = self._generate_answer_with_llm(
                query=query,
                context=context,
                conversation_history=conversation_history
            )
            logger.info("✅ Answer generated")
        else:
            logger.info("\n📋 Stage 3: Context-only mode (no LLM)")
            answer = context
        
        # Extract sources
        sources = self._extract_sources(retrieved_chunks)
        
        # Build response
        response = RAGResponse(
            answer=answer,
            query=query,
            retrieved_chunks=retrieved_chunks,
            sources=sources,
            metadata={
                'num_chunks': len(retrieved_chunks),
                'top_score': retrieved_chunks[0].rerank_score or retrieved_chunks[0].score if retrieved_chunks else 0,
                'reranker_enabled': enable_reranker,
                'context_expansion_enabled': enable_context_expansion,
                'alpha': alpha,
                'llm_used': use_llm,
                'memory_enabled': self.enable_memory,
                'history_included': conversation_history is not None,
            }
        )
        
        # Add to memory if enabled
        if self.enable_memory and self.memory is not None:
            logger.info(f"💾 Adding to memory: query={query[:50]}..., answer length={len(answer)}")
            self.memory.add_user_message(query)
            self.memory.add_assistant_message(
                answer[:500] if len(answer) > 500 else answer,  # Store truncated answer
                metadata={'sources_count': len(sources)}
            )
            logger.info(f"✅ Memory updated: {len(self.memory)} messages")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ RAG Pipeline Complete")
        logger.info("=" * 80)
        
        return response
    
    def format_response(
        self,
        response: RAGResponse,
        include_chunks: bool = True,
        include_sources: bool = True,
    ) -> str:
        """
        Format RAG response for display
        
        Args:
            response: RAG response object
            include_chunks: Show retrieved chunks
            include_sources: Show source citations
            
        Returns:
            Formatted string
        """
        output = []
        
        output.append("=" * 80)
        output.append("🤖 คำตอบจากระบบ RAG - กรมที่ดิน")
        output.append("=" * 80)
        output.append(f"\n❓ คำถาม: {response.query}\n")
        
        # Answer
        output.append("💡 คำตอบ:")
        output.append("-" * 80)
        output.append(response.answer)
        output.append("-" * 80)
        
        # Sources
        if include_sources and response.sources:
            output.append("\n📚 แหล่งอ้างอิง:")
            for i, source in enumerate(response.sources, 1):
                output.append(f"   {i}. {source['filename']}")
                output.append(f"      หัวข้อ: {source['section']}")
                output.append(f"      คะแนน: {source['score']}")
        
        # Retrieved chunks (optional)
        if include_chunks:
            output.append("\n📄 เอกสารที่ค้นพบ:")
            for i, chunk in enumerate(response.retrieved_chunks[:3], 1):
                output.append(f"\n   [{i}] {chunk.section_title or 'ทั่วไป'}")
                output.append(f"       {chunk.text[:200]}...")
                if chunk.rerank_score:
                    output.append(f"       คะแนน: {chunk.rerank_score:.4f}")
        
        # Metadata
        output.append(f"\n📊 ข้อมูลเพิ่มเติม:")
        output.append(f"   - จำนวนเอกสาร: {response.metadata['num_chunks']}")
        output.append(f"   - คะแนนสูงสุด: {response.metadata['top_score']:.4f}")
        output.append(f"   - ใช้ Reranker: {'✅' if response.metadata['reranker_enabled'] else '❌'}")
        output.append(f"   - ขยาย Context: {'✅' if response.metadata['context_expansion_enabled'] else '❌'}")
        
        output.append("\n" + "=" * 80)
        
        return "\n".join(output)


if __name__ == "__main__":
    # Test RAG system
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize
    rag = LandDepartmentRAG()
    
    # Test query
    response = rag.query(
        query="ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่",
        top_k=3,
        enable_reranker=True,
        enable_context_expansion=True,
        use_llm=False,  # Set to True when LLM is integrated
    )
    
    # Display
    print(rag.format_response(response))
