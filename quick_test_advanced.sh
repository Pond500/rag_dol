#!/bin/bash

##############################################################################
# Quick Test - Advanced Retrieval Features
# รันทดสอบแบบด่วน 3 คำถาม เพื่อดู Hybrid, Query Analysis, Context Expansion
##############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

BASE_URL="http://localhost:8001"

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}${BOLD}  $1${NC}"
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

test_query() {
    local query="$1"
    local test_name="$2"
    local check_for="$3"
    
    print_header "$test_name"
    
    echo -e "${YELLOW}Query:${NC} \"$query\""
    echo -e "${CYAN}Testing:${NC} $check_for"
    echo ""
    
    start_time=$(date +%s.%N)
    response=$(curl -s -X POST "$BASE_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"$query\",
            \"session_id\": \"quicktest_$(date +%s)\"
        }")
    end_time=$(date +%s.%N)
    elapsed=$(echo "$end_time - $start_time" | bc)
    
    # Extract data
    answer=$(echo "$response" | jq -r '.answer' 2>/dev/null)
    metadata=$(echo "$response" | jq '.metadata' 2>/dev/null)
    chunks=$(echo "$response" | jq '.chunks' 2>/dev/null)
    
    # Show metadata
    echo -e "${MAGENTA}📊 Metadata:${NC}"
    echo "$metadata" | jq '{
        query_analysis: .query_analysis,
        retrieval_method: .retrieval_method,
        handler: .handler
    }' 2>/dev/null
    echo ""
    
    # Show retrieval details
    echo -e "${MAGENTA}🔍 Retrieval Details (Top 3):${NC}"
    for i in 0 1 2; do
        score=$(echo "$chunks" | jq -r ".[$i].score" 2>/dev/null)
        bm25=$(echo "$chunks" | jq -r ".[$i].bm25_score" 2>/dev/null)
        dense=$(echo "$chunks" | jq -r ".[$i].dense_score" 2>/dev/null)
        rerank=$(echo "$chunks" | jq -r ".[$i].rerank_score" 2>/dev/null)
        section=$(echo "$chunks" | jq -r ".[$i].section_title" 2>/dev/null)
        has_parent=$(echo "$chunks" | jq -r ".[$i].parent_text" 2>/dev/null)
        
        if [ "$score" != "null" ]; then
            echo "  Chunk $((i+1)):"
            echo "    - Section: $section"
            echo "    - Final Score: $score"
            [ "$bm25" != "null" ] && echo "    - BM25: $bm25"
            [ "$dense" != "null" ] && echo "    - Dense: $dense"
            [ "$rerank" != "null" ] && echo "    - Rerank: $rerank"
            [ "$has_parent" != "null" ] && [ "$has_parent" != "" ] && echo "    - Has Parent Context: ✅"
        fi
    done
    echo ""
    
    # Show answer
    echo -e "${GREEN}💬 Answer:${NC}"
    echo "$answer" | head -n 20
    echo ""
    
    echo -e "${CYAN}⏱️  Response Time: ${BOLD}${elapsed}s${NC}"
    echo ""
}

# Main
clear

print_header "🧪 Quick Test - Advanced Retrieval Features"

# Check server
echo -e "${YELLOW}Checking server...${NC}"
if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Server not running on $BASE_URL${NC}"
    echo -e "${YELLOW}Start server first:${NC}"
    echo "  cd /Users/pond500/RAG/rag_dol"
    echo "  uvicorn langgraph_system.api_server_langgraph:app --port 8001"
    exit 1
fi
echo -e "${GREEN}✅ Server is running${NC}"
echo ""

# Test 1: Keyword Query (BM25 should shine)
test_query \
    "ค่าธรรมเนียมโอนที่ดิน 2%" \
    "TEST 1: Keyword Query - Exact Matching" \
    "BM25 Score should be high for exact keyword '2%'"

# Test 2: Procedural Query (Query Analysis)
test_query \
    "ขั้นตอนการจดทะเบียนโอนที่ดินมีอะไรบ้าง" \
    "TEST 2: Procedural Query - Query Analysis" \
    "Query type should be 'document' or 'mixed', target_level should be detected"

# Test 3: Context Expansion
test_query \
    "เอกสารที่ใช้จดทะเบียนจำนอง" \
    "TEST 3: Context Expansion - Parent/Child" \
    "Chunks should have parent_text or children_texts"

# Summary
print_header "✅ Quick Test Complete"

echo -e "${CYAN}What to look for:${NC}"
echo ""
echo -e "${YELLOW}1. Hybrid Search (BM25 + Dense):${NC}"
echo "   - Check if chunks have both bm25_score and dense_score"
echo "   - BM25 should be higher for exact keyword matches"
echo ""
echo -e "${YELLOW}2. Query Analysis:${NC}"
echo "   - metadata.query_analysis should show query_type and target_level"
echo "   - Different queries should be classified differently"
echo ""
echo -e "${YELLOW}3. Context Expansion:${NC}"
echo "   - Some chunks should have 'Has Parent Context: ✅'"
echo "   - This gives additional hierarchical context"
echo ""

echo -e "${GREEN}${BOLD}If you see all 3 features working → Advanced Retrieval is ACTIVE! 🎉${NC}"
echo ""
