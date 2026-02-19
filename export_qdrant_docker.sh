#!/bin/bash
# Export Qdrant Data from Docker Container
# วิธีที่แน่นอนและรวดเร็วที่สุด!

set -e

echo "🐳 Export Qdrant from Docker Container"
echo "======================================="

CONTAINER_NAME="qdrant_rag_dol"
BACKUP_DIR="qdrant_backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
STORAGE_BACKUP="${BACKUP_DIR}/qdrant_storage_${TIMESTAMP}"

# Check if container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Error: Container '${CONTAINER_NAME}' not found"
    echo ""
    echo "Available containers:"
    docker ps -a --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "⚠️  Warning: Container is not running. Starting..."
    docker start ${CONTAINER_NAME}
    sleep 5
fi

# Create backup directory
mkdir -p ${BACKUP_DIR}

echo ""
echo "📊 Container info:"
docker inspect ${CONTAINER_NAME} --format='  Status: {{.State.Status}}'
docker inspect ${CONTAINER_NAME} --format='  Running: {{.State.Running}}'

echo ""
echo "📥 Copying storage from container..."
docker cp ${CONTAINER_NAME}:/qdrant/storage ${STORAGE_BACKUP}

# Get size
SIZE=$(du -sh ${STORAGE_BACKUP} | awk '{print $1}')
echo "✅ Storage copied: ${STORAGE_BACKUP}"
echo "📦 Size: ${SIZE}"

# Create tar archive
echo ""
echo "📦 Creating compressed archive..."
ARCHIVE_NAME="${BACKUP_DIR}/qdrant_storage_${TIMESTAMP}.tar.gz"
tar -czf ${ARCHIVE_NAME} -C ${BACKUP_DIR} $(basename ${STORAGE_BACKUP})

ARCHIVE_SIZE=$(ls -lh ${ARCHIVE_NAME} | awk '{print $5}')
echo "✅ Archive created: ${ARCHIVE_NAME}"
echo "📦 Archive size: ${ARCHIVE_SIZE}"

# Calculate compression ratio
STORAGE_SIZE_BYTES=$(du -sb ${STORAGE_BACKUP} | awk '{print $1}')
ARCHIVE_SIZE_BYTES=$(stat -f%z ${ARCHIVE_NAME} 2>/dev/null || stat -c%s ${ARCHIVE_NAME})
COMPRESSION=$((100 - (ARCHIVE_SIZE_BYTES * 100 / STORAGE_SIZE_BYTES)))
echo "📊 Compression: ${COMPRESSION}%"

echo ""
echo "🚀 Deploy Instructions:"
echo "======================"
echo ""
echo "1. Upload to server:"
echo "   scp ${ARCHIVE_NAME} user@server:/opt/rag_dol/"
echo ""
echo "2. Extract on server:"
echo "   cd /opt/rag_dol"
echo "   tar -xzf $(basename ${ARCHIVE_NAME})"
echo "   mv qdrant_storage_${TIMESTAMP} qdrant_storage"
echo ""
echo "3. Start Qdrant:"
echo "   docker-compose -f docker-compose.production.yml up -d qdrant"
echo ""
echo "✅ Done!"

# Optional: Clean up uncompressed backup
read -p "Delete uncompressed backup? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ${STORAGE_BACKUP}
    echo "🗑️  Deleted: ${STORAGE_BACKUP}"
fi
