# Server-Local Sync Workflow

มี 3 วิธีในการรัน ETL บน server แล้วนำข้อมูลมาใช้ใน local:

## วิธีที่ 1: Remote Connection (แนะนำที่สุด) 🌟

รัน ETL บน server แล้วเขียนตรงเข้า local Qdrant ผ่าน SSH tunnel

### ขั้นตอน:

**1. บน local machine: เปิด SSH tunnel**
```bash
# Forward local Qdrant port ไปยัง server
ssh -R 6333:localhost:6333 user@your-server.com
```

**2. บน server: รัน ETL**
```bash
# Copy code ไปยัง server
scp -r rag_dol/ user@your-server.com:/path/to/

# SSH เข้าไป
ssh user@your-server.com

# รัน ETL (จะเขียนข้อมูลผ่าน tunnel มาที่ local)
cd /path/to/rag_dol
python src/remote_etl_pipeline.py
```

**3. ตรวจสอบข้อมูลใน local**
```bash
# บน local machine
python -c "
from src.qdrant_client_setup import QdrantManager
manager = QdrantManager()
info = manager.client.get_collection('land_documents')
print(f'Documents: {info.points_count}')
info = manager.client.get_collection('land_chunks')
print(f'Chunks: {info.points_count}')
"
```

### ข้อดี:
- ✅ Real-time: ข้อมูลเข้าทันที
- ✅ ไม่ต้อง export/import
- ✅ ประหยัดเนื้อที่

### ข้อเสี้ย:
- ❌ ต้องมี SSH access
- ❌ Slow ถ้า network ไม่ดี

---

## วิธีที่ 2: Export/Import JSON (ง่ายที่สุด) 📦

Export เป็น JSON แล้วดาวน์โหลดมา import ใน local

### ขั้นตอน:

**1. บน server: รัน ETL และ export**
```bash
# รัน ETL บน server
python src/etl_pipeline.py

# Export เป็น JSON
python src/qdrant_export_import.py export
# จะได้ไฟล์:
# - exports/land_documents.json
# - exports/land_chunks.json
```

**2. ดาวน์โหลดมา local**
```bash
# บน local machine
scp -r user@your-server.com:/path/to/rag_dol/exports ./
```

**3. Import เข้า local Qdrant**
```bash
# บน local machine
python src/qdrant_export_import.py import
```

### ข้อดี:
- ✅ ง่าย ไม่ต้อง setup tunnel
- ✅ Portable: ย้ายไปไหนก็ได้
- ✅ ไม่ต้องพึ่ง network ตอนรัน

### ข้อเสีย:
- ❌ ไฟล์ใหญ่ (JSON + vectors)
- ❌ ช้ากว่า (export + download + import)
- ❌ ใช้เนื้อที่เยอะ

---

## วิธีที่ 3: Qdrant Snapshot (เร็วที่สุด) ⚡

ใช้ Qdrant snapshot API (binary format, compact)

### ขั้นตอน:

**1. บน server: รัน ETL และสร้าง snapshot**
```bash
# รัน ETL
python src/etl_pipeline.py

# สร้าง snapshot
python -c "
from src.qdrant_sync import QdrantSync
sync = QdrantSync(remote_host='localhost')
sync.create_snapshot('land_documents', remote=True)
sync.create_snapshot('land_chunks', remote=True)
"
```

**2. ดาวน์โหลด snapshot**
```bash
# บน server: หา snapshot files
docker exec qdrant ls /qdrant/storage/collections/land_documents/snapshots/

# ดาวน์โหลด
scp user@your-server.com:/path/to/qdrant_storage/collections/*/snapshots/*.snapshot ./snapshots/
```

**3. Restore ใน local**
```bash
# Copy snapshot ไปที่ local Qdrant storage
cp snapshots/*.snapshot ./qdrant_storage/collections/land_documents/snapshots/
cp snapshots/*.snapshot ./qdrant_storage/collections/land_chunks/snapshots/

# Restore ผ่าน Qdrant API
curl -X POST 'http://localhost:6333/collections/land_documents/snapshots/recover' \
  -H 'Content-Type: application/json' \
  -d '{"location": "file:///qdrant/storage/collections/land_documents/snapshots/snapshot-name.snapshot"}'
```

### ข้อดี:
- ✅ เร็วที่สุด (binary format)
- ✅ ไฟล์เล็กที่สุด (compressed)
- ✅ Native Qdrant format

