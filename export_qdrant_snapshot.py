"""
Export Qdrant Collection Snapshot for Deployment
สำหรับ backup และ deploy ข้อมูล index ไปเซิร์ฟเวอร์อื่น
"""
from qdrant_client import QdrantClient
import os
from datetime import datetime
import time

# Connect to local Qdrant with longer timeout
client = QdrantClient(host="localhost", port=6333, timeout=300)  # 5 minutes timeout

collection_name = "land_chunks_hybrid"
snapshot_dir = "qdrant_snapshots"

# Create snapshot directory
os.makedirs(snapshot_dir, exist_ok=True)

print(f"📸 Creating snapshot for collection: {collection_name}...")

try:
    # Create snapshot with progress indication
    print(f"⏳ Creating snapshot (this may take 1-5 minutes for 3,704 points)...")
    start_time = time.time()
    
    snapshot_info = client.create_snapshot(collection_name=collection_name)
    
    elapsed = time.time() - start_time
    print(f"✅ Snapshot created in {elapsed:.1f}s: {snapshot_info.name}")
    print(f"📊 Collection info:")
    
    # Get collection info
    collection_info = client.get_collection(collection_name)
    print(f"   - Vectors count: {collection_info.points_count:,}")
    print(f"   - Vector size: {collection_info.config.params.vectors.size}")
    
    # Download snapshot
    print(f"\n📥 Downloading snapshot...")
    snapshot_path = os.path.join(snapshot_dir, snapshot_info.name)
    
    # Get snapshot and save to file
    import requests
    snapshot_url = f"http://localhost:6333/collections/{collection_name}/snapshots/{snapshot_info.name}"
    
    print(f"📡 Fetching from: {snapshot_url}")
    response = requests.get(snapshot_url, stream=True, timeout=300)
    response.raise_for_status()
    
    # Save with progress
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(snapshot_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                progress = (downloaded / total_size) * 100
                print(f"\r   Progress: {progress:.1f}% ({downloaded/(1024*1024):.1f}MB / {total_size/(1024*1024):.1f}MB)", end='')
    
    print()  # New line
    file_size = os.path.getsize(snapshot_path) / (1024 * 1024)  # MB
    print(f"✅ Snapshot saved: {snapshot_path}")
    print(f"📦 File size: {file_size:.2f} MB")
    
    print(f"\n🚀 Deploy Instructions:")
    print(f"1. Upload snapshot to server:")
    print(f"   scp {snapshot_path} user@server:/opt/rag_dol/qdrant_snapshots/")
    print(f"\n2. On server, restore with:")
    print(f"   curl -X PUT 'http://localhost:6333/collections/{collection_name}/snapshots/upload' \\")
    print(f"        -H 'Content-Type: multipart/form-data' \\")
    print(f"        -F 'snapshot=@qdrant_snapshots/{snapshot_info.name}'")
    
except requests.exceptions.Timeout:
    print(f"❌ Error: Download timed out (snapshot might still be created)")
    print(f"\n💡 Try downloading manually:")
    print(f"   curl http://localhost:6333/collections/{collection_name}/snapshots -o snapshot.tar")
    print(f"\n💡 Or use JSON export (slower but more reliable):")
    print(f"   python export_qdrant_json.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"\n💡 Troubleshooting:")
    print(f"1. Check Qdrant is running: curl http://localhost:6333/collections")
    print(f"2. Try JSON export instead: python export_qdrant_json.py")
    print(f"3. List existing snapshots: curl http://localhost:6333/collections/{collection_name}/snapshots")
    import traceback
    traceback.print_exc()
