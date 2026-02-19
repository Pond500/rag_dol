"""
Import Qdrant Collection from JSON
สำหรับ restore ข้อมูลบนเซิร์ฟเวอร์ปลายทาง
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import json
from tqdm import tqdm

# Connect to Qdrant (on target server)
client = QdrantClient(host="localhost", port=6333)

# Input file
import_file = "qdrant_export/land_chunks_hybrid.json"

print(f"📥 Loading data from {import_file}...")

try:
    with open(import_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    collection_name = data['collection_name']
    vector_size = data['vector_size']
    distance = Distance.COSINE  # Default
    points = data['points']
    
    print(f"📊 Collection: {collection_name}")
    print(f"📊 Vector size: {vector_size}")
    print(f"📊 Points: {len(points):,}")
    
    # Create collection
    print(f"\n🔧 Creating collection...")
    try:
        client.delete_collection(collection_name)
        print(f"🗑️  Deleted existing collection")
    except:
        pass
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=distance
        )
    )
    print(f"✅ Collection created")
    
    # Upload points in batches
    print(f"\n📤 Uploading points...")
    batch_size = 100
    
    for i in tqdm(range(0, len(points), batch_size), desc="Uploading"):
        batch = points[i:i+batch_size]
        
        point_structs = [
            PointStruct(
                id=p['id'],
                vector=p['vector'],
                payload=p['payload']
            )
            for p in batch
        ]
        
        client.upsert(
            collection_name=collection_name,
            points=point_structs
        )
    
    # Verify
    collection_info = client.get_collection(collection_name)
    print(f"\n✅ Import completed!")
    print(f"📊 Imported: {collection_info.points_count:,} points")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
