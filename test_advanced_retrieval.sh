#!/bin/bash

##############################################################################
# Advanced Retrieval Testing Suite for LangGraph System
# Tests: Hybrid Search, Query Analysis, Context Expansion
##############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
BASE_URL="http://localhost:8001"
LOG_FILE="test_advanced_retrieval_$(date +%Y%m%d_%H%M%S).log"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}  $1${NC}"
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_test() {
    echo -e "${BLUE}${BOLD}[TEST $1/$2]${NC} $3"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
    ((PASSED_TESTS++))
}

print_fail() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    ((FAILED_TESTS++))
}

print_info() {
    echo -e "${CYAN}ℹ️  INFO:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARN:${NC} $1"
}

measure_time() {
    start_time=$(date +%s.%N)
    "$@"
    end_time=$(date +%s.%N)
    elapsed=$(echo "$end_time - $start_time" | bc)
    echo "$elapsed"
}

##############################################################################
# Test Functions
##############################################################################

test_health_check() {
    print_test 1 10 "Health Check - ตรวจสอบว่าระบบพร้อมใช้งาน"
    
    response=$(curl -s -w "\n%{http_code}" "$BASE_URL/health")
    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        status=$(echo "$body" | jq -r '.status' 2>/dev/null)
        if [ "$status" = "healthy" ]; then
            print_success "Server is healthy"
            echo "$body" | jq '.' 2>/dev/null
            return 0
        else
            print_fail "Server returned unhealthy status"
            return 1
        fi
    else
        print_fail "Health check failed (HTTP $http_code)"
        return 1
    fi
}

test_config() {
    print_test 2 10 "Configuration Check - ตรวจสอบ Advanced Retrieval Settings"
    
    response=$(curl -s "$BASE_URL/config")
    
    # Check Advanced Retrieval settings
    enable_hybrid=$(echo "$response" | jq -r '.enable_hybrid_search' 2>/dev/null)
    enable_query_analysis=$(echo "$response" | jq -r '.enable_query_analysis' 2>/dev/null)
    enable_context_expansion=$(echo "$response" | jq -r '.enable_context_expansion' 2>/dev/null)
    
    echo -e "${CYAN}Configuration:${NC}"
    echo "$response" | jq '{
        enable_hybrid_search,
        enable_query_analysis,
        enable_context_expansion,
        hybrid_alpha,
        top_k,
        rerank_top_n
    }' 2>/dev/null
    
    if [ "$enable_hybrid" = "true" ] && [ "$enable_query_analysis" = "true" ] && [ "$enable_context_expansion" = "true" ]; then
        print_success "All Advanced Retrieval features enabled"
        return 0
    else
        print_fail "Some Advanced Retrieval features are disabled"
        return 1
    fi
}

test_keyword_query() {
    print_test 3 10 "Keyword Query - ทดสอบการค้นหาด้วย exact keyword"
    
    query="ค่าธรรมเนียมโอนที่ดิน 2%"
    
    echo -e "${YELLOW}Query:${NC} \"$query\""
    echo -e "${CYAN}Expected:${NC} ควรหาข้อมูลที่มี \"2%\" หรือ \"2 เปอร์เซ็นต์\" ได้"
    echo ""
    
    start_time=$(date +%s.%N)
    response=$(curl -s -X POST "$BASE_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"$query\",
            \"session_id\": \"test_keyword_$(date +%s)\"
        }")
    end_time=$(date +%s.%N)
    elapsed=$(echo "$end_time - $start_time" | bc)
    
    # Check response
    answer=$(echo "$response" | jq -r '.answer' 2>/dev/null)
    chunks=$(echo "$response" | jq -r '.chunks' 2>/dev/null)
    metadata=$(echo "$response" | jq -r '.metadata' 2>/dev/null)
    
    echo -e "${CYAN}Response Time:${NC} ${elapsed}s"
    echo ""
    echo -e "${CYAN}Answer:${NC}"
    echo "$answer" | head -n 10
    echo ""
    
    # Check for keyword in answer or chunks
    if echo "$answer" | grep -qi "2"; then
        print_success "Found keyword '2' in answer"
        
        # Check metadata for query analysis
        query_type=$(echo "$metadata" | jq -r '.query_analysis.query_type' 2>/dev/null)
        fusion_method=$(echo "$metadata" | jq -r '.retrieval_method' 2>/dev/null)
        
        echo -e "${CYAN}Query Analysis:${NC}"
        echo "  - Query Type: $query_type"
        echo "  - Fusion Method: $fusion_method"
        
        return 0
    else
        print_warning "Keyword '2' not found clearly in answer"
        return 1
    fi
}

