# 🎯 FINAL DEPLOYMENT CHECKLIST - น้องไอดิน

## ✅ Step-by-Step Deployment (ทดสอบแล้ว!)

### 📦 สิ่งที่มีพร้อมแล้ว:

```bash
qdrant_backup/
  └── qdrant_storage_20260219_092634.tar.gz  # 80 MB (จาก 2.3 GB!)

data/
  └── bm25_vocabulary.pkl                     # 460 KB

langgraph_system/                             # API code
src/                                          # Retrieval engine
rag_system/                                   # Memory system
```

---

## 🚀 Option 1: Deploy ด้วย rsync (แนะนำ!)

### บนเครื่อง Local:

```bash
# 1. Upload ทุกอย่างไปเซิร์ฟเวอร์
rsync -avz --progress \
  --exclude='qdrant_storage' \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.git' \
  ./ user@server:/opt/rag_dol/

# 2. Upload Qdrant backup
rsync -avz --progress \
  qdrant_backup/qdrant_storage_20260219_092634.tar.gz \
  user@server:/opt/rag_dol/
```

### บนเซิร์ฟเวอร์:

```bash
# SSH เข้าเซิร์ฟเวอร์
ssh user@server

# ไปที่ directory
cd /opt/rag_dol

# Extract Qdrant storage
tar -xzf qdrant_storage_20260219_092634.tar.gz
mv qdrant_storage_20260219_092634 qdrant_storage

# Start services
docker-compose -f docker-compose.production.yml up -d

# ดู logs
docker-compose -f docker-compose.production.yml logs -f

# รอ 1-2 นาที แล้วทดสอบ
curl http://localhost:8001/health

# ทดสอบ chat
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test-prod","query":"โฉนดที่ดินคืออะไร"}' | jq
```

---

## 🚀 Option 2: Deploy ด้วย Git (สำหรับโค้ด) + Manual Upload (สำหรับ Data)

### 1. Push โค้ดไป GitHub:

```bash
git add .
git commit -m "Add deployment scripts and production config"
git push origin main
```

### 2. Clone บนเซิร์ฟเวอร์:

```bash
# SSH to server
ssh user@server

# Clone repository
cd /opt
git clone https://github.com/Pond500/rag_dol.git
cd rag_dol
```

### 3. Upload Qdrant data (Large file - ไม่ push git):

```bash
# From local machine
scp qdrant_backup/qdrant_storage_20260219_092634.tar.gz \
  user@server:/opt/rag_dol/
```

### 4. Setup บนเซิร์ฟเวอร์:

```bash
# Extract
tar -xzf qdrant_storage_20260219_092634.tar.gz
mv qdrant_storage_20260219_092634 qdrant_storage

# Start
docker-compose -f docker-compose.production.yml up -d
```

---

## 📁 Structure บนเซิร์ฟเวอร์ (หลัง Deploy):

```
/opt/rag_dol/
├── langgraph_system/
│   ├── api_server_langgraph.py
│   ├── graph.py
│   ├── nodes.py
│   └── state.py
├── src/
│   ├── advanced_retrieval_engine.py
│   ├── embedding_engine.py
│   ├── bm25_indexer.py
│   └── reranker.py
├── rag_system/
│   └── memory.py
├── data/
│   └── bm25_vocabulary.pkl          # ⚠️ จำเป็น!
├── qdrant_storage/                   # ⚠️ จำเป็น! (จาก tar.gz)
│   └── collections/
│       └── land_chunks_hybrid/
├── docker-compose.production.yml
├── Dockerfile.production
├── requirements.production.txt
└── streaming_demo.html
```

---

## 🔍 Verification Steps:

```bash
# 1. Check Docker containers
docker ps

# Expected:
# qdrant_rag_dol  (port 6333, 6334)
# idin_api        (port 8001)

# 2. Check Qdrant data
curl http://localhost:6333/collections/land_chunks_hybrid | jq '.result.points_count'
# Expected: 3704

# 3. Check API health
curl http://localhost:8001/health | jq
# Expected: {"status":"healthy","langgraph":true}

# 4. Test chat
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-production",
    "query": "โฉนดที่ดินคืออะไร"
  }' | jq '.answer'

# 5. Check logs
docker-compose -f docker-compose.production.yml logs --tail=50 api
```

---

## 🎯 Quick Commands:

```bash
# View all logs
docker-compose -f docker-compose.production.yml logs -f

# Restart API only
docker-compose -f docker-compose.production.yml restart api

# Restart everything
docker-compose -f docker-compose.production.yml restart

# Stop all
docker-compose -f docker-compose.production.yml down

# Start all
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps
```

---

## 📊 Size Summary:

| Item | Size | Compressed |
|------|------|------------|
| **Qdrant Storage** | 2.3 GB | **80 MB** ✅ |
| **BM25 Vocab** | 460 KB | - |
| **Code** | ~50 MB | ~10 MB |
| **Docker Images** | ~2 GB | (pulled on server) |
| **Total Upload** | - | **~90 MB** 🎉 |

**ข้อดี:** Upload แค่ 90 MB แทนที่จะเป็น 2.3 GB!

---

## 🔒 Security Checklist (Production):

- [ ] เปลี่ยน API key ใน config หรือใช้ .env
- [ ] ตั้ง firewall (เปิดแค่ port 80/443)
- [ ] ติดตั้ง Nginx reverse proxy
- [ ] ติดตั้ง SSL certificate (Let's Encrypt)
- [ ] ตั้ง rate limiting
- [ ] Enable Docker logging rotation
- [ ] Backup Qdrant ทุกสัปดาห์

---

## 🆘 Common Issues:

### 1. API ไม่ Start

```bash
# Check logs
docker logs idin_api --tail=100

# Common fix: Missing files
ls -la data/bm25_vocabulary.pkl
ls -la qdrant_storage/
```

### 2. Qdrant ไม่มีข้อมูล

```bash
# Check
curl http://localhost:6333/collections

# Fix: Re-extract storage
tar -xzf qdrant_storage_*.tar.gz
mv qdrant_storage_* qdrant_storage
docker-compose restart qdrant
```

### 3. Memory Error

```bash
# Check memory
free -h

# Reduce workers in docker-compose.yml
# --workers 2 -> --workers 1
```

### 4. Port Already in Use

```bash
# Check what's using port
sudo lsof -i :8001
sudo lsof -i :6333

# Change ports in docker-compose.production.yml
```

---

## ✅ Success Indicators:

เมื่อ deploy สำเร็จ คุณจะเห็น:

1. ✅ `docker ps` แสดง 2 containers (qdrant + api)
2. ✅ `curl localhost:6333/collections` แสดง collection
3. ✅ `curl localhost:8001/health` return `{"status":"healthy"}`
4. ✅ Chat API ตอบคำถามได้ถูกต้อง
5. ✅ Streaming endpoint ทำงาน
6. ✅ Logs ไม่มี ERROR

---

## 📞 Need Help?

เจอปัญหา? ตรวจสอบ:
- Logs: `docker-compose logs -f`
- Health: `curl localhost:8001/health`
- Qdrant: `curl localhost:6333/collections`
- Disk: `df -h`
- Memory: `free -h`

---

**🎉 Ready to Deploy!** 

เริ่มด้วยคำสั่ง:
```bash
rsync -avz --progress ./ user@server:/opt/rag_dol/
```
