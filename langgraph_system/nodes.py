"""
LangGraph Nodes for น้องไอดิน
Each node represents a step in the conversation workflow
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

from typing import Dict, Any, List
from datetime import datetime
import asyncio
import time
import pickle
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from qdrant_client import QdrantClient
import logging

from langgraph_system.state import ChatState
from rag_system.prompts import ROLE_INFO, OUT_OF_SCOPE_RESPONSE, ABOUT_BOT_RESPONSE

# Import Advanced Retrieval Engine
from src.advanced_retrieval_engine import AdvancedRetrievalEngine
from src.embedding_engine import EmbeddingEngine
from src.bm25_indexer import BM25Indexer
from src.reranker import BGEReranker

logger = logging.getLogger(__name__)

# Global cache for Advanced Retrieval Engine
_RETRIEVAL_ENGINE_CACHE = None

# Reranker settings (kept for compatibility)
RERANK_TIMEOUT = 15  # seconds
RERANK_MAX_TEXT_LENGTH = 1000  # characters


# ==============================================================================
# ROUTER NODE
# ==============================================================================
async def router_node(state: ChatState, config: RunnableConfig) -> ChatState:
    """
    Routes the query to appropriate handler
    Decision: RAG, OUT_OF_SCOPE, or ABOUT_BOT
    """
    logger.info(f"🔀 Router Node - Processing query: {state['query'][:50]}...")
    
    query = state['query']
    chat_history = state.get('chat_history', [])
    
    # Build routing prompt
    history_str = '\n'.join([
        f"{msg['role']}: {msg['content']}"
        for msg in chat_history[-4:]
    ]) if chat_history else 'ไม่มี'
    
    routing_prompt = f"""คุณคือ AI Query Classifier สำหรับแชทบอท "น้องไอดิน" ของกรมที่ดิน

**หน้าที่:** วิเคราะห์คำถามและจัดเส้นทาง

**หมวดงานของกรมที่ดิน:**
- การโอนที่ดิน (การซื้อขาย, การโอนกรรมสิทธิ์)
- การจำนองที่ดิน
- การเช่าที่ดิน
- ค่าธรรมเนียมและภาษี
- เอกสารสิทธิ์ที่ดิน (โฉนด, น.ส.3, ส.ค.1)
- สิทธิ์ของคนต่างชาติ
- การโอนมรดก
- กฎหมายที่ดิน

**เส้นทาง (ตอบเพียง 1 คำ):**
- `RAG` - คำถามเกี่ยวกับงานกรมที่ดิน (ต้องการค้นหาข้อมูล)
- `OUT_OF_SCOPE` - คำถามนอกเหนือขอบเขต (ความรู้ทั่วไป, เรื่องอื่น)
- `ABOUT_BOT` - ถามเกี่ยวกับตัวบอท (สวัสดี, เธอคือใคร, ทำอะไรได้บ้าง)

**ตัวอย่าง:**
- "ค่าธรรมเนียมโอนที่ดิน" → RAG
- "คนต่างชาติซื้อที่ดินได้ไหม" → RAG
- "สอนทำอาหาร" → OUT_OF_SCOPE
- "สวัสดีครับ" → ABOUT_BOT

**ประวัติการสนทนา:**
{history_str}

**คำถามปัจจุบัน:** "{query}"

