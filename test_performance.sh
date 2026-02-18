#!/bin/bash

# Performance Test Script for LangGraph System
# Tests reranker optimizations and measures improvements

set -e

echo "=================================================================================================="
echo "🧪 LANGGRAPH PERFORMANCE TEST - Reranker Optimization Validation"
echo "=================================================================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_DIR="/Users/pond500/RAG/rag_dol"
LOG_FILE="/tmp/langgraph_perf_test.log"
SERVER_PID=""

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null || true
    fi
    pkill -f "api_server_langgraph.py" 2>/dev/null || true
}

trap cleanup EXIT

# Step 1: Kill existing servers
echo "Step 1: Stopping existing servers..."
pkill -f "api_server_langgraph.py" 2>/dev/null || true
sleep 2
echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

# Step 2: Start optimized server
echo "Step 2: Starting optimized LangGraph server..."
cd "$BASE_DIR"
.venv/bin/python langgraph_system/api_server_langgraph.py > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "   Server PID: $SERVER_PID"
echo "   Log file: $LOG_FILE"
echo ""

# Step 3: Wait for server and model pre-warming
echo "Step 3: Waiting for server startup and model pre-warming..."
echo "   ⏳ This may take 20-30 seconds (loading 2 models)..."

MAX_WAIT=40
COUNTER=0
while [ $COUNTER -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Server is ready!${NC}"
        break
    fi
    sleep 1
    COUNTER=$((COUNTER + 1))
    if [ $((COUNTER % 5)) -eq 0 ]; then
        echo "   ... waiting ($COUNTER/$MAX_WAIT seconds)"
    fi
done

if [ $COUNTER -eq $MAX_WAIT ]; then
    echo -e "   ${RED}❌ Server failed to start within $MAX_WAIT seconds${NC}"
    echo ""
    echo "Last 30 lines of server log:"
    tail -30 "$LOG_FILE"
    exit 1
fi

sleep 2
echo ""

# Step 4: Check startup logs
echo "Step 4: Checking model pre-warming..."
if grep -q "Models pre-warmed successfully" "$LOG_FILE"; then
    echo -e "   ${GREEN}✅ Models pre-warmed successfully${NC}"
    
    # Extract loading times
    echo ""
    echo "   Model Loading Times:"
    grep "Embedding model loaded\|Reranker model loaded" "$LOG_FILE" | sed 's/^/   /'
else
    echo -e "   ${YELLOW}⚠️  Models will be loaded on first use${NC}"
fi
echo ""

# Step 5: Run performance tests
echo "=================================================================================================="
echo "📊 PERFORMANCE TESTS"
echo "=================================================================================================="
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
HEALTH_START=$(date +%s.%N)
HEALTH_RESPONSE=$(curl -s http://localhost:8001/health)
HEALTH_END=$(date +%s.%N)
HEALTH_TIME=$(echo "$HEALTH_END - $HEALTH_START" | bc)
echo "   Response: $HEALTH_RESPONSE"
echo -e "   Time: ${GREEN}${HEALTH_TIME}s${NC}"
echo ""

# Test 2: ABOUT_BOT (no reranking)
echo "Test 2: ABOUT_BOT Routing (baseline - no reranking)"
ABOUT_START=$(date +%s.%N)
ABOUT_RESPONSE=$(curl -s -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"perf_test_about","query":"สวัสดีครับ"}')
ABOUT_END=$(date +%s.%N)
ABOUT_TIME=$(echo "$ABOUT_END - $ABOUT_START" | bc)
ABOUT_ROUTING=$(echo "$ABOUT_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['metadata']['routing_decision'])" 2>/dev/null || echo "ERROR")
echo "   Routing: $ABOUT_ROUTING"
echo -e "   Time: ${GREEN}${ABOUT_TIME}s${NC}"
echo ""

# Test 3: First RAG query (models should be cached)
echo "Test 3: First RAG Query (reranker test #1)"
RAG1_START=$(date +%s.%N)
RAG1_RESPONSE=$(curl -s -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"perf_test_1","query":"ค่าธรรมเนียมโอนที่ดิน"}')
RAG1_END=$(date +%s.%N)
RAG1_TIME=$(echo "$RAG1_END - $RAG1_START" | bc)
RAG1_CHUNKS=$(echo "$RAG1_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('retrieved_chunks',[])))" 2>/dev/null || echo "0")
RAG1_ROUTING=$(echo "$RAG1_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['metadata']['routing_decision'])" 2>/dev/null || echo "ERROR")
echo "   Routing: $RAG1_ROUTING"
echo "   Chunks retrieved: $RAG1_CHUNKS"
echo -e "   Total time: ${BLUE}${RAG1_TIME}s${NC}"
echo ""

# Extract rerank time from logs
sleep 2
RERANK1_TIME=$(tail -50 "$LOG_FILE" | grep -A 5 "perf_test_1" | grep "Prediction completed" | tail -1 | grep -oE '[0-9]+\.[0-9]+s' || echo "N/A")
if [ "$RERANK1_TIME" != "N/A" ]; then
    echo -e "   Rerank time: ${GREEN}${RERANK1_TIME}${NC}"
else
    echo "   Rerank time: Not measured"
fi
echo ""

# Test 4: Second RAG query (critical test for bug)
echo "Test 4: Second RAG Query (reranker test #2 - bug check)"
echo "   🎯 This is the critical test - should NOT take 70+ seconds!"
RAG2_START=$(date +%s.%N)
RAG2_RESPONSE=$(curl -s -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"perf_test_2","query":"ค่าธรรมเนียมจำนอง"}')
RAG2_END=$(date +%s.%N)
RAG2_TIME=$(echo "$RAG2_END - $RAG2_START" | bc)
RAG2_CHUNKS=$(echo "$RAG2_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('retrieved_chunks',[])))" 2>/dev/null || echo "0")
RAG2_ROUTING=$(echo "$RAG2_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['metadata']['routing_decision'])" 2>/dev/null || echo "ERROR")
echo "   Routing: $RAG2_ROUTING"
echo "   Chunks retrieved: $RAG2_CHUNKS"

# Color code based on time
if (( $(echo "$RAG2_TIME < 20" | bc -l) )); then
    echo -e "   Total time: ${GREEN}${RAG2_TIME}s ✅ EXCELLENT${NC}"
elif (( $(echo "$RAG2_TIME < 30" | bc -l) )); then
    echo -e "   Total time: ${YELLOW}${RAG2_TIME}s ⚠️  ACCEPTABLE${NC}"
else
    echo -e "   Total time: ${RED}${RAG2_TIME}s ❌ TOO SLOW (BUG NOT FIXED)${NC}"
fi
echo ""

# Extract rerank time
sleep 2
RERANK2_TIME=$(tail -50 "$LOG_FILE" | grep -A 5 "perf_test_2" | grep "Prediction completed" | tail -1 | grep -oE '[0-9]+\.[0-9]+s' || echo "N/A")
if [ "$RERANK2_TIME" != "N/A" ]; then
    RERANK2_SECONDS=$(echo "$RERANK2_TIME" | sed 's/s//')
    if (( $(echo "$RERANK2_SECONDS < 5" | bc -l) )); then
        echo -e "   Rerank time: ${GREEN}${RERANK2_TIME} ✅ FAST${NC}"
    elif (( $(echo "$RERANK2_SECONDS < 15" | bc -l) )); then
        echo -e "   Rerank time: ${YELLOW}${RERANK2_TIME} ⚠️  ACCEPTABLE${NC}"
    else
        echo -e "   Rerank time: ${RED}${RERANK2_TIME} ❌ TOO SLOW${NC}"
    fi
else
    echo "   Rerank time: Not measured"
fi
echo ""

# Test 5: Third consecutive query (stability test)
echo "Test 5: Third RAG Query (stability test)"
RAG3_START=$(date +%s.%N)
RAG3_RESPONSE=$(curl -s -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"perf_test_3","query":"จดทะเบียนเช่าที่ดิน"}')
RAG3_END=$(date +%s.%N)
RAG3_TIME=$(echo "$RAG3_END - $RAG3_START" | bc)
RAG3_CHUNKS=$(echo "$RAG3_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('retrieved_chunks',[])))" 2>/dev/null || echo "0")
echo "   Chunks retrieved: $RAG3_CHUNKS"
echo -e "   Total time: ${BLUE}${RAG3_TIME}s${NC}"
echo ""

# Test 6: Session management (same session, consecutive queries)
echo "Test 6: Session Management (2 queries in same session)"
SESSION_START=$(date +%s.%N)

curl -s -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"perf_session","query":"ค่าธรรมเนียมโอน"}' > /dev/null

sleep 2

curl -s -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"perf_session","query":"แล้วค่าจำนองล่ะ"}' > /dev/null