### ข้อเสีย:
- ❌ ซับซ้อนกว่า
- ❌ ต้องรู้จัก Qdrant internals

---

## การเลือกใช้

| วิธี | ความเร็ว | ความง่าย | Use Case |
|------|----------|----------|----------|
| Remote Connection | ⭐⭐⭐ | ⭐⭐ | มี SSH access, network ดี |
| Export/Import JSON | ⭐⭐ | ⭐⭐⭐ | ง่ายที่สุด, ไม่ต้อง setup |
| Snapshot | ⭐⭐⭐ | ⭐ | ข้อมูลเยอะมาก, ต้องการความเร็ว |

---

## แก้ไข Config สำหรับ Server

### 1. สำหรับ server (มี GPU):

**config/settings.py**
```python
EMBEDDING_MODEL_NAME = "BAAI/bge-multilingual-gemma2"
EMBEDDING_DIMENSIONS = 3584
EMBEDDING_DEVICE = "cuda"  # ใช้ GPU
EMBEDDING_BATCH_SIZE = 32  # Batch ใหญ่ได้
```

### 2. สำหรับ local (CPU):

**config/settings.py**
```python
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
EMBEDDING_DIMENSIONS = 1024
EMBEDDING_DEVICE = "cpu"
EMBEDDING_BATCH_SIZE = 8
```

---

## Example: Complete Workflow

```bash
# ============================================
# บน SERVER (มี GPU)
# ============================================

# 1. Clone และ setup
git clone https://github.com/your-repo/rag_dol.git
cd rag_dol

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Qdrant
docker-compose up -d

# 4. รัน ETL (ใช้ GPU, ใช้เวลาน้อย)
python src/etl_pipeline.py

# 5. Export ข้อมูล
python src/qdrant_export_import.py export

# 6. Compress (optional)
tar -czf exports.tar.gz exports/

# ============================================
# บน LOCAL MACHINE
# ============================================

# 1. ดาวน์โหลด exports
scp user@server:/path/to/rag_dol/exports.tar.gz ./
tar -xzf exports.tar.gz

# 2. Start local Qdrant
docker-compose up -d

# 3. Import ข้อมูล
python src/qdrant_export_import.py import

# 4. ตรวจสอบ
python -c "
from src.qdrant_client_setup import QdrantManager
manager = QdrantManager()
info = manager.client.get_collection('land_documents')
print(f'✅ Documents: {info.points_count}')
info = manager.client.get_collection('land_chunks')
print(f'✅ Chunks: {info.points_count}')
"
```

---

## Troubleshooting

### 1. SSH tunnel ไม่ work
```bash
# ลองใช้ autossh (auto-reconnect)
autossh -M 0 -R 6333:localhost:6333 user@server
```

### 2. JSON file ใหญ่เกินไป
```bash
# Export ทีละ collection
python -c "
from src.qdrant_export_import import QdrantExporter
exp = QdrantExporter()
exp.export_collection('land_documents', 'docs.json', limit=1000)
"

# หรือใช้ compression
gzip exports/*.json
```

### 3. Import ช้า
```bash
# เพิ่ม batch size ใน qdrant_export_import.py
# Line ~180: batch_size = 100 -> 500
```

---

## Performance Tips

1. **บน Server:**
   - ใช้ GPU ถ้ามี → เร็วขึ้น 10-50x
   - ใช้ batch size ใหญ่ → 32-64
   - ใช้ SSD สำหรับ Qdrant storage

2. **Transfer Data:**
   - ใช้ `rsync` แทน `scp` (resume ได้)
   - Compress ก่อนส่ง: `tar -czf`
   - ใช้ `aria2c` สำหรับ parallel download

3. **Import:**
   - เพิ่ม batch size
   - Disable WAL ชั่วคราว (ใน Qdrant config)
   - ใช้ snapshot ถ้าข้อมูลเยอะมาก

---

## Next Steps

หลังจาก sync ข้อมูลเสร็จแล้ว:

1. **Build Query Interface:**
   ```bash
   # สร้าง API สำหรับ query
   python src/query_engine.py
   ```

2. **Test Retrieval:**
   ```bash
   # ทดสอบ search
   python tests/test_search.py
   ```

3. **Deploy Frontend:**
   ```bash
   # Streamlit app
   streamlit run app.py
   ```
