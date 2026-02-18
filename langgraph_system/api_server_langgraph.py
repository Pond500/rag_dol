"""
FastAPI Server for LangGraph-based น้องไอดิน
Complete rewrite using LangGraph framework
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List
import logging
import time
from datetime import datetime

from langgraph_system.graph import create_idin_graph
from langgraph_system.state import create_initial_state
from rag_system.memory import ConversationBufferMemory

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="น้องไอดิน - LangGraph Edition",
    description="RAG API powered by LangGraph for Land Department",
    version="3.0.0-langgraph",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
langgraph_app = None
sessions: Dict[str, Dict] = {}

# Configuration
CONFIG = {
    "llm_model": "ptm-oss-120b",
    "llm_api_base": "https://tokenmind.abdul.in.th/v1",
    "llm_api_key": "sk-driylW9kC_SdAaHEl3350g",
    "llm_temperature": 0.5,
    "qdrant_host": "localhost",
    "qdrant_port": 6333,
    "qdrant_collection": "land_chunks_hybrid",
    "bm25_vocabulary_path": "data/bm25_vocabulary.pkl",  # For Advanced Retrieval
    "top_k": 10,
    "enable_reranker": True,
    "enable_context_expansion": True,  # Enable parent/child context
    "rerank_timeout": 15,  # seconds
    "rerank_max_text_length": 1000,  # characters
    "max_history_turns": 3,
    "enable_memory": True
}


@app.on_event("startup")
async def startup_event():
    """Initialize LangGraph and pre-warm Advanced Retrieval Engine"""
    global langgraph_app
    logger.info("🚀 Starting น้องไอดิน - LangGraph Edition (Advanced Retrieval)...")
    
    try:
        # Create LangGraph workflow
        langgraph_app = create_idin_graph()
        logger.info("✅ LangGraph workflow initialized")
        
        # Pre-warm Advanced Retrieval Engine
        logger.info("🔥 Pre-warming Advanced Retrieval Engine...")
        try:
            from langgraph_system import nodes
            import pickle
            from qdrant_client import QdrantClient
            from src.embedding_engine import EmbeddingEngine
            from src.bm25_indexer import BM25Indexer
            from src.reranker import BGEReranker
            from src.advanced_retrieval_engine import AdvancedRetrievalEngine
            
            # Load BM25 vocabulary
            logger.info("📦 Loading BM25 vocabulary...")
            with open(CONFIG['bm25_vocabulary_path'], 'rb') as f:
                vocab_data = pickle.load(f)
            logger.info(f"✅ Loaded {len(vocab_data['vocabulary'])} terms")
            
            # Initialize components
            logger.info("📦 Initializing retrieval components...")
            qdrant_client = QdrantClient(
                host=CONFIG['qdrant_host'],
                port=CONFIG['qdrant_port']
            )
            
            embedding_engine = EmbeddingEngine(device='cpu')
            logger.info("✅ Embedding engine initialized")
            
            bm25_indexer = BM25Indexer()
            bm25_indexer.vocabulary = vocab_data['vocabulary']
            bm25_indexer.idf_scores = vocab_data['idf_scores']
            bm25_indexer.avg_doc_length = vocab_data['avg_doc_length']
            bm25_indexer.doc_count = vocab_data['doc_count']
            logger.info("✅ BM25 indexer initialized")
            
            reranker = BGEReranker()
            logger.info("✅ Reranker initialized")
            
            # Create and cache Advanced Retrieval Engine
            nodes._RETRIEVAL_ENGINE_CACHE = AdvancedRetrievalEngine(
                qdrant_client=qdrant_client,
                embedding_engine=embedding_engine,
                bm25_indexer=bm25_indexer,
                reranker=reranker,
                vocabulary=vocab_data['vocabulary'],
            )
            logger.info("✅ Advanced Retrieval Engine initialized and cached")
            logger.info("   Features: BM25 + Dense + RRF + Query Analysis + Context Expansion")
            
        except Exception as e:
            logger.warning(f"⚠️  Advanced Retrieval pre-warming failed: {e}")
            logger.warning("   Will initialize on first use")
        
        logger.info("✅ น้องไอดิน (LangGraph) พร้อมให้บริการ")
    except Exception as e:
        logger.error(f"❌ Failed to initialize LangGraph: {e}")
        raise


# ==============================================================================
# REQUEST/RESPONSE MODELS
# ==============================================================================
class ChatRequest(BaseModel):
    session_id: str
    query: str


class SearchRequest(BaseModel):
    session_id: str
    query: str


# ==============================================================================
# API ENDPOINTS
# ==============================================================================
@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint"""
    return {
        "service": "น้องไอดิน - LangGraph Edition",
        "version": "3.0.0",
        "framework": "LangGraph",
        "status": "active"
    }