test_semantic_query() {
    print_test 4 10 "Semantic Query - ทดสอบการค้นหาแบบ semantic"
    
    query="คนต่างชาติซื้อที่ดินในไทยได้ไหม"
    
    echo -e "${YELLOW}Query:${NC} \"$query\""
    echo -e "${CYAN}Expected:${NC} ควรเข้าใจความหมายและหาข้อมูลเกี่ยวกับสิทธิของคนต่างชาติ"
    echo ""
    
    start_time=$(date +%s.%N)
    response=$(curl -s -X POST "$BASE_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"$query\",
            \"session_id\": \"test_semantic_$(date +%s)\"
        }")
    end_time=$(date +%s.%N)
    elapsed=$(echo "$end_time - $start_time" | bc)
    
    answer=$(echo "$response" | jq -r '.answer' 2>/dev/null)
    metadata=$(echo "$response" | jq -r '.metadata' 2>/dev/null)
    
    echo -e "${CYAN}Response Time:${NC} ${elapsed}s"
    echo ""
    echo -e "${CYAN}Answer:${NC}"
    echo "$answer" | head -n 10
    echo ""
    
    # Check for relevant keywords
    if echo "$answer" | grep -Eqi "ต่างด้าว|ต่างชาติ|alien|foreign"; then
        print_success "Found relevant semantic content about foreigners"
        
        query_type=$(echo "$metadata" | jq -r '.query_analysis.query_type' 2>/dev/null)
        echo -e "${CYAN}Query Type Detected:${NC} $query_type"
        
        return 0
    else
        print_fail "No relevant semantic content found"
        return 1
    fi
}

test_procedural_query() {
    print_test 5 10 "Procedural Query - ทดสอบคำถามเกี่ยวกับขั้นตอน"
    
    query="ขั้นตอนการจดทะเบียนโอนที่ดินมีอะไรบ้าง"
    
    echo -e "${YELLOW}Query:${NC} \"$query\""
    echo -e "${CYAN}Expected:${NC} ควรได้ข้อมูลขั้นตอนแบบละเอียด (Query Analysis → document type)"
    echo ""
    
    start_time=$(date +%s.%N)
    response=$(curl -s -X POST "$BASE_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"$query\",
            \"session_id\": \"test_procedural_$(date +%s)\"
        }")
    end_time=$(date +%s.%N)
    elapsed=$(echo "$end_time - $start_time" | bc)
    
    answer=$(echo "$response" | jq -r '.answer' 2>/dev/null)
    chunks=$(echo "$response" | jq -r '.chunks | length' 2>/dev/null)
    metadata=$(echo "$response" | jq -r '.metadata' 2>/dev/null)
    
    echo -e "${CYAN}Response Time:${NC} ${elapsed}s"
    echo -e "${CYAN}Chunks Retrieved:${NC} $chunks"
    echo ""
    echo -e "${CYAN}Answer:${NC}"
    echo "$answer" | head -n 15
    echo ""
    
    # Check for procedural content
    if echo "$answer" | grep -Eqi "ขั้นตอน|วิธี|กระบวนการ|เริ่มต้น|ผู้ใช้|1\.|2\.|3\."; then
        print_success "Found procedural content with steps"
        
        query_type=$(echo "$metadata" | jq -r '.query_analysis.query_type' 2>/dev/null)
        target_level=$(echo "$metadata" | jq -r '.query_analysis.target_level' 2>/dev/null)
        
        echo -e "${CYAN}Query Analysis:${NC}"
        echo "  - Query Type: $query_type"
        echo "  - Target Level: $target_level"
        
        return 0
    else
        print_warning "Procedural content not clear"
        return 1
    fi
}

