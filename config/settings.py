"""
Configuration settings for RAG DOL
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SRC_DIR = BASE_DIR / "src"
CONFIG_DIR = BASE_DIR / "config"

# Qdrant settings
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)

# Collection names
COLLECTION_DOCUMENTS = os.getenv("COLLECTION_DOCUMENTS", "land_documents")
COLLECTION_CHUNKS = os.getenv("COLLECTION_CHUNKS", "land_chunks")

# Embedding Model settings (BGE-M3)
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", 1024))  # BGE-M3 = 1024 dims
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")  # "cpu" or "cuda" or "mps"
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", 16))  # Can use larger batch with smaller model

# Chunking configuration
CHUNK_SIZE_MIN = int(os.getenv("CHUNK_SIZE_MIN", 200))
CHUNK_SIZE_MAX = int(os.getenv("CHUNK_SIZE_MAX", 1000))
CHUNK_SIZE_TARGET = int(os.getenv("CHUNK_SIZE_TARGET", 600))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150))  # เพิ่ม overlap จาก 100 → 150

# Special configurations
TABLE_MAX_TOKENS = 1500
LIST_MAX_TOKENS = 1200
LEGAL_MAX_TOKENS = 800

# Document type patterns
DOCUMENT_TYPES = {
    "คู่มือปชช": "คู่มือสำหรับประชาชน",
    "คู่มือเจ้าหน้าที่": "การจดทะเบียน",
    "ระเบียบกรม": "ระเบียบกรมที่ดิน",
    "กฎหมาย": "พระราชบัญญัติ"
}

# Category mappings
CATEGORIES = {
    "การโอน": ["โอน", "ขาย", "ซื้อ", "transfer"],
    "ภาระผูกพัน": ["จำนอง", "เช่า", "mortgage"],
    "อื่นๆ": ["อายัด", "แก้ไข", "ตรวจสอบ"],
    "ระเบียบ": ["ระเบียบ", "คำสั่ง"]
}
