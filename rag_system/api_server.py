"""
FastAPI Server for Land Department RAG System - น้องไอดิน

Simple API with 3 main endpoints:
- POST /chat - Chat with RAG system
- GET /history - Get conversation history
- POST /search - Search documents (diagnostic)
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import time
from datetime import datetime

from rag_system.rag_engine import LandDepartmentRAG
from rag_system.memory import ConversationBufferMemory
from rag_system.router import route_query
from rag_system.prompts import ROLE_INFO, OUT_OF_SCOPE_RESPONSE, ABOUT_BOT_RESPONSE, CONDENSE_QUESTION_TEMPLATE

# LlamaIndex imports for LLM
from llama_index.llms.openai_like import OpenAILike
from llama_index.core import Settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Land Department RAG API - น้องไอดิน",
    description="Simple RAG API with automatic session management by น้องไอดิน",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage (in-memory)
sessions: Dict[str, Dict] = {}

# RAG system (singleton)
rag_system: LandDepartmentRAG = None

# LLM instance (singleton)
llm_instance = None


@app.on_event("startup")
async def startup_event():
    """Initialize RAG system and LLM on startup"""
    global rag_system, llm_instance
    logger.info("🚀 Starting Land Department RAG API - น้องไอดิน...")
    
    # Initialize LLM
    try:
        # LLM Configuration
        LLM_MODEL_NAME = "ptm-oss-120b"
        LLM_API_BASE = "https://tokenmind.abdul.in.th/v1"
        LLM_API_KEY = "sk-driylW9kC_SdAaHEl3350g"
        
        llm_instance = OpenAILike(
            model=LLM_MODEL_NAME,
            api_base=LLM_API_BASE,
            api_key=LLM_API_KEY,
            temperature=0.5,
            context_window=8000,
            max_new_tokens=1500,
            is_chat_model=True,
            timeout=120
        )
        Settings.llm = llm_instance
        logger.info("✅ LLM (ptm-oss-120b) initialized and set to Settings.llm")
    except Exception as e:
        logger.warning(f"⚠️  LLM initialization failed: {e}")
        llm_instance = None
    
    # Initialize RAG system
    rag_system = LandDepartmentRAG(enable_memory=False)
    logger.info("✅ น้องไอดิน พร้อมให้บริการ")


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
@app.post("/chat", response_class=JSONResponse)
async def chat(request: ChatRequest) -> Dict[str, Any]:
    """
    Chat endpoint with intelligent routing
    - Auto-creates session if not exists
    - Routes to: RAG, OUT_OF_SCOPE, or ABOUT_BOT
    - Maintains conversation history per session
    """
    start_time = time.time()
    
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
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
        
        # Route the query
        decision = await route_query(
            query=request.query,
            chat_history=memory.get_messages(),
            llm=llm_instance  # Use global LLM instance
        )
        
        answer = ""
        sources = []
        retrieved_chunks = []
        metadata = {"routing_decision": decision}
        
        # Handle based on routing decision
        if decision == 'ABOUT_BOT':
            answer = ABOUT_BOT_RESPONSE
            # Save to memory
            from rag_system.memory import Message
            memory.add_user_message(request.query)
            memory.add_assistant_message(answer)
            
        elif decision == 'OUT_OF_SCOPE':
            answer = OUT_OF_SCOPE_RESPONSE
            # Save to memory
            from rag_system.memory import Message
            memory.add_user_message(request.query)
            memory.add_assistant_message(answer)
            
        elif decision == 'RAG':
            # Attach memory to RAG system temporarily
            original_memory = rag_system.memory
            original_enable_memory = rag_system.enable_memory
            rag_system.memory = memory
            rag_system.enable_memory = True
            
            # Query RAG
            response = rag_system.query(
                query=request.query,
                top_k=3,
                enable_reranker=True,
                enable_context_expansion=True,
                alpha=0.5,
                use_llm=False,
                include_conversation_history=True,
                max_history_turns=3,
            )
            
            answer = response.answer
            sources = response.sources
            retrieved_chunks = [
                {
                    "text": chunk.text[:500],
                    "section_title": chunk.section_title,
                    "chunk_type": chunk.chunk_type,
                    "score": chunk.score,
                    "rerank_score": chunk.rerank_score,
                }
                for chunk in response.retrieved_chunks
            ]
            metadata.update(response.metadata)
            
            # Restore original memory
            rag_system.memory = original_memory
            rag_system.enable_memory = original_enable_memory
        
        # Build response
        elapsed = time.time() - start_time
        
        return JSONResponse(content={
            "session_id": request.session_id,
            "query": request.query,
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": retrieved_chunks,
            "metadata": metadata,
            "time_seconds": f"{elapsed:.3f}s",
            "status": "completed"
        })
        
    except Exception as e:
        logger.error(f"❌ Error in /chat: {e}", exc_info=True)
        elapsed = time.time() - start_time
        return JSONResponse(content={
            "session_id": request.session_id,
            "query": request.query,
            "answer": f"ขออภัยค่ะ เกิดข้อผิดพลาด: {str(e)}",
            "sources": [],
            "retrieved_chunks": [],
            "metadata": {},
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
    Diagnostic search endpoint - returns detailed retrieval information
    """
    start_time = time.time()
    
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        # Query RAG without memory
        original_enable_memory = rag_system.enable_memory
        rag_system.enable_memory = False
        
        response = rag_system.query(
            query=request.query,
            top_k=10,
            enable_reranker=True,
            enable_context_expansion=True,
            alpha=0.5,
            use_llm=False,
            include_conversation_history=False,
        )
        
        rag_system.enable_memory = original_enable_memory
        
        elapsed = time.time() - start_time
        
        return JSONResponse(content={
            "query": request.query,
            "retrieval_results": {
                "count": len(response.retrieved_chunks),
                "chunks": [
                    {
                        "rank": i + 1,
                        "score": chunk.score,
                        "rerank_score": chunk.rerank_score,
                        "text": chunk.text,
                        "section_title": chunk.section_title,
                        "chunk_type": chunk.chunk_type,
                        "hierarchy_level": chunk.hierarchy_level,
                    }
                    for i, chunk in enumerate(response.retrieved_chunks)
                ]
            },
            "sources": response.sources,
            "time_seconds": f"{elapsed:.3f}s"
        })
        
    except Exception as e:
        logger.error(f"❌ Error in /search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



# ==============================================================================
# RUN
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