@app.get("/health", response_class=JSONResponse)
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "langgraph": langgraph_app is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/chat", response_class=JSONResponse)
async def chat(request: ChatRequest) -> Dict[str, Any]:
    """
    Chat endpoint with LangGraph workflow
    - Auto-creates session if not exists
    - Routes using LangGraph state machine
    - Maintains conversation history per session
    """
    start_time = time.time()
    
    if langgraph_app is None:
        raise HTTPException(status_code=503, detail="LangGraph not initialized")
    
    try:
        # Auto-create session if not exists
        if request.session_id not in sessions:
            created_at = datetime.now().isoformat()
            memory = ConversationBufferMemory(max_messages=50)
            sessions[request.session_id] = {
                'session_id': request.session_id,
                'memory': memory,
                'created_at': created_at,
                'last_activity': created_at,
            }
            logger.info(f"✨ Auto-created session: {request.session_id}")
        
        # Get session and update activity
        session = sessions[request.session_id]
        memory = session['memory']
        session['last_activity'] = datetime.now().isoformat()
        
        # Convert memory to chat_history format
        chat_history = [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in memory.get_messages()
        ]
        
        # Create initial state
        initial_state = create_initial_state(
            query=request.query,
            session_id=request.session_id,
            chat_history=chat_history
        )
        
        # Run LangGraph workflow
        logger.info(f"🔄 Running LangGraph for query: {request.query[:50]}...")
        final_state = await langgraph_app.ainvoke(initial_state, config={"configurable": CONFIG})
        
        # Extract results
        answer = final_state.get('generated_answer', 'ไม่สามารถสร้างคำตอบได้')
        routing_decision = final_state.get('routing_decision', 'UNKNOWN')
        sources = final_state.get('sources', [])
        error = final_state.get('error')
        
        # Extract Advanced Retrieval metadata from state
        query_analysis = final_state.get('metadata', {}).get('query_analysis')
        retrieval_method = final_state.get('metadata', {}).get('retrieval_method')
        handler = final_state.get('metadata', {}).get('handler')
        
        # Format retrieved chunks for response with full metadata
        chunks = []
        if final_state.get('reranked_documents'):
            chunks = [
                {
                    "rank": doc.get('rank', i + 1),
                    "text": doc.get('text', '')[:500],
                    "section_title": doc.get('section_title', ''),
                    "chunk_type": doc.get('chunk_type', ''),
                    "document_title": doc.get('document_title', ''),
                    "score": doc.get('score', 0),
                    "bm25_score": doc.get('bm25_score'),
                    "dense_score": doc.get('dense_score'),
                    "rerank_score": doc.get('rerank_score', 0),
                    "parent_text": doc.get('parent_text', '')[:200] if doc.get('parent_text') else None,
                    "children_texts": [child[:200] for child in doc.get('children_texts', [])] if doc.get('children_texts') else None,
                    "fusion_method": doc.get('fusion_method')
                }
                for i, doc in enumerate(final_state['reranked_documents'])
            ]
        elif final_state.get('retrieved_documents'):
            # Fallback to retrieved if no reranked
            chunks = [
                {
                    "rank": doc.get('rank', i + 1),
                    "text": doc.get('text', '')[:500],
                    "section_title": doc.get('section_title', ''),
                    "chunk_type": doc.get('chunk_type', ''),
                    "score": doc.get('score', 0),
                    "bm25_score": doc.get('bm25_score'),
                    "dense_score": doc.get('dense_score'),
                }
                for i, doc in enumerate(final_state['retrieved_documents'])
            ]
        
        # Save to memory
        memory.add_user_message(request.query)
        memory.add_assistant_message(answer)
        
        # Build response with complete metadata
        elapsed = time.time() - start_time
        
        response_data = {
            "session_id": request.session_id,
            "query": request.query,
            "answer": answer,
            "sources": sources,
            "chunks": chunks,  # Changed from retrieved_chunks
            "metadata": {
                "routing_decision": routing_decision,
                "handler": handler or routing_decision.lower(),
                "retrieval_method": retrieval_method,
                "query_analysis": query_analysis,
                "framework": "langgraph",
                "workflow_steps": len(final_state.get('intermediate_steps', [])),
                "chunks_count": len(chunks),
                "error": error
            },
            "time_seconds": f"{elapsed:.3f}s",
            "status": "completed" if not error else "completed_with_errors"
        }
        
        logger.info(f"✅ Chat completed in {elapsed:.3f}s - Decision: {routing_decision}")
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"❌ Error in /chat: {e}", exc_info=True)
        elapsed = time.time() - start_time
        return JSONResponse(content={
            "session_id": request.session_id,
            "query": request.query,
            "answer": f"ขออภัยค่ะ เกิดข้อผิดพลาด: {str(e)}",
            "sources": [],
            "chunks": [],  # Changed from retrieved_chunks
            "metadata": {
                "error": str(e),
                "framework": "langgraph"
            },
            "time_seconds": f"{elapsed:.3f}s",
            "status": "error"
        }, status_code=500)


