#!/bin/bash
# Quick Start Script for Running ETL on Server
# Usage: bash quick_start.sh

set -e

echo "============================================"
echo "🚀 RAG DOL Quick Start"
echo "============================================"
echo ""

# Check if in correct directory
if [ ! -f "src/etl_pipeline.py" ]; then
    echo "❌ Error: Please run this script from rag_dol directory"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if Qdrant is running
echo "🔍 Checking Qdrant..."
if curl -s http://localhost:6333 > /dev/null 2>&1; then
    echo "✅ Qdrant is running"
else
    echo "🐳 Starting Qdrant..."
    docker-compose up -d
    echo "⏳ Waiting for Qdrant to be ready..."
    sleep 5
fi

# Create collections if not exist
echo "🗄️  Setting up collections..."
python -c "
from src.qdrant_client_setup import QdrantManager
manager = QdrantManager()
try:
    manager.setup_collections()
    print('✅ Collections ready')
except Exception as e:
    print(f'Collections may already exist: {e}')
"

# Ask for test or full run
echo ""
echo "Choose run mode:"
echo "1) Test run (3 files)"
echo "2) Full run (all files)"
read -p "Enter choice (1 or 2): " choice

if [ "$choice" == "1" ]; then
    echo ""
    echo "🧪 Running test with 3 files..."
    python src/etl_pipeline.py
elif [ "$choice" == "2" ]; then
    echo ""
    echo "⚠️  This will process all files and may take a long time!"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Modify script to process all files
        sed -i.bak 's/limit=3,/limit=None,/' src/etl_pipeline.py
        
        echo ""
        echo "🚀 Running full ETL pipeline..."
        echo "💡 Tip: Use 'screen' or 'tmux' for long-running tasks"
        echo ""
        
        python src/etl_pipeline.py
        
        # Restore original
        mv src/etl_pipeline.py.bak src/etl_pipeline.py 2>/dev/null || true
    fi
else
    echo "❌ Invalid choice"
    exit 1
fi

echo ""
echo "============================================"
echo "✅ ETL Complete!"
echo "============================================"
echo ""
echo "📊 Check data:"
echo "  curl http://localhost:6333/collections/land_documents"
echo "  curl http://localhost:6333/collections/land_chunks"
echo ""
echo "📦 Export data:"
echo "  python src/qdrant_export_import.py export"
echo ""
