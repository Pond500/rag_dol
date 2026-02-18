# 🚀 Quick Deployment Guide

## สำหรับคนรีบ (5 นาที)

### บน Server
```bash
# 1. Setup (ครั้งเดียว)
bash setup_server.sh

# 2. Copy code
# (รันจาก local machine)
rsync -avz rag_dol/ user@server:~/rag_dol/

# 3. Copy data
rsync -avz data/ user@server:~/rag_dol/data/

# 4. Install dependencies (บน server)
cd ~/rag_dol
source venv/bin/activate
pip install -r requirements.txt

# 5. Run ETL
bash scripts/quick_start.sh

# 6. Export
python src/qdrant_export_import.py export
tar -czf exports.tar.gz exports/
```

### บน Local
```bash
# 1. Download
scp user@server:~/rag_dol/exports.tar.gz ./

# 2. Extract
tar -xzf exports.tar.gz

# 3. Import
python src/qdrant_export_import.py import

# เสร็จ! ✅
```

---

## 📖 Complete Guide

ดูเอกสารละเอียด: [SERVER_DEPLOYMENT_CHECKLIST.md](docs/SERVER_DEPLOYMENT_CHECKLIST.md)

---

## 🛠️ Requirements

### Server
- Ubuntu 20.04+ (หรือ Linux distro อื่น)
- Docker + Docker Compose
- Python 3.10+
- 4GB+ RAM (8GB+ แนะนำ)
- 20GB+ Disk space
- GPU (Optional - จะเร็วกว่ามาก)

### Local
- Docker + Docker Compose
- Python 3.10+
- Qdrant running (localhost:6333)

---

## 📦 Installation

### Method 1: Auto Setup (แนะนำ)
```bash
# บน Server
bash scripts/setup_server.sh
```

### Method 2: Manual Setup
ดู: [SERVER_DEPLOYMENT_CHECKLIST.md](docs/SERVER_DEPLOYMENT_CHECKLIST.md)

---

## 🎯 Workflow

```
┌─────────────┐
│   Server    │  1. รัน ETL (มี GPU/CPU แรง)
│   + GPU     │  2. Generate embeddings
└──────┬──────┘  3. Store in Qdrant
       │         4. Export to JSON
       │
       │ rsync/scp
       ↓
┌─────────────┐
│ exports.tar │  5. Transfer file
│   .gz       │
└──────┬──────┘
       │
       │ extract
       ↓
┌─────────────┐
│   Local     │  6. Import to local Qdrant
│  Machine    │  7. Use for queries
└─────────────┘
```

---

## ⚙️ Configuration

### สำหรับ CPU (bge-m3)
```env
EMBEDDING_MODEL_NAME=BAAI/bge-m3
EMBEDDING_DIMENSIONS=1024
EMBEDDING_DEVICE=cpu
EMBEDDING_BATCH_SIZE=16
```

### สำหรับ GPU (bge-multilingual-gemma2)
```env
EMBEDDING_MODEL_NAME=BAAI/bge-multilingual-gemma2
EMBEDDING_DIMENSIONS=3584
EMBEDDING_DEVICE=cuda
EMBEDDING_BATCH_SIZE=32
```

---

## 📊 Performance

| Setup | ETL Time (108 files) | Export | Transfer | Import | Total |
|-------|---------------------|--------|----------|--------|-------|
| CPU (bge-m3) | 30-60 min | 5 min | 10 min | 10 min | ~1-2 hrs |
| GPU (bge-m3) | 10-20 min | 5 min | 10 min | 10 min | ~30-45 min |
| GPU (gemma2) | 15-30 min | 5 min | 10 min | 10 min | ~40-60 min |

---

## 🔍 Verification

### ตรวจสอบบน Server
```bash
curl http://localhost:6333/collections/land_documents
curl http://localhost:6333/collections/land_chunks
```

### ตรวจสอบบน Local
```python
from src.qdrant_client_setup import QdrantManager

manager = QdrantManager()
docs = manager.client.get_collection('land_documents')
chunks = manager.client.get_collection('land_chunks')

print(f'Documents: {docs.points_count}')
print(f'Chunks: {chunks.points_count}')
```

---

## 🐛 Troubleshooting

### Docker Permission Denied
```bash
sudo usermod -aG docker $USER
# Logout และ login ใหม่
```

### Out of Memory
```bash
# ลด batch size
export EMBEDDING_BATCH_SIZE=4
```

### Slow Network
```bash
# ใช้ compression
tar -czf exports.tar.gz exports/
rsync -avz --compress-level=9
```

### GPU Not Working
```bash
# Check GPU
nvidia-smi

# Install CUDA PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## 📚 Documentation

- [Server Deployment Checklist](docs/SERVER_DEPLOYMENT_CHECKLIST.md)
- [Server-Local Sync Workflow](docs/SERVER_LOCAL_SYNC.md)
- [ETL Pipeline Documentation](src/etl_pipeline.py)

---

## 🆘 Support

### Common Commands

**Monitor ETL Progress:**
```bash
watch -n 10 'curl -s http://localhost:6333/collections/land_chunks | jq .result.points_count'
```

**Check Disk Space:**
```bash
df -h
du -sh rag_dol/
```

**View Logs:**
```bash
docker logs qdrant
tail -f etl.log
```

**Restart Everything:**
```bash
docker-compose down
docker-compose up -d
```

---

## 📝 Notes

- แนะนำใช้ `screen` หรือ `tmux` สำหรับรัน ETL ที่ใช้เวลานาน
- Export file อาจใหญ่ถึง 1-2GB (ขึ้นกับจำนวนเอกสาร)
- ใช้ `rsync` แทน `scp` สำหรับ resume ได้
- GPU จะเร็วกว่า CPU ประมาณ 3-5 เท่า

---

## 🎉 Success Checklist

- [ ] Server setup complete
- [ ] Code และ data อยู่บน server
- [ ] Qdrant running
- [ ] ETL เสร็จสมบูรณ์
- [ ] Export ได้ไฟล์ JSON
- [ ] Download มา local สำเร็จ
- [ ] Import เข้า local Qdrant สำเร็จ
- [ ] Query ได้ผลลัพธ์

**ถ้าครบทุกข้อ = พร้อมใช้งาน! 🎊**
