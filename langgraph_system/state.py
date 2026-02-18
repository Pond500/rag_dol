"""
LangGraph State Definition for น้องไอดิน
Defines the state structure for the conversation flow
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add
from datetime import datetime


class ChatState(TypedDict):
    """
    Main state for chat conversation
    
    Fields:
        - query: User's current question
        - session_id: Session identifier
        - chat_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
        - routing_decision: Decision from router (RAG/OUT_OF_SCOPE/ABOUT_BOT)
        - retrieved_documents: Documents retrieved from Qdrant
        - reranked_documents: Documents after reranking
        - generated_answer: Final answer from LLM
        - sources: Source references
        - metadata: Additional metadata
        - error: Error message if any
        - intermediate_steps: Tracking of execution steps
    """
    # Input
    query: str
    session_id: str
    chat_history: Annotated[List[Dict[str, str]], add]
    
    # Routing
    routing_decision: Optional[str]
    
    # Retrieval
    retrieved_documents: Annotated[List[Dict[str, Any]], add]
    reranked_documents: Optional[List[Dict[str, Any]]]
    
    # Generation
    generated_answer: Optional[str]
    sources: Annotated[List[Dict[str, Any]], add]
    
    # Metadata
    metadata: Dict[str, Any]
    error: Optional[str]
    intermediate_steps: Annotated[List[Dict[str, Any]], add]


class GraphConfig(TypedDict):
    """
    Configuration for the graph
    """
    # LLM settings
    llm_model: str
    llm_api_base: str
    llm_api_key: str
    llm_temperature: float
    
    # Retrieval settings
    qdrant_host: str
    qdrant_port: int
    qdrant_collection: str
    top_k: int
    enable_reranker: bool
    
    # System settings
    max_history_turns: int
    enable_memory: bool


def create_initial_state(query: str, session_id: str, chat_history: List[Dict[str, str]] = None) -> ChatState:
    """
    Create initial state for a new conversation turn
    
    Args:
        query: User's question
        session_id: Session ID
        chat_history: Previous conversation history
    
    Returns:
        Initial ChatState
    """
    return ChatState(
        query=query,
        session_id=session_id,
        chat_history=chat_history or [],
        routing_decision=None,
        retrieved_documents=[],
        reranked_documents=None,
        generated_answer=None,
        sources=[],
        metadata={
            "start_time": datetime.now().isoformat(),
            "workflow_version": "langgraph_v1"
        },
        error=None,
        intermediate_steps=[]
    )