**ตอบเพียงคำเดียว (RAG, OUT_OF_SCOPE, หรือ ABOUT_BOT):**"""

    # Get config from RunnableConfig
    cfg = config.get('configurable', {})
    
    # Initialize LLM
    llm = ChatOpenAI(
        model=cfg['llm_model'],
        api_key=cfg['llm_api_key'],
        base_url=cfg['llm_api_base'],
        temperature=0.1,
    )
    
    # Get decision
    try:
        response = await llm.ainvoke([HumanMessage(content=routing_prompt)])
        
        # Handle both content and reasoning_content (TokenMind API quirk)
        decision = None
        if hasattr(response, 'content') and response.content:
            decision = response.content.strip().upper()
        elif hasattr(response, 'reasoning_content'):
            decision = response.reasoning_content.strip().upper()
        else:
            # Try to extract from response dict
            if isinstance(response, dict):
                decision = response.get('content', response.get('reasoning_content', '')).strip().upper()
        
        # Extract only the decision keyword
        if decision:
            # Clean up extra text and extract keyword
            for keyword in ['RAG', 'OUT_OF_SCOPE', 'ABOUT_BOT']:
                if keyword in decision:
                    decision = keyword
                    break
            else:
                # No valid keyword found
                logger.warning(f"⚠️  Could not extract valid decision from: {decision[:100]}")
                decision = 'OUT_OF_SCOPE'
        else:
            decision = 'OUT_OF_SCOPE'
        
        # Validate decision
        if decision not in ['RAG', 'OUT_OF_SCOPE', 'ABOUT_BOT']:
            logger.warning(f"Invalid routing decision: {decision}, defaulting to OUT_OF_SCOPE")
            decision = 'OUT_OF_SCOPE'
        
        logger.info(f"✅ Routing decision: {decision}")
        
        # Update state
        state['routing_decision'] = decision
        state['intermediate_steps'].append({
            "step": "router",
            "decision": decision,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Router error: {e}")
        logger.info("⚠️  Attempting fallback keyword-based routing...")
        
        # Fallback: Simple keyword-based routing
        query_lower = query.lower()
        
        # Check for ABOUT_BOT keywords
        about_keywords = ['สวัสดี', 'hello', 'hi', 'เธอคือใคร', 'ชื่ออะไร', 'ทำอะไรได้', 'ช่วยอะไรได้']
        if any(kw in query_lower for kw in about_keywords):
            decision = 'ABOUT_BOT'
        
        # Check for land-related keywords (RAG)
        elif any(kw in query_lower for kw in [
            'ที่ดิน', 'โฉนด', 'โอน', 'จำนอง', 'เช่า', 'มรดก', 
            'ธรรมเนียม', 'ภาษี', 'ต่างด้าว', 'ต่างชาติ', 
            'เอกสาร', 'น.ส.3', 'ส.ค.1', 'กรมที่ดิน', 'จดทะเบียน',
            'ค่า', 'ขั้นตอน', 'วิธี', 'กฎหมาย', 'มาตรา'
        ]):
            decision = 'RAG'
        
        # Otherwise OUT_OF_SCOPE
        else:
            decision = 'OUT_OF_SCOPE'
        
        logger.info(f"✅ Fallback routing decision: {decision}")
        state['routing_decision'] = decision
        state['error'] = f"Router LLM error (used fallback): {str(e)}"
    
    return state


# ==============================================================================
# ABOUT BOT NODE
# ==============================================================================
async def about_bot_node(state: ChatState, config: RunnableConfig) -> ChatState:
    """
    Handles ABOUT_BOT queries with predefined response
    """
    logger.info("🤖 About Bot Node - Returning bot introduction")
    
    state['generated_answer'] = ABOUT_BOT_RESPONSE
    state['metadata']['handler'] = 'about_bot'
    state['intermediate_steps'].append({
        "step": "about_bot",
        "timestamp": datetime.now().isoformat()
    })
    
    return state


# ==============================================================================
# OUT OF SCOPE NODE
# ==============================================================================
async def out_of_scope_node(state: ChatState, config: RunnableConfig) -> ChatState:
    """
    Handles OUT_OF_SCOPE queries with polite refusal
    """
    logger.info("⛔ Out of Scope Node - Returning refusal message")
    
    state['generated_answer'] = OUT_OF_SCOPE_RESPONSE
    state['metadata']['handler'] = 'out_of_scope'
    state['intermediate_steps'].append({
        "step": "out_of_scope",
        "timestamp": datetime.now().isoformat()
    })
    
    return state


# ==============================================================================
# RETRIEVAL NODE (Using Advanced Retrieval Engine)
# ==============================================================================
async def retrieval_node(state: ChatState, config: RunnableConfig) -> ChatState:
    """
    Retrieves relevant documents using Advanced Retrieval Engine
    Features: BM25 + Dense Vector + RRF Fusion + Query Analysis
    """
    logger.info(f"🔍 Retrieval Node - Advanced Search for: {state['query'][:50]}...")
    
    # Track timing
    start_time = time.time()
    
    # Get config from RunnableConfig
    cfg = config.get('configurable', {})
    
    try:
        # Initialize Advanced Retrieval Engine (cached)
        global _RETRIEVAL_ENGINE_CACHE
        
        if _RETRIEVAL_ENGINE_CACHE is None:
            logger.info("📦 Initializing Advanced Retrieval Engine (first time)...")
            
            # Load BM25 vocabulary
            vocab_path = cfg.get('bm25_vocabulary_path', 'data/bm25_vocabulary.pkl')
            with open(vocab_path, 'rb') as f:
                vocab_data = pickle.load(f)
            
            # Initialize components
            qdrant_client = QdrantClient(
                host=cfg['qdrant_host'],
                port=cfg['qdrant_port']
            )
            
            embedding_engine = EmbeddingEngine(device='cpu')
            
            bm25_indexer = BM25Indexer()
            bm25_indexer.vocabulary = vocab_data['vocabulary']
            bm25_indexer.idf_scores = vocab_data['idf_scores']
            bm25_indexer.avg_doc_length = vocab_data['avg_doc_length']
            bm25_indexer.doc_count = vocab_data['doc_count']
            
            reranker = BGEReranker()
            
            # Create Advanced Retrieval Engine
            _RETRIEVAL_ENGINE_CACHE = AdvancedRetrievalEngine(
                qdrant_client=qdrant_client,
                embedding_engine=embedding_engine,
                bm25_indexer=bm25_indexer,
                reranker=reranker,
                vocabulary=vocab_data['vocabulary'],
            )
            logger.info("✅ Advanced Retrieval Engine initialized and cached")
        
        retrieval_engine = _RETRIEVAL_ENGINE_CACHE
        
        # Use complete multi-stage retrieval pipeline
        logger.info("🚀 Running Advanced Retrieval (BM25 + Dense + RRF + Query Analysis)...")
        results = retrieval_engine.retrieve(
            query=state['query'],
            top_k=cfg.get('top_k', 10),
            enable_reranker=cfg.get('enable_reranker', True),
            enable_context_expansion=cfg.get('enable_context_expansion', True),
            alpha=0.5,  # Balanced BM25 and Dense
            adaptive=True,  # Enable query analysis
        )
        
        # Extract query analysis metadata (if available)
        query_analysis_metadata = None
        if hasattr(retrieval_engine, 'last_query_analysis') and retrieval_engine.last_query_analysis:
            qa = retrieval_engine.last_query_analysis
            query_analysis_metadata = {
                "query_type": qa.query_type,
                "target_level": qa.target_level,
                "is_complex": qa.is_complex,
                "keywords": qa.keywords[:5] if qa.keywords else [],  # Limit to 5
                "estimated_answer_length": qa.estimated_answer_length
            }
        
        # Format results for state (convert RetrievalResult to dict)
        documents = []
        for i, result in enumerate(results):
            doc = {
                "rank": i + 1,
                "score": result.score,
                "rerank_score": result.rerank_score,
                "text": result.text,
                "section_title": result.section_title or '',
                "chunk_type": result.chunk_type or '',
                "document_title": result.filename or '',
                "hierarchy_level": result.hierarchy_level,
                # Context expansion
                "parent_text": result.parent_text,
                "children_texts": result.children_texts,
                # Fusion scores
                "bm25_score": result.bm25_score,
                "dense_score": result.dense_score,
                "fusion_method": result.fusion_method,
                # Full metadata
                "metadata": {
                    "chunk_id": result.chunk_id,
                    "filename": result.filename,
                    "filepath": result.filepath,
                    "document_id": result.document_id,
                }
            }
            documents.append(doc)
        
        logger.info(f"✅ Advanced Retrieval: {len(documents)} documents (BM25+Dense+RRF)")
        
        # Calculate retrieval time
        retrieval_time = time.time() - start_time
        
        # Store both retrieved and reranked in state (since Advanced Engine does both)
        state['retrieved_documents'] = documents
        state['reranked_documents'] = documents[:3]  # Top 3 after reranking
        
        # Store retrieval metadata in state
        state['metadata']['retrieval_method'] = 'hybrid_rrf' if documents else 'none'
        state['metadata']['query_analysis'] = query_analysis_metadata
        state['metadata']['handler'] = 'rag'
        state['metadata']['retrieval_time_seconds'] = round(retrieval_time, 3)
        
        state['intermediate_steps'].append({
            "step": "advanced_retrieval",
            "method": "BM25 + Dense + RRF + Rerank + Context Expansion",
            "count": len(documents),
            "time_seconds": round(retrieval_time, 3),
            "top_rerank_score": documents[0].get('rerank_score') if documents else 0,
            "query_analysis": query_analysis_metadata,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Advanced Retrieval error: {e}")
        logger.warning("⚠️ Falling back to simple retrieval...")
        
        # Fallback to simple dense-only search
        try:
            from sentence_transformers import SentenceTransformer
            
            client = QdrantClient(
                host=cfg['qdrant_host'],
                port=cfg['qdrant_port']
            )
            
            embed_model = SentenceTransformer('BAAI/bge-m3')
            query_embedding = embed_model.encode(state['query']).tolist()
            
            search_result = client.query_points(
                collection_name=cfg['qdrant_collection'],
                query=query_embedding,
                using="dense",
                limit=cfg.get('top_k', 10)
            )
            
            documents = []
            for i, hit in enumerate(search_result.points):
                doc = {
                    "rank": i + 1,
                    "score": hit.score,
                    "text": hit.payload.get('text', hit.payload.get('chunk_text', '')),
                    "section_title": hit.payload.get('section_title', ''),
                    "chunk_type": hit.payload.get('chunk_type', ''),
                    "document_title": hit.payload.get('document_title', ''),
                    "metadata": hit.payload
                }
                documents.append(doc)
            
            state['retrieved_documents'] = documents
            state['reranked_documents'] = documents[:3]
            logger.info(f"✅ Fallback retrieval: {len(documents)} documents (dense only)")
            
        except Exception as fallback_error:
            logger.error(f"❌ Fallback also failed: {fallback_error}")
            state['error'] = f"Retrieval error: {str(e)}"
            state['retrieved_documents'] = []
            state['reranked_documents'] = []
    
    return state


# ==============================================================================
# RERANK NODE (Now skipped - done by Advanced Retrieval Engine)
# ==============================================================================
async def rerank_node(state: ChatState, config: RunnableConfig) -> ChatState:
    """
    Rerank node - now a pass-through since Advanced Retrieval Engine handles reranking
    """
    logger.info("⏭️ Rerank Node - Skipping (already done by Advanced Retrieval Engine)")
    
    # Advanced Retrieval Engine already did reranking
    # Just ensure reranked_documents is set
    if 'reranked_documents' not in state or not state['reranked_documents']:
        # Fallback: use top 3 from retrieved_documents
        state['reranked_documents'] = state.get('retrieved_documents', [])[:3]
    
    state['intermediate_steps'].append({
        "step": "rerank",
        "note": "Handled by Advanced Retrieval Engine",
        "count": len(state.get('reranked_documents', [])),
        "timestamp": datetime.now().isoformat()
    })
    
    return state


# ==============================================================================
# GENERATION NODE (Enhanced with Context Expansion)
# ==============================================================================
async def generation_node(state: ChatState, config: RunnableConfig) -> ChatState:
    """
    Generates answer using LLM with retrieved context + hierarchical expansion
    """
    logger.info("✨ Generation Node - Generating answer with context expansion...")
    
    # Track timing
    start_time = time.time()
    
    try:
        documents = state.get('reranked_documents', [])
        
        if not documents:
            state['generated_answer'] = "ขออภัยค่ะ น้องไอดินไม่พบข้อมูลที่เกี่ยวข้องกับคำถามของคุณ"
            return state
        
        # Build context with hierarchical expansion
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[เอกสารที่ {i}]")
            
            # Add source info
            if doc.get('document_title'):
                context_parts.append(f"📄 ที่มา: {doc['document_title']}")
            if doc.get('section_title'):
                context_parts.append(f"📑 หัวข้อ: {doc['section_title']}")
            
            # Add hierarchy info
            if doc.get('hierarchy_level') is not None:
                context_parts.append(f"🏷️  ระดับ: {doc['hierarchy_level']}")
            
            # Add fusion scores (if available)
            bm25_score = doc.get('bm25_score')
            dense_score = doc.get('dense_score')
            rerank_score = doc.get('rerank_score')
            
            if bm25_score is not None and dense_score is not None:
                rerank_val = rerank_score if rerank_score is not None else 0
                context_parts.append(
                    f"🎯 คะแนน: Rerank={rerank_val:.3f}, "
                    f"BM25={bm25_score:.3f}, "
                    f"Dense={dense_score:.3f}"
                )
            
            # Main content
            context_parts.append(f"\n**เนื้อหาหลัก:**")
            context_parts.append(f"{doc['text']}")
            
            # Add parent context if available (from context expansion)
            if doc.get('parent_text'):
                context_parts.append(f"\n**บริบทจากหัวข้อใหญ่:**")
                # Limit parent text to avoid too long context
                parent_text = doc['parent_text'][:500]
                context_parts.append(f"{parent_text}...")
            
            # Add children contexts if available (from context expansion)
            if doc.get('children_texts') and len(doc['children_texts']) > 0:
                context_parts.append(f"\n**รายละเอียดเพิ่มเติม ({len(doc['children_texts'])} รายการ):**")
                for j, child_text in enumerate(doc['children_texts'][:2], 1):  # Limit to 2 children
                    # Limit child text
                    child_preview = child_text[:200] if child_text else ''
                    context_parts.append(f"  {j}. {child_preview}...")
            
            context_parts.append("")  # Empty line between documents
        
        context = "\n".join(context_parts)
        
        # Log context stats
        logger.info(f"📊 Context stats: {len(context)} chars, {len(documents)} docs")
        for i, doc in enumerate(documents, 1):
            has_parent = "✅" if doc.get('parent_text') else "❌"
            num_children = len(doc.get('children_texts', []))
            bm25 = doc.get('bm25_score') or 0
            dense = doc.get('dense_score') or 0
            logger.info(
                f"   Doc {i}: Parent={has_parent}, Children={num_children}, "
                f"BM25={bm25:.3f}, Dense={dense:.3f}"
            )
        
        # Build chat history
        history_messages = []
        for msg in state.get('chat_history', [])[-3:]:
            if msg['role'] == 'user':
                history_messages.append(HumanMessage(content=msg['content']))
            else:
                history_messages.append(SystemMessage(content=msg['content']))
        
        # Build prompt
        system_prompt = f"""{ROLE_INFO}

