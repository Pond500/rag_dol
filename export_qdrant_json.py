"""
Export Qdrant Collection to JSON
สำหรับกรณีที่ต้องการย้ายข้อมูลแบบ portable
"""
from qdrant_client import QdrantClient
import json
from tqdm import tqdm
import os

# Connect to local Qdrant
client = QdrantClient(host="localhost", port=6333)

collection_name = "land_chunks_hybrid"
output_dir = "qdrant_export"
output_file = os.path.join(output_dir, f"{collection_name}.json")

os.makedirs(output_dir, exist_ok=True)

print(f"📦 Exporting collection: {collection_name}")

try:
    # Get collection info
    collection_info = client.get_collection(collection_name)
    total_points = collection_info.points_count
    
    print(f"📊 Total points: {total_points:,}")
    print(f"📊 Vector size: {collection_info.config.params.vectors.size}")
    
    # Scroll all points
    print(f"\n📥 Fetching all points...")
    all_points = []
    offset = None
    batch_size = 100
    
    with tqdm(total=total_points, desc="Exporting") as pbar:
        while True:
            results, next_offset = client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )
            
            if not results:
                break
            
            for point in results:
                all_points.append({
                    "id": point.id,
                    "vector": point.vector,
                    "payload": point.payload
                })
            
            pbar.update(len(results))
            offset = next_offset
            
            if offset is None:
                break
    
    # Save to JSON
    print(f"\n💾 Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "collection_name": collection_name,
            "vector_size": collection_info.config.params.vectors.size,
            "distance": str(collection_info.config.params.vectors.distance),
            "count": len(all_points),
            "points": all_points
        }, f, ensure_ascii=False, indent=2)
    
    file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
    print(f"✅ Export completed!")
    print(f"📦 File: {output_file}")
    print(f"📊 Size: {file_size:.2f} MB")
    print(f"📊 Points: {len(all_points):,}")
    
    print(f"\n🚀 Deploy Instructions:")
    print(f"1. Upload to server: scp {output_file} user@server:/path/")
    print(f"2. Import with: python import_qdrant_json.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