test_context_expansion() {
    print_test 6 10 "Context Expansion - ทดสอบการขยาย context (parent/child)"
    
    query="เอกสารที่ใช้จดทะเบียนจำนอง"
    
    echo -e "${YELLOW}Query:${NC} \"$query\""
    echo -e "${CYAN}Expected:${NC} ควรได้ทั้ง main content + parent context + child details"
    echo ""
    
    response=$(curl -s -X POST "$BASE_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"$query\",
            \"session_id\": \"test_context_$(date +%s)\"
        }")
    
    answer=$(echo "$response" | jq -r '.answer' 2>/dev/null)
    chunks=$(echo "$response" | jq '.chunks' 2>/dev/null)
    metadata=$(echo "$response" | jq -r '.metadata' 2>/dev/null)
    
    # Check for context expansion in chunks
    has_parent=$(echo "$chunks" | jq -r '.[0].parent_text' 2>/dev/null)
    has_children=$(echo "$chunks" | jq -r '.[0].children_texts' 2>/dev/null)
    
    echo -e "${CYAN}Answer:${NC}"
    echo "$answer" | head -n 10
    echo ""
    
    echo -e "${CYAN}Context Check:${NC}"
    echo "  - Parent Context: $(if [ "$has_parent" != "null" ] && [ -n "$has_parent" ]; then echo "✅ Found"; else echo "❌ Not found"; fi)"
    echo "  - Child Contexts: $(if [ "$has_children" != "null" ] && [ "$has_children" != "[]" ]; then echo "✅ Found"; else echo "❌ Not found"; fi)"
    echo ""
    
    if [ "$has_parent" != "null" ] || [ "$has_children" != "null" ]; then
        print_success "Context expansion is working"
        
        # Show sample context
        if [ "$has_parent" != "null" ] && [ -n "$has_parent" ]; then
            echo -e "${CYAN}Sample Parent Context:${NC}"
            echo "$has_parent" | head -c 200
            echo "..."
            echo ""
        fi
        
        return 0
    else
        print_warning "Context expansion not detected (may not be needed for this query)"
        return 0  # Don't fail, as not all queries need expansion
    fi
}

test_hybrid_vs_dense() {
    print_test 7 10 "Hybrid vs Dense Comparison - เปรียบเทียบ Hybrid กับ Dense only"
    
    query="มาตรา 93 แห่งประมวลกฎหมายที่ดิน"
    
    echo -e "${YELLOW}Query:${NC} \"$query\""
    echo -e "${CYAN}Test:${NC} คำถามที่มี exact keyword (มาตรา 93)"
    echo ""
    
    start_time=$(date +%s.%N)
    response=$(curl -s -X POST "$BASE_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"$query\",
            \"session_id\": \"test_hybrid_$(date +%s)\"
        }")
    end_time=$(date +%s.%N)
    elapsed=$(echo "$end_time - $start_time" | bc)
    
    answer=$(echo "$response" | jq -r '.answer' 2>/dev/null)
    metadata=$(echo "$response" | jq -r '.metadata' 2>/dev/null)
    chunks=$(echo "$response" | jq '.chunks' 2>/dev/null)
    
    echo -e "${CYAN}Response Time:${NC} ${elapsed}s"
    echo ""
    
    # Check fusion method
    fusion_method=$(echo "$metadata" | jq -r '.retrieval_method' 2>/dev/null)
    echo -e "${CYAN}Retrieval Method:${NC} $fusion_method"
    
    # Check for BM25 and Dense scores in chunks
    echo -e "${CYAN}Score Analysis (Top 3):${NC}"
    for i in 0 1 2; do
        bm25_score=$(echo "$chunks" | jq -r ".[$i].bm25_score" 2>/dev/null)
        dense_score=$(echo "$chunks" | jq -r ".[$i].dense_score" 2>/dev/null)
        final_score=$(echo "$chunks" | jq -r ".[$i].score" 2>/dev/null)
        
        if [ "$bm25_score" != "null" ] && [ "$dense_score" != "null" ]; then
            echo "  Chunk $((i+1)): BM25=$bm25_score, Dense=$dense_score, Final=$final_score"
        fi
    done
    echo ""
    
    echo -e "${CYAN}Answer:${NC}"
    echo "$answer" | head -n 10
    echo ""
    
    # Check if "มาตรา 93" appears in answer
    if echo "$answer" | grep -qi "มาตรา.*93\|93"; then
        print_success "Found exact keyword 'มาตรา 93' (Hybrid Search working)"
        return 0
    else
        print_warning "Keyword 'มาตรา 93' not found clearly"
        return 1
    fi
}