**ข้อมูลจากเอกสาร (พร้อมบริบทเพิ่มเติม):**
{context}"""
        
        messages = [SystemMessage(content=system_prompt)] + history_messages + [
            HumanMessage(content=state['query'])
        ]
        
        # Get config from RunnableConfig
        cfg = config.get('configurable', {})
        
        # Generate
        llm = ChatOpenAI(
            model=cfg['llm_model'],
            api_key=cfg['llm_api_key'],
            base_url=cfg['llm_api_base'],
            temperature=cfg.get('llm_temperature', 0.5),
        )
        
        response = await llm.ainvoke(messages)
        answer = response.content
        
        # Calculate generation time
        generation_time = time.time() - start_time
        
        logger.info(f"✅ Generated answer: {len(answer)} characters")
        
        state['generated_answer'] = answer
        state['sources'] = [
            {
                "title": doc.get('document_title') or doc.get('filename') or 'ไม่ระบุแหล่งที่มา',
                "section": doc.get('section_title') or 'ข้อมูลทั่วไป',
                "document_id": doc.get('document_id', ''),
                "chunk_type": doc.get('chunk_type', ''),
                "score": doc.get('rerank_score', doc.get('score', 0)),
                "bm25_score": doc.get('bm25_score'),
                "dense_score": doc.get('dense_score'),
                "has_parent": bool(doc.get('parent_text')),
                "num_children": len(doc.get('children_texts', [])),
            }
            for doc in documents
        ]
        state['metadata']['handler'] = 'rag'
        state['metadata']['generation_time_seconds'] = round(generation_time, 3)
        state['intermediate_steps'].append({
            "step": "generation",
            "answer_length": len(answer),
            "time_seconds": round(generation_time, 3),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Generation error: {e}")
        state['generated_answer'] = f"ขออภัยค่ะ เกิดข้อผิดพลาด: {str(e)}"
        state['error'] = f"Generation error: {str(e)}"
    
    return state
