"""
Qdrant Sync Utilities

ใช้สำหรับ:
1. Export snapshot จาก remote server
2. Import snapshot มา local Qdrant
3. Sync data ระหว่าง remote <-> local
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

import logging
import requests
from pathlib import Path
from typing import Optional
from qdrant_client import QdrantClient
from config.settings import (
    COLLECTION_DOCUMENTS,
    COLLECTION_CHUNKS,
)

logger = logging.getLogger(__name__)


class QdrantSync:
    """
    Sync Qdrant data between remote server and local
    
    Methods:
    - create_snapshot: สร้าง snapshot บน remote/local
    - download_snapshot: ดาวน์โหลด snapshot จาก remote
    - restore_snapshot: restore snapshot มา local
    - sync_from_remote: sync ทั้งหมดจาก remote มา local
    """
    
    def __init__(
        self,
        local_host: str = "localhost",
        local_port: int = 6333,
        remote_host: Optional[str] = None,
        remote_port: int = 6333,
        remote_api_key: Optional[str] = None,
    ):
        """
        Initialize sync client
        
        Args:
            local_host: Local Qdrant host
            local_port: Local Qdrant port
            remote_host: Remote server host (e.g., "your-server.com")
            remote_port: Remote server port
            remote_api_key: API key for remote (ถ้ามี authentication)
        """
        # Local client
        self.local_client = QdrantClient(
            host=local_host,
            port=local_port,
            https=False,
        )
        
        # Remote client (ถ้ามี)
        self.remote_client = None
        self.remote_host = remote_host
        self.remote_port = remote_port
        
        if remote_host:
            self.remote_client = QdrantClient(
                host=remote_host,
                port=remote_port,
                api_key=remote_api_key,
                https=True,  # ใช้ HTTPS สำหรับ remote
            )
        
        logger.info(f"QdrantSync initialized: local={local_host}:{local_port}, remote={remote_host}")
    
    def create_snapshot(
        self,
        collection_name: str,
        remote: bool = False,
    ) -> str:
        """
        สร้าง snapshot ของ collection
        
        Args:
            collection_name: ชื่อ collection
            remote: True = สร้างบน remote, False = สร้างบน local
            
        Returns:
            Snapshot name
        """
        client = self.remote_client if remote else self.local_client
        location = "remote" if remote else "local"
        
        logger.info(f"Creating snapshot for {collection_name} on {location}...")
        
        snapshot = client.create_snapshot(collection_name=collection_name)
        
        logger.info(f"✅ Snapshot created: {snapshot.name}")
        return snapshot.name
    
    def download_snapshot(
        self,
        collection_name: str,
        snapshot_name: str,
        output_dir: Path = Path("./snapshots"),
    ) -> Path:
        """
        ดาวน์โหลด snapshot จาก remote server
        
        Args:
            collection_name: ชื่อ collection
            snapshot_name: ชื่อ snapshot
            output_dir: โฟลเดอร์สำหรับเก็บ snapshot
            
        Returns:
            Path to downloaded snapshot file
        """
        if not self.remote_host:
            raise ValueError("Remote host not configured!")
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Download URL
        url = f"https://{self.remote_host}:{self.remote_port}/collections/{collection_name}/snapshots/{snapshot_name}"
        
        logger.info(f"Downloading snapshot from {url}...")
        
        # Download
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Save to file
        output_path = output_dir / f"{collection_name}_{snapshot_name}"
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"✅ Downloaded to {output_path}")
        return output_path
    
    def restore_snapshot(
        self,
        collection_name: str,
        snapshot_path: Path,
    ):
        """
        Restore snapshot มา local Qdrant
        
        Args:
            collection_name: ชื่อ collection
            snapshot_path: Path to snapshot file
        """
        logger.info(f"Restoring snapshot {snapshot_path} to {collection_name}...")
        
        # ใช้ Qdrant API เพื่อ restore
        # Note: ต้อง copy snapshot file ไปที่ Qdrant storage directory ก่อน
        
        logger.warning("⚠️  Manual restore required:")
        logger.info(f"1. Copy {snapshot_path} to Qdrant storage: ./qdrant_storage/collections/{collection_name}/snapshots/")
        logger.info(f"2. Use Qdrant API: POST /collections/{collection_name}/snapshots/recover")
        logger.info(f"3. Or use: docker exec -it qdrant qdrant-restore --snapshot-path /qdrant/storage/...")
    
    def sync_from_remote(
        self,
        collections: list = [COLLECTION_DOCUMENTS, COLLECTION_CHUNKS],
        output_dir: Path = Path("./snapshots"),
    ):
        """
        Sync ทั้งหมดจาก remote มา local
        
        Args:
            collections: List of collection names to sync
            output_dir: Directory for snapshots
        """
        logger.info("=" * 60)
        logger.info("Syncing from Remote to Local")
        logger.info("=" * 60)
        
        for collection_name in collections:
            try:
                # 1. Create snapshot on remote
                snapshot_name = self.create_snapshot(collection_name, remote=True)
                
                # 2. Download snapshot
                snapshot_path = self.download_snapshot(
                    collection_name,
                    snapshot_name,
                    output_dir,
                )
                
                # 3. Instructions for restore
                logger.info(f"\n📦 {collection_name}:")
                logger.info(f"   Snapshot: {snapshot_path}")
                logger.info(f"   Ready to restore to local Qdrant")
                
            except Exception as e:
                logger.error(f"Error syncing {collection_name}: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Sync Complete!")
        logger.info("=" * 60)


def main():
    """Example usage"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Sync from remote server
    sync = QdrantSync(
        local_host="localhost",
        local_port=6333,
        remote_host="your-server.com",  # เปลี่ยนเป็น server จริง
        remote_port=6333,
        remote_api_key=None,  # ใส่ API key ถ้ามี
    )
    
    # Sync all collections
    sync.sync_from_remote()


if __name__ == "__main__":
    main()
