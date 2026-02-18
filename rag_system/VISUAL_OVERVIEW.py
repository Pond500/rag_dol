"""
Visual Directory Tree for RAG System
"""

rag_system_tree = """
/Users/pond500/RAG/rag_dol/
│
├── rag_system/                         # 🆕 Complete RAG System
│   ├── README.md                       # 📖 Complete documentation
│   ├── SUMMARY.md                      # 📊 System summary & status
│   ├── requirements.txt                # 📦 Dependencies
│   │
│   ├── rag_engine.py                   # 🤖 Core RAG Engine
│   │   ├── LandDepartmentRAG          # Main class
│   │   ├── RAGResponse                 # Response dataclass
│   │   ├── query()                     # Main entry point
│   │   ├── _build_context()            # Context assembly
│   │   ├── _generate_answer_with_llm() # LLM integration
│   │   └── format_response()           # Display formatting
│   │
│   ├── chat_interface.py               # 💬 Interactive CLI
│   │   ├── ChatInterface               # Main class
│   │   ├── Chat history management
│   │   ├── Configuration on-the-fly
│   │   └── Command system (/help, /config, etc.)
│   │
│   ├── api_server.py                   # 🌐 REST API (FastAPI)
│   │   ├── POST /query                 # Main endpoint
│   │   ├── GET /health                 # Health check
│   │   ├── GET /config                 # Configuration
│   │   └── GET /docs                   # Auto-generated docs
│   │
│   └── quick_start.py                  # ⚡ Testing script
│       └── Automated system tests
│
├── src/                                # Core Components
│   ├── advanced_retrieval_engine.py    # ✅ Multi-stage retrieval
│   ├── embedding_engine.py             # ✅ BGE-M3 embeddings
│   ├── bm25_indexer.py                 # ✅ Thai BM25
│   ├── reranker.py                     # ✅ BGE-reranker
│   ├── chunking_engine.py              # ✅ Hierarchical chunking
│   ├── metadata_extractor.py           # ✅ Metadata extraction
│   ├── hybrid_etl_pipeline.py          # ✅ ETL pipeline
│   └── qdrant_hybrid_setup.py          # ✅ Qdrant setup
│
├── data/                               # Data Files
│   ├── bm25_vocabulary.pkl             # ✅ 8,827 terms
│   └── คู่มือปชช.รายละเอียดเนื้อหา/   # ✅ 108 documents
│
├── docs/                               # Documentation
│   ├── advanced_retrieval_engine_guide.md
│   ├── chunking_benefits_for_retrieval.md
│   └── ...
│
└── examples/                           # Examples & Tests
    ├── simple_test.py
    ├── test_rag_simple.py
    └── ...
"""

print(rag_system_tree)

# Feature Summary
feature_summary = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    🎉 RAG SYSTEM FEATURES 🎉
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ RETRIEVAL (Advanced Multi-Stage)
   ├─ Hybrid Search: BM25 + BGE-M3 Dense
   ├─ RRF Fusion: Reciprocal Rank Fusion
   ├─ Adaptive Strategy: Auto-select level (0/1/2)
   ├─ Reranking: BGE-reranker-v2-m3
   └─ Context Expansion: Parent + Children + Siblings

✅ RAG PIPELINE
   ├─ Query Analysis: Intent detection
   ├─ Context Building: Smart assembly
   ├─ LLM Integration: Ready (placeholder)
   └─ Source Citation: Automatic tracking

✅ USER INTERFACES
   ├─ Chat CLI: Interactive with history
   ├─ Python API: Programmatic access
   ├─ REST API: HTTP endpoints (FastAPI)
   └─ Documentation: Complete guides

✅ DATA LAYER
   ├─ Qdrant: 3,704 chunks indexed
   ├─ BM25: 8,827 Thai terms
   ├─ Embeddings: BGE-M3 (1024 dims)
   └─ Hierarchical: 3-level structure

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

print(feature_summary)

# Quick Commands
quick_commands = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                      🚀 QUICK START COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  INTERACTIVE CHAT (แนะนำสำหรับผู้ใช้ทั่วไป)
    cd /Users/pond500/RAG/rag_dol
    .venv/bin/python rag_system/chat_interface.py

2️⃣  PYTHON API (สำหรับ Developer)
    from rag_system.rag_engine import LandDepartmentRAG
    rag = LandDepartmentRAG()
    response = rag.query("ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่")

3️⃣  REST API SERVER (สำหรับ Web/Mobile Integration)
    pip install fastapi uvicorn
    .venv/bin/python rag_system/api_server.py
    # API: http://localhost:8000

4️⃣  TESTING (ทดสอบระบบ)
    .venv/bin/python test_rag_simple.py
    .venv/bin/python rag_system/quick_start.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

print(quick_commands)

# Performance Stats
performance = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    📊 PERFORMANCE METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Retrieval Quality:
  • Precision@5:  0.92 (Full Pipeline)
  • MRR:          0.95
  • Top-1 Acc:    ~90%

Response Time:
  • Hybrid Only:     ~300ms  ⚡
  • + Reranker:      ~600ms  ⚡⚡
  • + Context:       ~650ms  ⚡⚡
  • + LLM (future):  +2-10s  🤖

Database:
  • Documents:    108
  • Chunks:       3,704
  • Vocabulary:   8,827 terms
  • Avg/Doc:      34.3 chunks

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

print(performance)
