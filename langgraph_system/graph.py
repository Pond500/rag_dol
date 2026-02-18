"""
LangGraph Workflow for น้องไอดิน
Defines the complete conversation flow using StateGraph
"""
from langgraph.graph import StateGraph, END
from typing import Literal
import logging

from langgraph_system.state import ChatState
from langgraph_system.nodes import (
    router_node,
    about_bot_node,
    out_of_scope_node,
    retrieval_node,
    rerank_node,
    generation_node
)

logger = logging.getLogger(__name__)


def should_retrieve(state: ChatState) -> Literal["about_bot", "out_of_scope", "retrieval"]:
    """
    Conditional edge: decides next node based on routing decision
    """
    decision = state.get('routing_decision')
    
    if decision == 'ABOUT_BOT':
        return "about_bot"
    elif decision == 'OUT_OF_SCOPE':
        return "out_of_scope"
    else:  # RAG
        return "retrieval"


def create_idin_graph() -> StateGraph:
    """
    Creates the complete LangGraph workflow for น้องไอดิน
    
    Flow:
        START → Router → [About Bot | Out of Scope | Retrieval → Rerank → Generation] → END
    
    Returns:
        Compiled StateGraph
    """
    logger.info("🏗️  Creating น้องไอดิน LangGraph workflow...")
    
    # Initialize graph
    workflow = StateGraph(ChatState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("about_bot", about_bot_node)
    workflow.add_node("out_of_scope", out_of_scope_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("rerank", rerank_node)
    workflow.add_node("generation", generation_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add conditional edges from router
    workflow.add_conditional_edges(
        "router",
        should_retrieve,
        {
            "about_bot": "about_bot",
            "out_of_scope": "out_of_scope",
            "retrieval": "retrieval"
        }
    )
    
    # Add edges for ABOUT_BOT and OUT_OF_SCOPE paths
    workflow.add_edge("about_bot", END)
    workflow.add_edge("out_of_scope", END)
    
    # Add edges for RAG path
    workflow.add_edge("retrieval", "rerank")
    workflow.add_edge("rerank", "generation")
    workflow.add_edge("generation", END)
    
    # Compile
    app = workflow.compile()
    
    logger.info("✅ LangGraph workflow created successfully")
    
    return app


# ==============================================================================
# VISUALIZATION (Optional)
# ==============================================================================
def visualize_graph(save_path: str = "/tmp/idin_graph.png"):
    """
    Visualize the graph structure (requires graphviz)
    """
    try:
        app = create_idin_graph()
        
        # Get mermaid diagram
        mermaid = app.get_graph().draw_mermaid()
        
        print("📊 Mermaid Diagram:")
        print(mermaid)
        
        # Try to save as image (if graphviz installed)
        try:
            img = app.get_graph().draw_mermaid_png()
            with open(save_path, "wb") as f:
                f.write(img)
            print(f"💾 Graph saved to: {save_path}")
        except Exception as e:
            print(f"⚠️  Could not save image: {e}")
            print("(Install graphviz to enable image export)")
        
    except Exception as e:
        print(f"❌ Visualization error: {e}")


if __name__ == "__main__":
    # Test graph creation
    graph = create_idin_graph()
    print("✅ Graph created successfully!")
    
    # Try visualization
    visualize_graph()