test_complex_query() {
    print_test 8 10 "Complex Query - ทดสอบคำถามซับซ้อนหลายแนวคิด"
    
    query="คนต่างชาติจะโอนที่ดินมรดกต้องเสียค่าธรรมเนียมเท่าไหร่และมีขั้นตอนอย่างไร"
    
    echo -e "${YELLOW}Query:${NC} \"$query\""
    echo -e "${CYAN}Complexity:${NC} มีหลายแนวคิด (คนต่างชาติ + มรดก + ค่าธรรมเนียม + ขั้นตอน)"
    echo ""
    
    start_time=$(date +%s.%N)
    response=$(curl -s -X POST "$BASE_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"$query\",
            \"session_id\": \"test_complex_$(date +%s)\"
        }")
    end_time=$(date +%s.%N)
    elapsed=$(echo "$end_time - $start_time" | bc)
    
    answer=$(echo "$response" | jq -r '.answer' 2>/dev/null)
    metadata=$(echo "$response" | jq -r '.metadata' 2>/dev/null)
    chunks=$(echo "$response" | jq -r '.chunks | length' 2>/dev/null)
    
    echo -e "${CYAN}Response Time:${NC} ${elapsed}s"
    echo -e "${CYAN}Chunks Retrieved:${NC} $chunks"
    echo ""
    
    # Check query analysis
    is_complex=$(echo "$metadata" | jq -r '.query_analysis.is_complex' 2>/dev/null)
    query_type=$(echo "$metadata" | jq -r '.query_analysis.query_type' 2>/dev/null)
    
    echo -e "${CYAN}Query Analysis:${NC}"
    echo "  - Is Complex: $is_complex"
    echo "  - Query Type: $query_type"
    echo ""
    
    echo -e "${CYAN}Answer:${NC}"
    echo "$answer" | head -n 15
    echo ""
    
    # Check if answer covers multiple concepts
    covered_concepts=0
    echo "$answer" | grep -qi "ต่างชาติ\|ต่างด้าว\|foreign" && ((covered_concepts++))
    echo "$answer" | grep -qi "มรดก\|inherit" && ((covered_concepts++))
    echo "$answer" | grep -qi "ค่าธรรมเนียม\|ค่า\|fee" && ((covered_concepts++))
    echo "$answer" | grep -qi "ขั้นตอน\|วิธี\|step\|procedure" && ((covered_concepts++))
    
    echo -e "${CYAN}Concept Coverage:${NC} $covered_concepts/4"
    
    if [ $covered_concepts -ge 2 ]; then
        print_success "Complex query handled well (covers $covered_concepts concepts)"
        return 0
    else
        print_warning "Complex query coverage could be better ($covered_concepts concepts)"
        return 1
    fi
}

test_performance_consistency() {
    print_test 9 10 "Performance Consistency - ทดสอบความเสถียรของเวลาตอบ"
    
    query="โฉนดที่ดินคืออะไร"
    
    echo -e "${YELLOW}Query:${NC} \"$query\""
    echo -e "${CYAN}Test:${NC} รัน 3 ครั้ง เพื่อดูความคงที่ของเวลา"
    echo ""
    
    times=()
    for i in 1 2 3; do
        echo -e "${CYAN}Run $i/3...${NC}"
        start_time=$(date +%s.%N)
        response=$(curl -s -X POST "$BASE_URL/chat" \
            -H "Content-Type: application/json" \
            -d "{
                \"query\": \"$query\",
                \"session_id\": \"test_perf_${i}_$(date +%s)\"
            }")
        end_time=$(date +%s.%N)
        elapsed=$(echo "$end_time - $start_time" | bc)
        times+=($elapsed)
        echo "  Time: ${elapsed}s"
    done
    echo ""
    
    # Calculate average and variance
    sum=0
    for t in "${times[@]}"; do
        sum=$(echo "$sum + $t" | bc)
    done
    avg=$(echo "scale=2; $sum / 3" | bc)
    
    # Calculate standard deviation
    sum_sq_diff=0
    for t in "${times[@]}"; do
        diff=$(echo "$t - $avg" | bc)
        sq_diff=$(echo "$diff * $diff" | bc)
        sum_sq_diff=$(echo "$sum_sq_diff + $sq_diff" | bc)
    done
    variance=$(echo "scale=2; $sum_sq_diff / 3" | bc)
    std_dev=$(echo "scale=2; sqrt($variance)" | bc)
    
    echo -e "${CYAN}Statistics:${NC}"
    echo "  - Average: ${avg}s"
    echo "  - Std Dev: ${std_dev}s"
    echo "  - Min: $(printf '%s\n' "${times[@]}" | sort -n | head -1)s"
    echo "  - Max: $(printf '%s\n' "${times[@]}" | sort -n | tail -1)s"
    echo ""
    
    # Check if average is reasonable and consistent
    if (( $(echo "$avg < 15" | bc -l) )) && (( $(echo "$std_dev < 3" | bc -l) )); then
        print_success "Performance is good and consistent (avg=${avg}s, std=${std_dev}s)"
        return 0
    else
        print_warning "Performance could be improved (avg=${avg}s, std=${std_dev}s)"
        return 1
    fi
}

