"""
Export Qdrant Storage Directory (วิธีง่ายที่สุด!)
Copy storage folder โดยตรง - รวดเร็วและแน่นอน
"""
import shutil
import os
from datetime import datetime

print("📦 Direct Storage Export - น้องไอดิน")
print("=" * 50)

# Qdrant storage path (default Docker location)
source_storage = "./qdrant_storage"
backup_dir = "qdrant_backup"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"{backup_dir}/qdrant_storage_{timestamp}"

# Create backup directory
os.makedirs(backup_dir, exist_ok=True)

print(f"\n📁 Source: {source_storage}")
print(f"📁 Destination: {backup_path}")

try:
    # Check if source exists
    if not os.path.exists(source_storage):
        print(f"\n❌ Error: {source_storage} not found!")
        print("\n💡 Solutions:")
        print("1. If using Docker: docker cp qdrant_rag_dol:/qdrant/storage ./qdrant_storage")
        print("2. If running local: Check your Qdrant storage path")
        print("3. Use JSON export: python export_qdrant_json.py")
        exit(1)
    
    # Get source size
    def get_dir_size(path):
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
        return total
    
    source_size = get_dir_size(source_storage)
    print(f"📊 Source size: {source_size / (1024*1024):.2f} MB")
    
    # Copy directory
    print(f"\n📋 Copying storage...")
    shutil.copytree(source_storage, backup_path)
    
    backup_size = get_dir_size(backup_path)
    print(f"✅ Backup created: {backup_path}")
    print(f"📦 Backup size: {backup_size / (1024*1024):.2f} MB")
    
    # Create tar archive
    print(f"\n📦 Creating archive...")
    archive_name = f"{backup_dir}/qdrant_storage_{timestamp}.tar.gz"
    
    import tarfile
    with tarfile.open(archive_name, "w:gz") as tar:
        tar.add(backup_path, arcname=f"qdrant_storage")
    
    archive_size = os.path.getsize(archive_name)
    print(f"✅ Archive created: {archive_name}")
    print(f"📦 Archive size: {archive_size / (1024*1024):.2f} MB")
    print(f"📊 Compression: {(1 - archive_size/backup_size)*100:.1f}%")
    
    print(f"\n🚀 Deploy Instructions:")
    print(f"=" * 50)
    print(f"\n1. Upload to server:")
    print(f"   scp {archive_name} user@server:/opt/rag_dol/")
    
    print(f"\n2. Extract on server:")
    print(f"   cd /opt/rag_dol")
    print(f"   tar -xzf {os.path.basename(archive_name)}")
    
    print(f"\n3. Start Qdrant with the storage:")
    print(f"   # In docker-compose.production.yml, storage is already mounted")
    print(f"   docker-compose -f docker-compose.production.yml up -d qdrant")
    
    print(f"\n✅ Done! This is the FASTEST way to deploy Qdrant data.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
    print(f"\n💡 Alternatives:")
    print(f"1. Export from Docker: docker cp qdrant_rag_dol:/qdrant/storage ./qdrant_storage")
    print(f"2. Use JSON export: python export_qdrant_json.py")
