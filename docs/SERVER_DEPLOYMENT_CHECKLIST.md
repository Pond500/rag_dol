# Server Deployment Checklist

## ✅ Pre-Deployment (Local)

- [ ] ทดสอบ ETL ใน local ให้สำเร็จก่อน (3 ไฟล์)
- [ ] ตรวจสอบว่า requirements.txt ครบถ้วน
- [ ] Commit code ลง Git (หรือเตรียม tar.gz)
- [ ] เตรียมข้อมูล (data/ folder)

## 📤 Server Setup

- [ ] SSH เข้า server ได้
- [ ] ติดตั้ง Docker + Docker Compose
- [ ] ติดตั้ง Python 3.10+ และ pip
- [ ] ติดตั้ง Git (ถ้าใช้)
- [ ] เช็ค GPU (ถ้ามี): `nvidia-smi`

## 📥 Code Transfer

- [ ] Copy โค้ดไปที่ server (rsync/scp/git)
- [ ] Copy ข้อมูลไปที่ server (data/)
- [ ] ตรวจสอบ structure: `tree -L 2`

## 🔧 Environment Setup

- [ ] สร้าง virtual environment: `python3 -m venv venv`
- [ ] Activate: `source venv/bin/activate`
- [ ] ติดตั้ง dependencies: `pip install -r requirements.txt`
- [ ] สร้าง .env file
- [ ] แก้ config (GPU/CPU, batch size)

## 🗄️ Database Setup

- [ ] Start Qdrant: `docker-compose up -d`
- [ ] ตรวจสอบ Qdrant: `curl http://localhost:6333`
- [ ] สร้าง collections: `python -c "from src.qdrant_client_setup ..."`
- [ ] ตรวจสอบ collections: `docker logs qdrant`

## 🚀 Run ETL

- [ ] Test run (3 files): `python src/etl_pipeline.py`
- [ ] ตรวจสอบ logs
- [ ] ตรวจสอบว่ามีข้อมูลใน Qdrant
- [ ] Full run: แก้ `limit=None` ใน etl_pipeline.py
- [ ] รันใน screen/tmux: `screen -S etl`
- [ ] Monitor: `watch -n 60 'curl -s http://localhost:6333/collections/land_chunks | jq .result.points_count'`

## 📦 Export Data

- [ ] รอ ETL เสร็จ
- [ ] Export: `python src/qdrant_export_import.py export`
- [ ] ตรวจสอบขนาดไฟล์: `ls -lh exports/`
- [ ] Compress: `tar -czf exports.tar.gz exports/`
- [ ] ตรวจสอบไฟล์ compress: `ls -lh exports.tar.gz`

## 📥 Download to Local

- [ ] Download: `scp user@server:/path/to/exports.tar.gz ./`
- [ ] Extract: `tar -xzf exports.tar.gz`
- [ ] ตรวจสอบไฟล์ JSON: `ls -lh exports/`
- [ ] Validate JSON: `python -c "import json; json.load(open('exports/land_documents.json'))"`

## 📥 Import to Local

- [ ] Start local Qdrant: `docker-compose up -d`
- [ ] Import: `python src/qdrant_export_import.py import`
- [ ] ตรวจสอบข้อมูล: จำนวน documents & chunks
- [ ] Test query: ทดสอบ search

## 🧹 Cleanup (Optional)

- [ ] ลบไฟล์ชั่วคราวบน server: `rm -rf exports/ exports.tar.gz`
- [ ] Stop Qdrant บน server: `docker-compose down`
- [ ] ลบข้อมูลบน server: `docker volume rm rag_dol_qdrant_storage`

---

## 🔍 Troubleshooting Commands

### ตรวจสอบ Qdrant
```bash
curl http://localhost:6333
curl http://localhost:6333/collections
curl http://localhost:6333/collections/land_documents
```

### ตรวจสอบ Docker
```bash
docker ps
docker logs qdrant
docker stats
```

### ตรวจสอบ Python Environment
```bash
which python
python --version
pip list | grep -E "(qdrant|sentence|torch)"
```

### ตรวจสอบ GPU
```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

### Monitor ETL Progress
```bash
# ดูจำนวน chunks ที่ upload แล้ว
watch -n 10 'curl -s http://localhost:6333/collections/land_chunks | jq .result.points_count'

# ดู CPU/Memory usage
htop

# ดู Disk usage
df -h
du -sh rag_dol/
```

---

## ⏱️ Estimated Time

| Task | CPU (bge-m3) | GPU (bge-multilingual-gemma2) |
|------|--------------|-------------------------------|
| Setup | 30 min | 30 min |
| Download Model | 10 min | 60 min (37GB) |
| ETL (108 files) | 30-60 min | 15-30 min |
| Export | 5 min | 5 min |
| Transfer (1GB) | 5-30 min | 5-30 min |
| Import | 5-10 min | 5-10 min |
| **Total** | **~2-3 hours** | **~2 hours** |

---

## 📞 Quick Commands

```bash
# บน Server - Quick Start
cd ~/rag_dol
source venv/bin/activate
docker-compose up -d
python src/etl_pipeline.py

# บน Local - Quick Import
cd /Users/pond500/RAG/rag_dol
python src/qdrant_export_import.py import
```

---

## 🆘 Common Issues

### 1. Out of Memory
```bash
# ลด batch size ใน .env
EMBEDDING_BATCH_SIZE=4  # แทน 16
```

### 2. Docker Permission Denied
```bash
sudo usermod -aG docker $USER
# Logout และ login ใหม่
```

### 3. Port Already in Use
```bash
# เปลี่ยน port ใน docker-compose.yml
ports:
  - "6334:6333"  # แทน 6333:6333
```

### 4. Slow Transfer
```bash
# ใช้ rsync แทน scp
rsync -avz --compress-level=9 --progress exports/ user@local:/path/
```

### 5. JSON Too Large
```bash
# Export แยก collection
python -c "
from src.qdrant_export_import import QdrantExporter
exp = QdrantExporter()
exp.export_collection('land_documents', 'docs.json')
exp.export_collection('land_chunks', 'chunks.json')
"
```
