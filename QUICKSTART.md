# 🚀 Quick Reference Guide

## Fast Commands

### Start Server
```bash
uvicorn langgraph_system.api_server_langgraph:app --host 0.0.0.0 --port 8001
```

### Test
```bash
# Quick test (3 tests)
./quick_test_advanced.sh

# Full test suite (10 tests)
./test_advanced_retrieval.sh

# Automated (start + test)
./run_and_test_advanced.sh
```

### Query
```bash
# Simple query
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "ค่าธรรมเนียมโอนที่ดิน", "session_id": "test"}'

# Health check
curl http://localhost:8001/health
```

---

## Key Files

| File | Purpose |
|------|---------|
| `langgraph_system/api_server_langgraph.py` | Main server |
| `langgraph_system/nodes.py` | Workflow nodes |
| `src/advanced_retrieval_engine.py` | Retrieval engine |
| `test_advanced_retrieval.sh` | Main test suite |
| `README.md` | Complete documentation |

---

## Endpoints

- `POST /chat` - Chat with AI
- `GET /health` - Health check
- `GET /config` - Configuration
- `GET /history/{session_id}` - Chat history
- `GET /sessions` - List sessions
- `DELETE /session/{session_id}` - Delete session

---

## Troubleshooting

### Server won't start
```bash
# Check if Qdrant is running
curl http://localhost:6333

# Start Qdrant
docker-compose up -d
```

### Slow responses
- Model loading takes ~20-25s on first query
- Subsequent queries: ~13s average
- Check server logs: `tail -f server_final_fixed.log`

### Tests failing
```bash
# Restart server
pkill -9 -f "uvicorn.*8001"
uvicorn langgraph_system.api_server_langgraph:app --host 0.0.0.0 --port 8001

# Wait 25s for models to load
sleep 25

# Run tests
./test_advanced_retrieval.sh
```

---

## Project Structure

```
rag_dol/
├── langgraph_system/    ← Production LangGraph code
├── src/                 ← Advanced Retrieval Engine
├── rag_system/          ← Base RAG components
├── data/                ← Documents + BM25 vocab
├── tests/               ← Test scripts
└── archive/             ← Old files (reference)
```

---

## Environment Variables

Copy `.env.example` to `.env` and set:

```bash
TOKENMIND_API_KEY=your_key_here
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

## Archive

Old files are in `archive/`:
- `logs/` - Old test/server logs
- `old_tests/` - Legacy test scripts
- `old_docs/` - Previous documentation
- `old_scripts/` - Deprecated utilities

**Note:** Don't delete archive - it's for reference and rollback if needed.

---

## Performance Benchmarks

| Metric | Target | Current |
|--------|--------|---------|
| Response Time | <15s | 12.9s ✅ |
| Test Pass Rate | >90% | 100% ✅ |
| Rerank Score | >0.9 | 0.93-0.94 ✅ |

---

## Support Checklist

- [ ] Check `README.md` for full documentation
- [ ] Review `DEPLOYMENT.md` for deployment guide
- [ ] See `ADVANCED_RETRIEVAL_UPGRADE.md` for technical details
- [ ] Check server logs if issues persist
- [ ] Review test results in `archive/logs/`

---

**Last Updated:** February 18, 2026  
**Status:** Production Ready 🟢
