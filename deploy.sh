# 🚀 Quick Deploy Script - น้องไอดิน
# สคริปต์สำหรับ deploy แบบ one-command

#!/bin/bash

set -e  # Exit on error

echo "🚀 น้องไอดิน - Production Deployment Script"
echo "============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="/opt/rag_dol"
SERVER_USER="your-user"
SERVER_HOST="your-server.com"
QDRANT_PORT=6333
API_PORT=8001

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_info "✅ Dependencies OK"
}

export_qdrant() {
    log_info "Exporting Qdrant collection..."
    python3 export_qdrant_snapshot.py
    log_info "✅ Qdrant export completed"
}

create_package() {
    log_info "Creating deployment package..."
    
    # Create tarball
    tar -czf rag_dol_deploy.tar.gz \
        langgraph_system/ \
        src/ \
        rag_system/ \
        data/bm25_vocabulary.pkl \
        docker-compose.production.yml \
        Dockerfile.production \
        requirements.txt \
        import_qdrant_json.py
    
    tar -czf qdrant_data.tar.gz qdrant_snapshots/
    
    log_info "✅ Package created"
    ls -lh *.tar.gz
}

upload_to_server() {
    log_info "Uploading to server ${SERVER_HOST}..."
    
    # Create directory on server
    ssh ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${DEPLOY_DIR}"
    
    # Upload files
    rsync -avz --progress rag_dol_deploy.tar.gz ${SERVER_USER}@${SERVER_HOST}:${DEPLOY_DIR}/
    rsync -avz --progress qdrant_data.tar.gz ${SERVER_USER}@${SERVER_HOST}:${DEPLOY_DIR}/
    
    log_info "✅ Upload completed"
}

deploy_on_server() {
    log_info "Deploying on server..."
    
    ssh ${SERVER_USER}@${SERVER_HOST} << 'ENDSSH'
cd /opt/rag_dol

# Extract
tar -xzf rag_dol_deploy.tar.gz
tar -xzf qdrant_data.tar.gz

# Start Qdrant
docker-compose -f docker-compose.production.yml up -d qdrant
sleep 30

# Import data (snapshot)
SNAPSHOT=$(ls qdrant_snapshots/*.snapshot | head -n 1)
SNAPSHOT_NAME=$(basename $SNAPSHOT)

curl -X PUT "http://localhost:6333/collections/land_chunks_hybrid/snapshots/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "snapshot=@${SNAPSHOT}"

# Build and start API
docker-compose -f docker-compose.production.yml build api
docker-compose -f docker-compose.production.yml up -d api

# Wait for API
sleep 60

# Health check
curl http://localhost:8001/health

echo "✅ Deployment completed!"
ENDSSH
    
    log_info "✅ Server deployment completed"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Health check
    HEALTH=$(ssh ${SERVER_USER}@${SERVER_HOST} "curl -s http://localhost:${API_PORT}/health")
    echo "Health: $HEALTH"
    
    # Test query
    log_info "Testing chat endpoint..."
    ssh ${SERVER_USER}@${SERVER_HOST} << 'ENDSSH'
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-prod",
    "query": "โฉนดที่ดินคืออะไร"
  }' | jq '.answer'
ENDSSH
    
    log_info "✅ Verification completed"
}

# Main deployment flow
main() {
    case "$1" in
        local)
            log_info "Local deployment mode"
            check_dependencies
            export_qdrant
            docker-compose -f docker-compose.production.yml up -d
            log_info "✅ Local deployment completed"
            ;;
        remote)
            log_info "Remote deployment mode"
            check_dependencies
            export_qdrant
            create_package
            upload_to_server
            deploy_on_server
            verify_deployment
            log_info "✅ Remote deployment completed"
            ;;
        export)
            log_info "Export mode only"
            export_qdrant
            create_package
            log_info "✅ Export completed"
            ;;
        *)
            echo "Usage: $0 {local|remote|export}"
            echo ""
            echo "  local  - Deploy locally with Docker"
            echo "  remote - Deploy to remote server"
            echo "  export - Export data only (no deployment)"
            exit 1
            ;;
    esac
}

# Run
main "$@"
