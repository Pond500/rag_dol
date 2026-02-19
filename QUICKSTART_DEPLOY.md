# 🎯 Quick Start - Deploy น้องไอดิน

## สำหรับคนรีบ (5 นาที) ⚡

### 1️⃣ Export ข้อมูล (บนเครื่อง Local)

```bash
# Export Qdrant data
python export_qdrant_snapshot.py

# ได้ไฟล์: qdrant_snapshots/land_chunks_hybrid-*.snapshot
```

### 2️⃣ Upload ไปเซิร์ฟเวอร์

```bash
# Option A: ใช้ script auto
./deploy.sh remote

# Option B: Manual upload
scp -r . user@server:/opt/rag_dol/
```

### 3️⃣ Deploy บน Server

```bash
# SSH เข้าเซิร์ฟเวอร์
ssh user@server

cd /opt/rag_dol

# Start ด้วย Docker
docker-compose -f docker-compose.production.yml up -d

# รอ 2 นาที แล้วทดสอบ
curl http://localhost:8001/health
```

### 4️⃣ Import Qdrant Data

```bash
# วิธีที่ 1: Snapshot (เร็วที่สุด ✅)
SNAPSHOT=$(ls qdrant_snapshots/*.snapshot | head -n 1)
curl -X PUT "http://localhost:6333/collections/land_chunks_hybrid/snapshots/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "snapshot=@${SNAPSHOT}"

# วิธีที่ 2: JSON Import
python import_qdrant_json.py
```

### 5️⃣ ทดสอบ

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","query":"โฉนดที่ดินคืออะไร"}' | jq
```

---

## คำสั่งที่ใช้บ่อย 📌

```bash
# ดู logs
docker-compose -f docker-compose.production.yml logs -f

# Restart
docker-compose -f docker-compose.production.yml restart api

# Stop
docker-compose -f docker-compose.production.yml down

# Update code
git pull && docker-compose -f docker-compose.production.yml up -d --build
```

---

## ขนาดไฟล์ประมาณ 📦

- โค้ด + dependencies: ~100 MB
- Qdrant data (snapshot): ~300-500 MB
- Docker images: ~2 GB (ครั้งแรก)
- **Total: ~2.5 GB**

---

## Requirements บนเซิร์ฟเวอร์ 💻

✅ **ขั้นต่ำ:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB
- Docker + Docker Compose

✅ **แนะนำ:**
- CPU: 4 cores
- RAM: 8GB
- Disk: 50GB
- SSD storage

---

## ไฟล์สำคัญที่ต้องมี ✨

```
/opt/rag_dol/
├── langgraph_system/          # โค้ด API
├── src/                       # Retrieval engine
├── rag_system/                # Memory system
├── data/
│   └── bm25_vocabulary.pkl    # ⚠️ สำคัญ!
├── qdrant_snapshots/          # ⚠️ Qdrant data
├── docker-compose.production.yml
├── Dockerfile.production
└── requirements.txt
```

---

## URLs หลังจาก Deploy ✅

- **API:** `http://your-server:8001`
- **Health Check:** `http://your-server:8001/health`
- **Chat:** `POST http://your-server:8001/chat`
- **Stream:** `POST http://your-server:8001/chat/stream`
- **Qdrant:** `http://your-server:6333`

---

## 🆘 เจอปัญหา?

1. **API ไม่ตอบสนอง**
   ```bash
   docker logs idin_api --tail=100
   ```

2. **Qdrant ไม่มีข้อมูล**
   ```bash
   curl http://localhost:6333/collections/land_chunks_hybrid
   ```

3. **Memory เต็ม**
   ```bash
   docker system prune -a
   ```

4. **Port ชน**
   ```bash
   # แก้ใน docker-compose.production.yml
   ports:
     - "8002:8001"  # เปลี่ยนจาก 8001
   ```

---

## 🎉 เสร็จแล้ว!

ระบบ น้องไอดิน พร้อมใช้งานแล้วครับ! 🚀

```bash
# ทดสอบ
curl http://your-server:8001/health
# {"status":"healthy","langgraph":true}
```