@app.get("/history/{session_id}", response_class=JSONResponse)
async def get_history(session_id: str) -> Dict[str, Any]:
    """
    Get conversation history for a session
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    session = sessions[session_id]
    memory = session['memory']
    messages = memory.get_messages()
    stats = memory.get_statistics()
    
    return JSONResponse(content={
        "session_id": session_id,
        "created_at": session['created_at'],
        "last_activity": session['last_activity'],
        "statistics": stats,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in messages
        ]
    })


@app.post("/search", response_class=JSONResponse)
async def search(request: SearchRequest) -> Dict[str, Any]:
    """
    Diagnostic search endpoint - returns detailed retrieval information without LLM generation
    Uses LangGraph workflow but skips generation step
    """
    start_time = time.time()
    
    if langgraph_app is None:
        raise HTTPException(status_code=503, detail="LangGraph not initialized")
    
    try:
        # Create a temporary state for search (no session memory)
        initial_state = create_initial_state(
            query=request.query,
            session_id=request.session_id,
            chat_history=[]  # No history for diagnostic search
        )
        
        # Override config to disable memory and force RAG path
        search_config = CONFIG.copy()
        search_config['enable_memory'] = False
        search_config['top_k'] = 10  # More results for diagnostic
        
        # Run workflow
        logger.info(f"🔍 Running diagnostic search for: {request.query[:50]}...")
        final_state = await langgraph_app.ainvoke(
            initial_state, 
            config={"configurable": search_config}
        )
        
        # Extract retrieval results
        retrieved_docs = final_state.get('retrieved_documents', [])
        reranked_docs = final_state.get('reranked_documents', [])
        
        # Use reranked if available, otherwise retrieved
        chunks_to_return = reranked_docs if reranked_docs else retrieved_docs
        
        elapsed = time.time() - start_time
        
        return JSONResponse(content={
            "query": request.query,
            "retrieval_results": {
                "count": len(chunks_to_return),
                "chunks": [
                    {
                        "rank": i + 1,
                        "score": chunk.get('score', 0),
                        "rerank_score": chunk.get('rerank_score', 0),
                        "text": chunk.get('text', ''),
                        "section_title": chunk.get('section_title', ''),
                        "chunk_type": chunk.get('chunk_type', ''),
                        "hierarchy_level": chunk.get('metadata', {}).get('hierarchy_level', 0),
                    }
                    for i, chunk in enumerate(chunks_to_return)
                ]
            },
            "sources": final_state.get('sources', []),
            "metadata": {
                "routing_decision": final_state.get('routing_decision'),
                "framework": "langgraph",
                "retrieved_count": len(retrieved_docs),
                "reranked_count": len(reranked_docs),
            },
            "time_seconds": f"{elapsed:.3f}s"
        })
        
    except Exception as e:
        logger.error(f"❌ Error in /search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions", response_class=JSONResponse)
async def list_sessions() -> Dict[str, Any]:
    """
    List all active sessions
    """
    return JSONResponse(content={
        "count": len(sessions),
        "sessions": [
            {
                "session_id": sid,
                "created_at": session['created_at'],
                "last_activity": session['last_activity'],
                "message_count": len(session['memory'].get_messages())
            }
            for sid, session in sessions.items()
        ]
    })


@app.delete("/session/{session_id}", response_class=JSONResponse)
async def delete_session(session_id: str) -> Dict[str, Any]:
    """
    Delete a session
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    del sessions[session_id]
    logger.info(f"🗑️  Deleted session: {session_id}")
    
    return JSONResponse(content={
        "message": f"Session {session_id} deleted successfully"
    })


@app.get("/config", response_class=JSONResponse)
async def get_config() -> Dict[str, Any]:
    """
    Get current configuration (without sensitive data)
    """
    safe_config = CONFIG.copy()
    safe_config['llm_api_key'] = "***HIDDEN***"
    
    # Add Advanced Retrieval feature flags for test compatibility
    return JSONResponse(content={
        "config": safe_config,
        "framework": "LangGraph",
        "version": "3.1.0-advanced-retrieval",
        "enable_hybrid_search": True,
        "enable_query_analysis": True,
        "enable_context_expansion": safe_config.get('enable_context_expansion', True),
        "hybrid_alpha": 0.5,
        "top_k": safe_config.get('top_k', 10),
        "rerank_top_n": safe_config.get('top_k', 10)
    })


# ==============================================================================
# RUN
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api_server_langgraph:app",
        host="0.0.0.0",
        port=8001,  # Different port from original
        reload=False,
        log_level="info",
    )
