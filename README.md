# 🤖 น้องไอดิน - Land Department RAG System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0.8-green.svg)](https://github.com/langchain-ai/langgraph)
[![Qdrant](https://img.shields.io/badge/Qdrant-1.16.2-red.svg)](https://qdrant.tech/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

> Advanced RAG system for Thailand's Department of Lands, powered by LangGraph and state-of-the-art retrieval techniques.

---

## 🎯 Overview

**น้องไอดิน** is an intelligent chatbot designed to answer questions about land registration procedures, fees, and regulations in Thailand. Built with **LangGraph** for sophisticated workflow management and **Advanced Retrieval Engine** featuring:

- 🔍 **Hybrid Search**: BM25 + Dense Vector + RRF Fusion
- 🧠 **Query Analysis**: Intelligent query type detection and adaptive retrieval
- 🌳 **Context Expansion**: Hierarchical parent-child context for comprehensive answers
- 🎯 **Cross-Encoder Reranking**: BGE reranker for precision
- ⚡ **High Performance**: Average response time < 13s

---

## 🏗️ Architecture

```
rag_dol/
├── langgraph_system/          # LangGraph workflow (Production)
│   ├── api_server_langgraph.py  # FastAPI server
│   ├── graph.py                 # Workflow definition
│   ├── nodes.py                 # Node implementations
│   └── state.py                 # State management
├── src/                       # Advanced Retrieval Engine
│   ├── advanced_retrieval_engine.py  # Main engine
│   ├── bm25_indexer.py              # BM25 implementation
│   ├── embedding_engine.py           # Dense vectors (BGE-M3)
│   └── reranker.py                   # Cross-encoder reranking
├── rag_system/                # Core RAG components
│   ├── memory.py              # Conversation memory
│   └── retriever.py           # Base retriever
├── data/                      # Data and models
│   ├── คู่มือปชช.รายละเอียดเนื้อหา/  # Source documents
│   └── bm25_vocabulary.pkl    # BM25 vocabulary (8,827 terms)
├── config/                    # Configuration files
├── tests/                     # Test suites
└── archive/                   # Old files (reference only)
```

---

## ✨ Features

### 🔥 Advanced Retrieval Pipeline

1. **Query Analysis**
   - Detects query type: `document`, `section`, `mixed`
   - Identifies target hierarchy level (0-3)
   - Determines complexity for adaptive processing

2. **Hybrid Search**
   - **BM25**: Keyword matching for exact terms (e.g., "มาตรา 93", "2%")
   - **Dense Vector**: Semantic understanding with BGE-M3
   - **RRF Fusion**: Optimal combination (alpha=0.5)

3. **Reranking**
   - Cross-encoder: BGE-reranker-v2-m3
   - Scores: 0.93-0.94 for high-quality results

4. **Context Expansion**
   - Parent context from document headers
   - Child context from detailed sections
   - Hierarchical information preservation

### 🤝 LangGraph Workflow

```
┌─────────────┐
│   Router    │ ← Intelligent routing (RAG/OUT_OF_SCOPE/ABOUT_BOT)
└──────┬──────┘
       │
┌──────▼────────┐
│   Retrieval   │ ← Advanced Retrieval Engine
└──────┬────────┘
       │
┌──────▼────────┐
│   Reranking   │ ← Cross-encoder (integrated in engine)
└──────┬────────┘
       │
┌──────▼────────┐
│  Generation   │ ← LLM with full context
└───────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Qdrant running on `localhost:6333`
- Thai language support (pythainlp)

### Installation

```bash
# Clone repository
cd /Users/pond500/RAG/rag_dol

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Run Server

```bash
# Start Qdrant (if not running)
docker-compose up -d

# Start LangGraph server
uvicorn langgraph_system.api_server_langgraph:app --host 0.0.0.0 --port 8001

# Server ready at: http://localhost:8001
```

### Test

```bash
# Health check
curl http://localhost:8001/health

# Quick test
./quick_test_advanced.sh

# Full test suite (10 tests)
./test_advanced_retrieval.sh
```

---

## 📊 Performance

**Test Results: 10/10 (100%)** ✅

| Metric | Value |
|--------|-------|
| **Response Time** | 12.9s avg (σ=2.23s) |
| **Retrieval Accuracy** | 93-94% (rerank scores) |
| **Test Pass Rate** | 100% (10/10 tests) |
| **Hybrid Search** | ✅ BM25 + Dense working |
| **Query Analysis** | ✅ All types detected |
| **Context Expansion** | ✅ Parent/Child working |

---

## 🔧 Configuration

Key settings in `langgraph_system/api_server_langgraph.py`:

```python
CONFIG = {
    "llm_model": "ptm-oss-120b",
    "top_k": 10,
    "enable_reranker": True,
    "enable_context_expansion": True,
    "enable_memory": True,
    "max_history_turns": 3,
}
```

---

## 📖 API Endpoints

### `/chat` - Main Chat Interface
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ค่าธรรมเนียมโอนที่ดิน 2%",
    "session_id": "user123"
  }'
```

**Response includes:**
- `answer`: Generated response
- `chunks`: Retrieved documents with scores
- `metadata`: 
  - `query_analysis`: Query type, complexity, keywords
  - `retrieval_method`: "hybrid_rrf"
  - `chunks_count`: Number of retrieved docs

### `/health` - Health Check
```bash
curl http://localhost:8001/health
# {"status": "healthy", "langgraph": true}
```

### `/config` - Configuration
```bash
curl http://localhost:8001/config
```

### `/history/{session_id}` - Conversation History
```bash
curl http://localhost:8001/history/user123
```

---

## 🧪 Testing

### Test Suite Structure

```bash
tests/
├── test_advanced_retrieval.sh    # Main test suite (10 tests)
├── quick_test_advanced.sh        # Quick validation (3 tests)
└── run_and_test_advanced.sh      # Automated run + test
```

### Test Coverage

1. ✅ Health Check
2. ✅ Configuration validation
3. ✅ Keyword query (BM25)
4. ✅ Semantic query (Dense)
5. ✅ Procedural query
6. ✅ Context expansion
7. ✅ Hybrid vs Dense comparison
8. ✅ Complex multi-concept query
9. ✅ Performance consistency
10. ✅ Retrieval quality

---

## 📚 Documentation

- 📄 [Advanced Retrieval Upgrade Guide](./ADVANCED_RETRIEVAL_UPGRADE.md)
- 🚀 [Deployment Guide](./DEPLOYMENT.md)
- 📐 [Schema Design V2](./schema_design_v2_comprehensive.md)
- 📦 [Archive README](./archive/README.md)

---

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | LangGraph | 1.0.8 |
| **LLM** | TokenMind ptm-oss-120b | Latest |
| **Vector DB** | Qdrant | 1.16.2 |
| **Embeddings** | BAAI/bge-m3 | Latest |
| **Reranker** | BAAI/bge-reranker-v2-m3 | Latest |
| **Thai NLP** | pythainlp | 5.2.0 |
| **API** | FastAPI | Latest |

---

## 📈 System Status

**Current Status:** 🟢 **Production Ready**

- All tests passing (10/10)
- Advanced Retrieval fully integrated
- Performance optimized
- Documentation complete
- Archive cleaned up

---

## 👥 Credits

Developed for Thailand's **Department of Lands** (กรมที่ดิน)

**Project:** RAG-based Question Answering System  
**Code Name:** น้องไอดิน (Nong Aidin)  
**Last Updated:** February 18, 2026

---

## 📝 License

Internal use for Department of Lands, Thailand.

---

## 🤝 Support

For issues or questions:
1. Check [DEPLOYMENT.md](./DEPLOYMENT.md)
2. Review [ADVANCED_RETRIEVAL_UPGRADE.md](./ADVANCED_RETRIEVAL_UPGRADE.md)
3. Check test logs in `archive/logs/`

---

**Built with ❤️ using LangGraph and Advanced Retrieval Techniques**