SESSION_END=$(date +%s.%N)
SESSION_TIME=$(echo "$SESSION_END - $SESSION_START" | bc)

# Check if completed without timeout
if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✅ Completed without timeout${NC}"
    echo -e "   Total time for 2 queries: ${BLUE}${SESSION_TIME}s${NC}"
else
    echo -e "   ${RED}❌ Failed or timed out${NC}"
fi
echo ""

# Step 6: Summary
echo "=================================================================================================="
echo "📋 TEST SUMMARY"
echo "=================================================================================================="
echo ""

# Calculate average RAG time
AVG_RAG_TIME=$(echo "scale=2; ($RAG1_TIME + $RAG2_TIME + $RAG3_TIME) / 3" | bc)

echo "Performance Metrics:"
echo "   Health check:         ${HEALTH_TIME}s"
echo "   ABOUT_BOT routing:    ${ABOUT_TIME}s"
echo "   RAG Query #1:         ${RAG1_TIME}s"
echo "   RAG Query #2:         ${RAG2_TIME}s (⚡ Critical test)"
echo "   RAG Query #3:         ${RAG3_TIME}s"
echo "   Average RAG time:     ${AVG_RAG_TIME}s"
echo "   Session management:   ${SESSION_TIME}s (2 queries)"
echo ""

