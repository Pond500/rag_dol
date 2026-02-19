#!/bin/bash
# Pre-deployment Checklist Script

echo "🔍 Pre-Deployment Checklist for น้องไอดิน"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

# Check function
check_item() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅${NC} $2"
    else
        echo -e "${RED}❌${NC} $2"
        ERRORS=$((ERRORS + 1))
    fi
}

echo ""
echo "📁 Checking Files..."
echo "--------------------"

# Check important files
test -f "langgraph_system/api_server_langgraph.py"
check_item $? "API Server file exists"

test -f "data/bm25_vocabulary.pkl"
check_item $? "BM25 vocabulary file exists"

test -f "docker-compose.production.yml"
check_item $? "Docker Compose file exists"

test -f "Dockerfile.production"
check_item $? "Dockerfile exists"

test -f "requirements.production.txt"
check_item $? "Requirements file exists"

echo ""
echo "🗂️ Checking Directories..."
echo "--------------------------"

test -d "langgraph_system"
check_item $? "langgraph_system/ directory exists"

test -d "src"
check_item $? "src/ directory exists"

test -d "rag_system"
check_item $? "rag_system/ directory exists"

test -d "data"
check_item $? "data/ directory exists"

echo ""
echo "🔧 Checking Scripts..."
echo "---------------------"

test -f "export_qdrant_snapshot.py"
check_item $? "Qdrant export script exists"

test -f "import_qdrant_json.py"
check_item $? "Qdrant import script exists"

test -x "deploy.sh"
check_item $? "Deploy script is executable"

echo ""
echo "🐳 Checking Docker..."
echo "--------------------"

docker --version > /dev/null 2>&1
check_item $? "Docker is installed"

docker-compose --version > /dev/null 2>&1
check_item $? "Docker Compose is installed"

echo ""
echo "📊 Checking Qdrant..."
echo "--------------------"

curl -s http://localhost:6333/collections > /dev/null 2>&1
check_item $? "Qdrant is running locally"

if [ $? -eq 0 ]; then
    POINT_COUNT=$(curl -s http://localhost:6333/collections/land_chunks_hybrid | grep -o '"points_count":[0-9]*' | cut -d':' -f2)
    if [ ! -z "$POINT_COUNT" ] && [ "$POINT_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅${NC} Qdrant has $POINT_COUNT points"
    else
        echo -e "${RED}❌${NC} Qdrant collection is empty"
        ERRORS=$((ERRORS + 1))
    fi
fi

echo ""
echo "📦 Checking File Sizes..."
echo "------------------------"

if [ -f "data/bm25_vocabulary.pkl" ]; then
    SIZE=$(ls -lh data/bm25_vocabulary.pkl | awk '{print $5}')
    echo -e "${GREEN}✅${NC} BM25 vocabulary: $SIZE"
fi

if [ -d "qdrant_snapshots" ] && [ "$(ls -A qdrant_snapshots)" ]; then
    SIZE=$(du -sh qdrant_snapshots | awk '{print $1}')
    echo -e "${GREEN}✅${NC} Qdrant snapshots: $SIZE"
elif [ -d "qdrant_export" ] && [ "$(ls -A qdrant_export)" ]; then
    SIZE=$(du -sh qdrant_export | awk '{print $1}')
    echo -e "${GREEN}✅${NC} Qdrant export: $SIZE"
else
    echo -e "${YELLOW}⚠️${NC}  No Qdrant data exported yet"
    echo "   Run: python export_qdrant_snapshot.py"
fi

echo ""
echo "🔑 Checking Configuration..."
echo "---------------------------"

if grep -q "sk-driylW9kC_SdAaHEl3350g" langgraph_system/api_server_langgraph.py; then
    echo -e "${YELLOW}⚠️${NC}  API key is hardcoded (consider using .env)"
fi

if grep -q "localhost" docker-compose.production.yml; then
    echo -e "${GREEN}✅${NC} Docker compose uses container networking"
fi

echo ""
echo "=========================================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to deploy.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Export Qdrant data: python export_qdrant_snapshot.py"
    echo "  2. Deploy locally: ./deploy.sh local"
    echo "  3. Deploy to server: ./deploy.sh remote"
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS error(s). Please fix before deploying.${NC}"
    exit 1
fi