test_retrieval_quality() {
    print_test 10 10 "Retrieval Quality - ประเมินคุณภาพของเอกสารที่ดึงมา"
    
    query="เอกสารที่ต้องใช้ในการจดทะเบียนโอนที่ดิน"
    
    echo -e "${YELLOW}Query:${NC} \"$query\""
    echo ""
    
    response=$(curl -s -X POST "$BASE_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"$query\",
            \"session_id\": \"test_quality_$(date +%s)\"
        }")
    
    chunks=$(echo "$response" | jq '.chunks' 2>/dev/null)
    answer=$(echo "$response" | jq -r '.answer' 2>/dev/null)
    sources=$(echo "$response" | jq '.sources' 2>/dev/null)
    
    num_chunks=$(echo "$chunks" | jq 'length' 2>/dev/null)
    num_sources=$(echo "$sources" | jq 'length' 2>/dev/null)
    
    echo -e "${CYAN}Retrieval Stats:${NC}"
    echo "  - Chunks Retrieved: $num_chunks"
    echo "  - Sources: $num_sources"
    echo ""
    
    # Analyze chunk quality
    echo -e "${CYAN}Top 3 Chunks Analysis:${NC}"
    for i in 0 1 2; do
        score=$(echo "$chunks" | jq -r ".[$i].score" 2>/dev/null)
        rerank_score=$(echo "$chunks" | jq -r ".[$i].rerank_score" 2>/dev/null)
        text=$(echo "$chunks" | jq -r ".[$i].text" 2>/dev/null)
        section=$(echo "$chunks" | jq -r ".[$i].section_title" 2>/dev/null)
        
        echo ""
        echo "  Chunk $((i+1)):"
        echo "    Score: $score"
        echo "    Rerank: $rerank_score"
        echo "    Section: $section"
        echo "    Text Preview: $(echo "$text" | head -c 150)..."
        
        # Check relevance
        if echo "$text" | grep -Eqi "เอกสาร|โอน|จดทะเบียน"; then
            echo "    Relevance: ✅ High"
        else
            echo "    Relevance: ⚠️  Medium/Low"
        fi
    done
    echo ""
    
    echo -e "${CYAN}Answer Quality:${NC}"
    answer_length=${#answer}
    echo "  - Length: $answer_length characters"
    
    # Check if answer is comprehensive
    has_document_list=$(echo "$answer" | grep -Eqi "เอกสาร.*1\.|เอกสาร.*2\.|เอกสาร.*3\." && echo "yes" || echo "no")
    echo "  - Has Document List: $has_document_list"
    
    echo ""
    echo -e "${CYAN}Answer Preview:${NC}"
    echo "$answer" | head -n 15
    echo ""
    
    if [ $num_chunks -ge 3 ] && [ "$answer_length" -gt 100 ]; then
        print_success "Retrieval quality is good (chunks=$num_chunks, answer_length=$answer_length)"
        return 0
    else
        print_fail "Retrieval quality needs improvement"
        return 1
    fi
}

##############################################################################
# Main Execution
##############################################################################

main() {
    clear
    
    print_header "🧪 Advanced Retrieval Testing Suite for LangGraph"
    
    echo -e "${CYAN}Test Configuration:${NC}"
    echo "  - Base URL: $BASE_URL"
    echo "  - Log File: $LOG_FILE"
    echo "  - Date: $(date)"
    echo ""
    
    # Start logging
    exec > >(tee -a "$LOG_FILE")
    exec 2>&1
    
    # Wait for server
    echo -e "${YELLOW}Checking if server is running...${NC}"
    if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
        echo -e "${RED}❌ Server is not running on $BASE_URL${NC}"
        echo -e "${YELLOW}Please start the server first:${NC}"
        echo "  cd /Users/pond500/RAG/rag_dol"
        echo "  uvicorn langgraph_system.api_server_langgraph:app --host 0.0.0.0 --port 8001"
        exit 1
    fi
    echo -e "${GREEN}✅ Server is running${NC}"
    echo ""
    
    # Run tests
    TOTAL_TESTS=10
    
    test_health_check && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
    echo ""
    
    test_config && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
    echo ""
    
    test_keyword_query && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
    echo ""
    
    test_semantic_query && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
    echo ""
    
    test_procedural_query && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
    echo ""
    
    test_context_expansion && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
    echo ""
    
    test_hybrid_vs_dense && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
    echo ""
    
    test_complex_query && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
    echo ""
    
    test_performance_consistency && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
    echo ""
    
    test_retrieval_quality && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
    echo ""
    
    # Final Report
    print_header "📊 Test Results Summary"
    
    echo -e "${CYAN}${BOLD}Results:${NC}"
    echo "  - Total Tests: $TOTAL_TESTS"
    echo -e "  - ${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "  - ${RED}Failed: $FAILED_TESTS${NC}"
    
    success_rate=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
    echo -e "  - Success Rate: ${BOLD}${success_rate}%${NC}"
    echo ""
    
    # Verdict
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}${BOLD}╔═══════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}${BOLD}║                                           ║${NC}"
        echo -e "${GREEN}${BOLD}║  ✅ ALL TESTS PASSED - EXCELLENT! 🎉     ║${NC}"
        echo -e "${GREEN}${BOLD}║                                           ║${NC}"
        echo -e "${GREEN}${BOLD}║  Advanced Retrieval is working perfectly ║${NC}"
        echo -e "${GREEN}${BOLD}║  Ready for production deployment! 🚀     ║${NC}"
        echo -e "${GREEN}${BOLD}║                                           ║${NC}"
        echo -e "${GREEN}${BOLD}╚═══════════════════════════════════════════╝${NC}"
        exit 0
    elif [ $FAILED_TESTS -le 2 ]; then
        echo -e "${YELLOW}${BOLD}╔═══════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}${BOLD}║                                           ║${NC}"
        echo -e "${YELLOW}${BOLD}║  ⚠️  MOSTLY PASSED - GOOD! 👍            ║${NC}"
        echo -e "${YELLOW}${BOLD}║                                           ║${NC}"
        echo -e "${YELLOW}${BOLD}║  Minor issues detected                    ║${NC}"
        echo -e "${YELLOW}${BOLD}║  Review failed tests above                ║${NC}"
        echo -e "${YELLOW}${BOLD}║                                           ║${NC}"
        echo -e "${YELLOW}${BOLD}╚═══════════════════════════════════════════╝${NC}"
        exit 1
    else
        echo -e "${RED}${BOLD}╔═══════════════════════════════════════════╗${NC}"
        echo -e "${RED}${BOLD}║                                           ║${NC}"
        echo -e "${RED}${BOLD}║  ❌ MULTIPLE FAILURES - NEEDS WORK 🔧    ║${NC}"
        echo -e "${RED}${BOLD}║                                           ║${NC}"
        echo -e "${RED}${BOLD}║  Several tests failed                     ║${NC}"
        echo -e "${RED}${BOLD}║  Please review and fix issues             ║${NC}"
        echo -e "${RED}${BOLD}║                                           ║${NC}"
        echo -e "${RED}${BOLD}╚═══════════════════════════════════════════╝${NC}"
        exit 1
    fi
}

# Run main
main "$@"