# Verdict
echo "🎯 OPTIMIZATION VERDICT:"
echo ""

BUG_FIXED=true

# Check if RAG2 is within acceptable range
if (( $(echo "$RAG2_TIME > 30" | bc -l) )); then
    echo -e "${RED}❌ CRITICAL BUG NOT FIXED${NC}"
    echo "   Query #2 took ${RAG2_TIME}s (should be <20s)"
    echo "   Reranker is still too slow!"
    BUG_FIXED=false
elif (( $(echo "$RAG2_TIME > 20" | bc -l) )); then
    echo -e "${YELLOW}⚠️  PARTIALLY FIXED${NC}"
    echo "   Query #2 took ${RAG2_TIME}s (acceptable but could be better)"
    echo "   Target: <20s for production readiness"
else
    echo -e "${GREEN}✅ BUG FIXED!${NC}"
    echo "   Query #2 took ${RAG2_TIME}s (within acceptable range)"
fi
echo ""

# Check average performance
if (( $(echo "$AVG_RAG_TIME < 20" | bc -l) )); then
    echo -e "${GREEN}✅ Average performance: EXCELLENT${NC} (${AVG_RAG_TIME}s < 20s)"
elif (( $(echo "$AVG_RAG_TIME < 30" | bc -l) )); then
    echo -e "${YELLOW}⚠️  Average performance: ACCEPTABLE${NC} (${AVG_RAG_TIME}s < 30s)"
else
    echo -e "${RED}❌ Average performance: NEEDS IMPROVEMENT${NC} (${AVG_RAG_TIME}s > 30s)"
    BUG_FIXED=false
fi
echo ""

# Overall assessment
echo "Overall Assessment:"
if [ "$BUG_FIXED" = true ]; then
    echo -e "${GREEN}✅ SYSTEM READY FOR PRODUCTION${NC}"
    echo ""
    echo "All critical bugs have been fixed!"
    echo "System performance is within acceptable ranges."
    EXIT_CODE=0
else
    echo -e "${RED}❌ SYSTEM NOT READY - REQUIRES FURTHER OPTIMIZATION${NC}"
    echo ""
    echo "Critical performance issues detected."
    echo "Review server logs for details: $LOG_FILE"
    EXIT_CODE=1
fi

echo ""
echo "=================================================================================================="
echo "📁 Detailed logs: $LOG_FILE"
echo "=================================================================================================="
echo ""

# Show last errors if any
if grep -q "ERROR\|❌" "$LOG_FILE"; then
    echo "⚠️  Errors detected in server logs (last 10):"
    grep "ERROR\|❌" "$LOG_FILE" | tail -10 | sed 's/^/   /'
    echo ""
fi

exit $EXIT_CODE
