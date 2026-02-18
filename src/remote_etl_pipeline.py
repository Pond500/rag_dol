"""
Remote ETL Pipeline Configuration

รัน ETL บน server แล้วเขียนตรงเข้า remote Qdrant
ไม่ต้อง export/import เลย
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

import logging
from pathlib import Path
from src.etl_pipeline import ETLPipeline
from src.qdrant_client_setup import QdrantManager

logger = logging.getLogger(__name__)


class RemoteETLPipeline(ETLPipeline):
    """
    ETL Pipeline ที่เขียนข้อมูลไปที่ remote Qdrant ตรง ๆ
    
    Use case:
    - รัน ETL บน server (มี GPU/CPU แรง)
    - เขียนข้อมูลตรงไปยัง Qdrant ที่ local (ผ่าน VPN หรือ tunnel)
    - หรือเขียนไปยัง Qdrant cloud
    """
    
    def __init__(
        self,
        data_dir: Path,
        device: str = "cpu",
        remote_host: str = "localhost",
        remote_port: int = 6333,
        remote_api_key: str = None,
    ):
        """
        Initialize with remote Qdrant connection
        
        Args:
            data_dir: Directory with documents
            device: cpu/cuda/mps for embeddings
            remote_host: Remote Qdrant host
            remote_port: Remote Qdrant port
            remote_api_key: API key (if needed)
        """
        # Initialize parent but override Qdrant manager
        super().__init__(data_dir, device)
        
        # Replace with remote Qdrant connection
        self.qdrant_manager = QdrantManager(
            host=remote_host,
            port=remote_port,
            api_key=remote_api_key,
        )
        
        logger.info(f"✅ Connected to remote Qdrant: {remote_host}:{remote_port}")


def main():
    """
    Example: รัน ETL บน server แล้วเขียนไปที่ local Qdrant
    
    Setup:
    1. บน server: เปิด SSH tunnel
       ssh -R 6333:localhost:6333 your-server.com
       
    2. รัน ETL บน server:
       python remote_etl_pipeline.py
       
    3. ข้อมูลจะเขียนตรงเข้า local Qdrant ผ่าน tunnel
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Option 1: เขียนไปที่ local ผ่าน SSH tunnel
    pipeline = RemoteETLPipeline(
        data_dir=Path("/path/to/data/on/server"),
        device="cuda",  # ใช้ GPU บน server
        remote_host="localhost",  # ผ่าน tunnel
        remote_port=6333,
    )
    
    # Option 2: เขียนไปที่ Qdrant Cloud
    # pipeline = RemoteETLPipeline(
    #     data_dir=Path("/path/to/data/on/server"),
    #     device="cuda",
    #     remote_host="your-cluster.cloud.qdrant.io",
    #     remote_port=6333,
    #     remote_api_key="your-api-key",
    # )
    
    # Run ETL
    pipeline.run(
        pattern="**/*.txt",
        limit=None,  # Process all
    )


if __name__ == "__main__":
    main()
