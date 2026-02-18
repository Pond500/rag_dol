#!/bin/bash

##############################################################################
# Run LangGraph Server with Advanced Retrieval and Test
##############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

PORT=8001
BASE_URL="http://localhost:$PORT"
SERVER_PID=""

cleanup() {
    echo ""
    echo -e "${YELLOW}Cleaning up...${NC}"
    if [ ! -z "$SERVER_PID" ]; then
        echo "Stopping server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null
        wait $SERVER_PID 2>/dev/null
    fi
    
    # Kill any remaining processes on port 8001
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    
    echo -e "${GREEN}Cleanup complete${NC}"
}

trap cleanup EXIT INT TERM

echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}  LangGraph Advanced Retrieval - Server & Test Runner${NC}"
echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port $PORT is already in use${NC}"
    echo -e "${YELLOW}Killing existing process...${NC}"
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 2
fi

# Start server
echo -e "${CYAN}🚀 Starting LangGraph server on port $PORT...${NC}"
cd /Users/pond500/RAG/rag_dol

uvicorn langgraph_system.api_server_langgraph:app --host 0.0.0.0 --port $PORT > server.log 2>&1 &
SERVER_PID=$!

echo -e "${GREEN}✅ Server started (PID: $SERVER_PID)${NC}"
echo ""

# Wait for server to be ready
echo -e "${YELLOW}⏳ Waiting for server to be ready (checking model pre-warming)...${NC}"
MAX_WAIT=60
WAIT_TIME=0
READY=false

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if curl -s "$BASE_URL/health" > /dev/null 2>&1; then
        # Check if models are warmed up
        RESPONSE=$(curl -s "$BASE_URL/health")
        STATUS=$(echo "$RESPONSE" | jq -r '.langgraph_ready' 2>/dev/null)
        
        if [ "$STATUS" = "true" ]; then
            READY=true
            break
        fi
    fi
    
    # Show progress
    echo -n "."
    sleep 2
    WAIT_TIME=$((WAIT_TIME + 2))
done

echo ""

if [ "$READY" = true ]; then
    echo -e "${GREEN}✅ Server is ready!${NC}"
    echo ""
    
    # Show server info
    echo -e "${CYAN}Server Info:${NC}"
    curl -s "$BASE_URL/" | jq '.' 2>/dev/null
    echo ""
    
    # Show config
    echo -e "${CYAN}Advanced Retrieval Configuration:${NC}"
    curl -s "$BASE_URL/config" | jq '{
        enable_hybrid_search,
        enable_query_analysis,
        enable_context_expansion,
        hybrid_alpha,
        top_k,
        rerank_top_n,
        vocabulary_size
    }' 2>/dev/null
    echo ""
    
    # Ask user if ready to test
    echo -e "${YELLOW}${BOLD}Ready to run Advanced Retrieval tests?${NC}"
    echo -e "${CYAN}This will run 10 comprehensive tests:${NC}"
    echo "  1. Health Check"
    echo "  2. Configuration Check"
    echo "  3. Keyword Query (exact matching)"
    echo "  4. Semantic Query"
    echo "  5. Procedural Query"
    echo "  6. Context Expansion"
    echo "  7. Hybrid vs Dense Comparison"
    echo "  8. Complex Query"
    echo "  9. Performance Consistency"
    echo "  10. Retrieval Quality"
    echo ""
    echo -e "${YELLOW}Press Enter to start tests, or Ctrl+C to cancel...${NC}"
    read
    
    # Run tests
    echo ""
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}  Running Tests...${NC}"
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    ./test_advanced_retrieval.sh
    TEST_EXIT_CODE=$?
    
    echo ""
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}  Test Complete${NC}"
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
    else
        echo -e "${YELLOW}⚠️  Some tests failed (see details above)${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}Server log saved to: server.log${NC}"
    echo -e "${CYAN}Test log saved to: test_advanced_retrieval_*.log${NC}"
    echo ""
    
else
    echo -e "${RED}❌ Server failed to start within ${MAX_WAIT}s${NC}"
    echo -e "${YELLOW}Check server.log for details:${NC}"
    tail -n 20 server.log
    exit 1
fi

# Keep server running
echo -e "${YELLOW}Press Enter to stop server and exit...${NC}"
read

cleanup
