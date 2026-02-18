#!/bin/bash
# Server Setup Script for RAG DOL Project
# Usage: bash setup_server.sh

set -e  # Exit on error

echo "============================================"
echo "🚀 RAG DOL Server Setup"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on server
if [ -z "$SERVER" ]; then
    echo -e "${YELLOW}⚠️  Warning: This script should be run on the server${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. Update system
echo -e "${GREEN}📦 Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
echo -e "${GREEN}🐳 Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${YELLOW}Docker already installed${NC}"
fi

# 3. Install Docker Compose
echo -e "${GREEN}🐙 Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${YELLOW}Docker Compose already installed${NC}"
fi

# 4. Install Python and dependencies
echo -e "${GREEN}🐍 Installing Python...${NC}"
sudo apt install -y python3.10 python3-pip python3-venv git curl wget

# 5. Check GPU
echo -e "${GREEN}🎮 Checking for GPU...${NC}"
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✅ NVIDIA GPU detected${NC}"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    HAS_GPU=true
else
    echo -e "${YELLOW}No GPU detected - will use CPU${NC}"
    HAS_GPU=false
fi

# 6. Create project directory
echo -e "${GREEN}📁 Creating project directory...${NC}"
mkdir -p ~/rag_dol
cd ~/rag_dol

# 7. Create virtual environment
echo -e "${GREEN}🔧 Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# 8. Upgrade pip
echo -e "${GREEN}📦 Upgrading pip...${NC}"
pip install --upgrade pip

# 9. Create .env file
echo -e "${GREEN}⚙️  Creating .env configuration...${NC}"
cat > .env << 'EOF'
# Qdrant Settings
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Collections
COLLECTION_DOCUMENTS=land_documents
COLLECTION_CHUNKS=land_chunks

# Embedding Model
EMBEDDING_MODEL_NAME=BAAI/bge-m3
EMBEDDING_DIMENSIONS=1024
EMBEDDING_BATCH_SIZE=16
EMBEDDING_DEVICE=cpu
EOF

if [ "$HAS_GPU" = true ]; then
    echo -e "${GREEN}🎮 Configuring for GPU...${NC}"
    sed -i 's/EMBEDDING_DEVICE=cpu/EMBEDDING_DEVICE=cuda/' .env
    sed -i 's/EMBEDDING_BATCH_SIZE=16/EMBEDDING_BATCH_SIZE=32/' .env
fi

# 10. Print next steps
echo ""
echo "============================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "============================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Copy your code to this server:"
echo "   ${YELLOW}rsync -avz /path/to/rag_dol/ $(whoami)@$(hostname):~/rag_dol/${NC}"
echo ""
echo "2. Install Python dependencies:"
echo "   ${YELLOW}source venv/bin/activate${NC}"
echo "   ${YELLOW}pip install -r requirements.txt${NC}"
echo ""
echo "3. Start Qdrant:"
echo "   ${YELLOW}docker-compose up -d${NC}"
echo ""
echo "4. Run ETL:"
echo "   ${YELLOW}python src/etl_pipeline.py${NC}"
echo ""
echo "5. Export data:"
echo "   ${YELLOW}python src/qdrant_export_import.py export${NC}"
echo ""
echo "============================================"
echo ""

if [ "$HAS_GPU" = false ]; then
    echo -e "${YELLOW}⚠️  Note: You may need to logout and login again for Docker permissions${NC}"
fi

echo -e "${GREEN}Current directory: $(pwd)${NC}"
echo -e "${GREEN}Virtual environment: $(pwd)/venv${NC}"
echo ""
