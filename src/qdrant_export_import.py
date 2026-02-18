"""
Export/Import Qdrant data as JSON

สำหรับ sync data ระหว่าง remote <-> local แบบง่าย
ไม่ต้องใช้ snapshot API
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter
from config.settings import (
    COLLECTION_DOCUMENTS,
    COLLECTION_CHUNKS,
)

logger = logging.getLogger(__name__)


class QdrantExporter:
    """Export Qdrant data to JSON files"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None,
    ):
        self.client = QdrantClient(
            host=host,
            port=port,
            api_key=api_key,
            https=api_key is not None,  # ใช้ HTTPS ถ้ามี API key
        )
        logger.info(f"Connected to Qdrant at {host}:{port}")
    
    def export_collection(
        self,
        collection_name: str,
        output_file: Path,
        limit: Optional[int] = None,
    ):
        """
        Export collection to JSON
        
        Args:
            collection_name: ชื่อ collection
            output_file: ไฟล์ output (JSON)
            limit: จำกัดจำนวน points (None = ทั้งหมด)
        """
        logger.info(f"Exporting {collection_name}...")
        
        # Get collection info
        info = self.client.get_collection(collection_name)
        total_points = info.points_count
        
        if limit:
            total_points = min(total_points, limit)
        
        logger.info(f"Total points to export: {total_points}")
        
        # Scroll through all points
        points_data = []
        offset = None
        batch_size = 100
        
        with tqdm(total=total_points, desc=f"Exporting {collection_name}") as pbar:
            while True:
                # Scroll batch
                result, next_offset = self.client.scroll(
                    collection_name=collection_name,
                    limit=batch_size,
                    offset=offset,
                    with_vectors=True,
                    with_payload=True,
                )
                
                if not result:
                    break
                
                # Convert to dict
                for point in result:
                    points_data.append({
                        'id': str(point.id),
                        'vector': point.vector,
                        'payload': point.payload,
                    })
                
                pbar.update(len(result))
                
                if limit and len(points_data) >= limit:
                    points_data = points_data[:limit]
                    break
                
                if next_offset is None:
                    break
                
                offset = next_offset
        
        # Save to JSON
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        export_data = {
            'collection_name': collection_name,
            'vector_size': info.config.params.vectors.size,
            'distance': info.config.params.vectors.distance.name,
            'points_count': len(points_data),
            'points': points_data,
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Exported {len(points_data)} points to {output_file}")
        logger.info(f"   File size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
    
    def export_all(
        self,
        collections: List[str],
        output_dir: Path = Path("./exports"),
        limit: Optional[int] = None,
    ):
        """Export multiple collections"""
        output_dir = Path(output_dir)
        
        logger.info("=" * 60)
        logger.info("Exporting Collections")
        logger.info("=" * 60)
        
        for collection_name in collections:
            try:
                output_file = output_dir / f"{collection_name}.json"
                self.export_collection(collection_name, output_file, limit)
            except Exception as e:
                logger.error(f"Error exporting {collection_name}: {e}")
        
        logger.info("\n✅ Export complete!")


class QdrantImporter:
    """Import Qdrant data from JSON files"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None,
    ):
        self.client = QdrantClient(
            host=host,
            port=port,
            api_key=api_key,
            https=False,  # Local ไม่ใช้ HTTPS
        )
        logger.info(f"Connected to Qdrant at {host}:{port}")
    
    def import_collection(
        self,
        json_file: Path,
        collection_name: Optional[str] = None,
        recreate: bool = True,
    ):
        """
        Import collection from JSON
        
        Args:
            json_file: JSON file to import
            collection_name: Override collection name (ถ้าไม่ระบุ ใช้จาก JSON)
            recreate: ลบ collection เก่าแล้วสร้างใหม่
        """
        logger.info(f"Importing from {json_file}...")
        
        # Load JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        collection_name = collection_name or data['collection_name']
        vector_size = data['vector_size']
        distance = data['distance']
        points = data['points']
        
        logger.info(f"Collection: {collection_name}")
        logger.info(f"Vector size: {vector_size}")
        logger.info(f"Points: {len(points)}")
        
        # Recreate collection
        if recreate:
            try:
                self.client.delete_collection(collection_name)
                logger.info(f"Deleted old collection: {collection_name}")
            except Exception:
                pass
            
            from qdrant_client.models import VectorParams, Distance
            
            distance_map = {
                'COSINE': Distance.COSINE,
                'DOT': Distance.DOT,
                'EUCLID': Distance.EUCLID,
            }
            
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_map.get(distance, Distance.COSINE),
                ),
            )
            logger.info(f"Created collection: {collection_name}")
        
        # Upload points in batches
        batch_size = 100
        
        for i in tqdm(range(0, len(points), batch_size), desc="Uploading"):
            batch = points[i:i + batch_size]
            
            point_structs = [
                PointStruct(
                    id=point['id'],
                    vector=point['vector'],
                    payload=point['payload'],
                )
                for point in batch
            ]
            
            self.client.upsert(
                collection_name=collection_name,
                points=point_structs,
            )
        
        logger.info(f"✅ Imported {len(points)} points to {collection_name}")
    
    def import_all(
        self,
        import_dir: Path = Path("./exports"),
        recreate: bool = True,
    ):
        """Import all JSON files from directory"""
        import_dir = Path(import_dir)
        
        logger.info("=" * 60)
        logger.info("Importing Collections")
        logger.info("=" * 60)
        
        json_files = list(import_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} files to import")
        
        for json_file in json_files:
            try:
                self.import_collection(json_file, recreate=recreate)
            except Exception as e:
                logger.error(f"Error importing {json_file}: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info("\n✅ Import complete!")


def main_export():
    """Export from remote server"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Export from remote server
    exporter = QdrantExporter(
        host="your-server.com",  # เปลี่ยนเป็น server จริง
        port=6333,
        api_key=None,  # ใส่ API key ถ้ามี
    )
    
    exporter.export_all(
        collections=[COLLECTION_DOCUMENTS, COLLECTION_CHUNKS],
        output_dir=Path("./exports"),
    )


def main_import():
    """Import to local Qdrant"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Import to local
    importer = QdrantImporter(
        host="localhost",
        port=6333,
    )
    
    importer.import_all(
        import_dir=Path("./exports"),
        recreate=True,
    )


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python qdrant_export_import.py export  # Export from remote")
        print("  python qdrant_export_import.py import  # Import to local")
        sys.exit(1)
    
    if sys.argv[1] == "export":
        main_export()
    elif sys.argv[1] == "import":
        main_import()
