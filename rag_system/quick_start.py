#!/usr/bin/env python3
"""
Quick Start Script for Land Department RAG

Tests all components to verify system is working
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("\n" + "=" * 80)
print("🚀 Land Department RAG System - Quick Start")
print("=" * 80)

# Test 1: Import modules
print("\n[1/4] Testing imports...")
try:
    from rag_system.rag_engine import LandDepartmentRAG
    print("✅ All modules imported successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Initialize RAG system
print("\n[2/4] Initializing RAG system...")
try:
    rag = LandDepartmentRAG()
    print("✅ RAG system initialized")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    sys.exit(1)

# Test 3: Run test query
print("\n[3/4] Running test query...")
test_queries = [
    "ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่",
    "จดทะเบียนโอนที่ดินต้องใช้เอกสารอะไรบ้าง",
]

try:
    for i, query in enumerate(test_queries, 1):
        print(f"\n  Test Query {i}: {query}")
        response = rag.query(
            query=query,
            top_k=3,
            enable_reranker=True,
            enable_context_expansion=True,
            use_llm=False,
        )
        print(f"  ✅ Retrieved {len(response.retrieved_chunks)} chunks")
        print(f"  ✅ Top score: {response.metadata['top_score']:.4f}")
        print(f"  ✅ Sources: {len(response.sources)}")
    
    print("\n✅ All test queries completed")
except Exception as e:
    print(f"❌ Query failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Display sample response
print("\n[4/4] Displaying sample response...")
try:
    print("\n" + "=" * 80)
    print("📊 Sample Response")
    print("=" * 80)
    print(rag.format_response(response, include_chunks=True, include_sources=True))
    print("\n✅ Response formatted successfully")
except Exception as e:
    print(f"❌ Display failed: {e}")
    sys.exit(1)

# Success
print("\n" + "=" * 80)
print("🎉 Quick Start Complete - All Tests Passed!")
print("=" * 80)
print("\n📖 Next Steps:")
print("  1. Run interactive chat: python rag_system/chat_interface.py")
print("  2. Start API server: python rag_system/api_server.py")
print("  3. Read documentation: rag_system/README.md")
print("\n" + "=" * 80)
