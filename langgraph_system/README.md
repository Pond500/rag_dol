# น้องไอดิน - LangGraph Edition

## 🎯 Overview

นี่คือ **เวอร์ชัน LangGraph** ของระบบ RAG น้องไอดิน สำหรับกรมที่ดิน สร้างขึ้นใหม่ทั้งหมดโดยใช้ **LangGraph framework** แทน LlamaIndex

## 🏗️ Architecture

```
LangGraph Workflow:
┌─────────┐
│  START  │
└────┬────┘
     │
     ▼
┌─────────┐
│ ROUTER  │ (classify intent)
└────┬────┘
     │
     ├──────┬──────────┬──────────┐
     │      │          │          │
     ▼      ▼          ▼          ▼
┌──────┐ ┌────┐  ┌──────────┐  ┌────────┐
│ABOUT │ │OUT │  │RETRIEVAL │  │  RAG   │
│ BOT  │ │OF  │  │   NODE   │  │ PATH   │
└──┬───┘ │SCOPE│ └────┬─────┘  └────────┘
   │     └─┬──┘       │
   │       │          ▼
   │       │     ┌─────────┐
   │       │     │ RERANK  │
   │       │     └────┬────┘
   │       │          │
   │       │          ▼
   │       │     ┌──────────┐
   │       │     │GENERATION│
   │       │     └────┬─────┘
   │       │          │
   └───────┴──────────┴──────▶ END
```

## 📁 Structure

```
langgraph_system/
├── __init__.py              # Package initialization
├── state.py                 # State definition (ChatState)
├── nodes.py                 # All node functions
├── graph.py                 # Workflow definition
├── api_server_langgraph.py  # FastAPI server
└── README.md                # This file
```

## 🚀 Quick Start

### 1. Start Server

```bash
# Port 8001 (different from original)
python langgraph_system/api_server_langgraph.py
```

### 2. Test Endpoints

```bash
# Health check
curl http://localhost:8001/health

# Chat - ABOUT_BOT
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test1","query":"สวัสดีครับ"}'

# Chat - OUT_OF_SCOPE
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test2","query":"สอนทำอาหาร"}'

# Chat - RAG
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test3","query":"ค่าธรรมเนียมโอนที่ดิน"}'

# Get history
curl http://localhost:8001/history/test1

# List sessions
curl http://localhost:8001/sessions
```

## 🔑 Key Features

### ✅ **LangGraph Benefits**

1. **State Management** - Built-in state tracking
2. **Visual Workflow** - Can visualize graph structure
3. **Conditional Routing** - Easy branching logic
4. **Checkpointing** - Can save/restore state (future enhancement)
5. **Streaming Support** - Native async/streaming support
6. **Human-in-the-Loop** - Can add approval nodes (future)

### ✅ **Current Capabilities**

- ✅ 3-way routing (RAG, OUT_OF_SCOPE, ABOUT_BOT)
- ✅ Qdrant integration for retrieval
- ✅ CrossEncoder reranking
- ✅ LLM generation with context
- ✅ Session management
- ✅ Conversation memory
- ✅ Comprehensive logging

## 📊 Comparison: LlamaIndex vs LangGraph

| Feature | LlamaIndex (Original) | LangGraph (New) |
|---------|----------------------|-----------------|
| **Framework** | LlamaIndex | LangGraph |
| **Routing** | Custom function | State machine nodes |
| **State Management** | Manual | Built-in |
| **Visualization** | None | Mermaid diagrams |
| **Retrieval** | LlamaIndex | Qdrant direct |
| **Reranking** | CrossEncoder | CrossEncoder |
| **LLM** | OpenAI-like | LangChain OpenAI |
| **Memory** | Custom | Reused from original |
| **Complexity** | Medium | Higher |
| **Flexibility** | Good | Excellent |
| **Port** | 8000 | 8001 |

## 🔧 Configuration

Edit in `api_server_langgraph.py`:

```python
CONFIG = {
    "llm_model": "ptm-oss-120b",
    "llm_api_base": "https://tokenmind.abdul.in.th/v1",
    "llm_api_key": "sk-driylW9kC_SdAaHEl3350g",
    "llm_temperature": 0.5,
    "qdrant_host": "localhost",
    "qdrant_port": 6333,
    "qdrant_collection": "dopa_v2",
    "top_k": 10,
    "enable_reranker": True,
}
```

## 🧪 Testing

### Test Graph Creation

```python
from langgraph_system.graph import create_idin_graph

# Create graph
graph = create_idin_graph()

# Visualize (requires graphviz)
from langgraph_system.graph import visualize_graph
visualize_graph()
```

### Test Individual Nodes

```python
from langgraph_system.nodes import router_node
from langgraph_system.state import create_initial_state

# Create state
state = create_initial_state(
    query="ค่าธรรมเนียมโอนที่ดิน",
    session_id="test",
    chat_history=[]
)

# Test router
config = {"llm_model": "...", ...}
result = await router_node(state, config)
print(result['routing_decision'])  # Should be 'RAG'
```

## 📝 API Endpoints

### Core Endpoints

- `GET /` - Root info
- `GET /health` - Health check
- `POST /chat` - Main chat endpoint
- `GET /history/{session_id}` - Get history
- `GET /sessions` - List all sessions
- `DELETE /session/{session_id}` - Delete session
- `GET /config` - Get configuration

### Response Format

```json
{
  "session_id": "test1",
  "query": "ค่าธรรมเนียมโอนที่ดิน",
  "answer": "...",
  "sources": [...],
  "retrieved_chunks": [...],
  "metadata": {
    "routing_decision": "RAG",
    "framework": "langgraph",
    "workflow_steps": 5
  },
  "time_seconds": "2.5s",
  "status": "completed"
}
```

## 🎓 Learning Resources

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangChain Docs](https://python.langchain.com/)
- [State Machines](https://en.wikipedia.org/wiki/Finite-state_machine)

## 🔮 Future Enhancements

- [ ] Streaming responses
- [ ] Checkpointing (save/restore state)
- [ ] Human-in-the-loop nodes
- [ ] Multi-agent collaboration
- [ ] Enhanced error handling
- [ ] Retry logic with exponential backoff
- [ ] Observability with LangSmith
- [ ] A/B testing different prompts

## 📄 License

Internal use for Land Department

## 👥 Authors

RAG Development Team - Land Department

---

**Version:** 3.0.0-langgraph  
**Framework:** LangGraph + LangChain  
**Created:** February 2026
