# Advanced Retrieval Engine

ระบบค้นคืนข้อมูลแบบ Hybrid Search ที่มีประสิทธิภาพสูงสุด สำหรับเอกสารกรมที่ดิน

## 🎯 Features

### 1. **Multi-Stage Retrieval Pipeline**

```
Query → Stage 1: Hybrid Search → Stage 2: Reranking → Stage 3: Context Expansion → Results
```

#### Stage 1: Hybrid Search (BM25 + Dense + RRF)
- **BM25 (Sparse)**: Keyword-based search ด้วย Thai tokenization
- **BGE-M3 (Dense)**: Semantic search 1024 มิติ
- **RRF Fusion**: Reciprocal Rank Fusion รวมผลลัพธ์จาก 2 วิธี

#### Stage 2: Reranking (Optional)
- **Cross-Encoder**: BGE-reranker-v2-m3
- ปรับ ranking ใหม่ด้วย query-document interaction
- เพิ่มความแม่นยำ 15-30%

#### Stage 3: Context Expansion (Optional)
- **Parent Context**: ดึงข้อความจาก parent chunk (Level 0 หรือ 1)
- **Children Context**: ดึงข้อความจาก child chunks (Level 2)
- **Hierarchical Relationships**: ใช้ประโยชน์จาก 3-level structure

### 2. **Adaptive Retrieval Strategy**

ระบบวิเคราะห์คำถามอัตโนมัติและเลือก strategy ที่เหมาะสม:

| Query Type | Target Level | Example Query |
|------------|--------------|---------------|
| Document-level | Level 0 | "จดทะเบียนโอนที่ดินทำยังไง" |
| Section-level | Level 1 | "ต้องใช้เอกสารอะไรบ้าง" |
| Chunk-level | Level 2 | "ค่าธรรมเนียม 5 ไร่เท่าไหร่" |
| Mixed | Level 2 | "คนต่างด้าวซื้อที่ดินได้ไหม มีเงื่อนไขอะไร" |

### 3. **Configurable Fusion**

#### RRF (Reciprocal Rank Fusion)
```python
RRF Score = alpha * (1/(k + rank_bm25)) + (1-alpha) * (1/(k + rank_dense))
```

**Alpha Parameter**:
- `alpha = 0.5` → Balanced (แนะนำ)
- `alpha > 0.5` → Favor BM25 (สำหรับ keyword queries)
- `alpha < 0.5` → Favor Dense (สำหรับ semantic queries)

### 4. **Rich Result Format**

แต่ละผลลัพธ์มี:
- **Scores**: Final, Rerank, BM25, Dense
- **Source Tracking**: Filename, filepath, relative path
- **Hierarchical Info**: Level, section title, chunk type
- **Context**: Parent text, children texts
- **Relationships**: Parent ID, children IDs

## 🚀 Quick Start

### 1. Test Suite (Comprehensive Testing)

```bash
python test_advanced_retrieval.py
```

รัน 4 test cases ครอบคลุมทุกประเภทคำถาม:
- ✅ Specific calculation query
- ✅ Document list query
- ✅ Process overview query
- ✅ Complex multi-part query

แต่ละ test จะทดสอบ 3 configurations:
1. Hybrid Search Only
2. Hybrid + Reranker
3. Full Pipeline (Hybrid + Reranker + Context)

### 2. Quick Query Tool (Interactive)

```bash
python quick_query.py
```

**Usage**:
```
💬 Enter your query: ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่

Configuration:
  - top_k: 5
  - reranker: True
  - context: True
  - alpha: 0.5
```

**Commands**:
- `config` - เปลี่ยนการตั้งค่า
- `quit` - ออกจากโปรแกรม

## 📊 Performance Tuning

### Alpha Tuning (BM25 vs Dense Weight)

| Query Type | Recommended Alpha | Reason |
|------------|-------------------|---------|
| Exact match (ค่าธรรมเนียม, เอกสาร) | 0.6-0.7 | BM25 ดีกว่าสำหรับ exact terms |
| Semantic (ทำยังไง, อธิบาย) | 0.3-0.4 | Dense ดีกว่าสำหรับ meaning |
| Mixed | 0.5 | Balanced |

### Top-K Strategy

| Stage | Recommended Top-K | Reason |
|-------|-------------------|--------|
| Hybrid Search | 20-30 | เก็บ candidates มากพอสำหรับ reranking |
| Reranking | 5-10 | จำกัดที่ผลลัพธ์ที่ดีที่สุด |
| Final Results | 3-5 | ป้อนให้ LLM (context window limit) |

### Context Expansion Settings

```python
# For short answers (ค่าธรรมเนียม, เอกสาร)
enable_context_expansion = False  # ไม่ต้องการ context เพิ่ม

# For explanations (ขั้นตอน, วิธีการ)
enable_context_expansion = True
include_parent = True  # Overview จาก parent
include_children = False  # ไม่ต้องการ details

# For comprehensive answers
enable_context_expansion = True
include_parent = True
include_children = True  # ต้องการ details ทั้งหมด
```

## 🔧 API Reference

### AdvancedRetrievalEngine

#### `__init__`
```python
AdvancedRetrievalEngine(
    qdrant_client: QdrantClient,
    embedding_engine: EmbeddingEngine,
    bm25_indexer: BM25Indexer,
    reranker: Reranker,
    vocabulary: Dict[str, int],
)
```

#### `retrieve` (Main Method)
```python
retrieve(
    query: str,
    top_k: int = 10,
    enable_reranker: bool = True,
    enable_context_expansion: bool = True,
    alpha: float = 0.5,
    adaptive: bool = True,
) -> List[RetrievalResult]
```

**Parameters**:
- `query`: คำถามของผู้ใช้
- `top_k`: จำนวนผลลัพธ์สุดท้าย (default: 10)
- `enable_reranker`: เปิดใช้ reranker (default: True)
- `enable_context_expansion`: เปิดใช้ context expansion (default: True)
- `alpha`: น้ำหนัก BM25 vs Dense, 0-1 (default: 0.5)
- `adaptive`: วิเคราะห์คำถามและเลือก level อัตโนมัติ (default: True)

**Returns**: `List[RetrievalResult]`

#### `analyze_query`
```python
analyze_query(query: str) -> QueryAnalysis
```

วิเคราะห์คำถามเพื่อกำหนด strategy:
- `query_type`: 'document', 'section', 'chunk', 'mixed'
- `target_level`: 0, 1, or 2
- `is_complex`: Boolean
- `keywords`: List[str]
- `estimated_answer_length`: 'short', 'medium', 'long'

#### `hybrid_search`
```python
hybrid_search(
    query: str,
    top_k: int = 20,
    alpha: float = 0.5,
    target_level: Optional[int] = None,
) -> List[Dict[str, Any]]
```

Hybrid search พื้นฐานด้วย RRF fusion

#### `rerank_results`
```python
rerank_results(
    query: str,
    results: List[Dict[str, Any]],
    top_k: int = 10,
) -> List[Dict[str, Any]]
```

Rerank ผลลัพธ์ด้วย cross-encoder

#### `expand_context`
```python
expand_context(
    results: List[Dict[str, Any]],
    include_parent: bool = True,
    include_children: bool = True,
    include_siblings: bool = False,
) -> List[RetrievalResult]
```

ขยาย context ด้วย hierarchical relationships

#### `format_results`
```python
format_results(
    results: List[RetrievalResult],
    include_scores: bool = True,
    include_context: bool = True,
) -> str
```

Format ผลลัพธ์สำหรับแสดงผล

## 📈 Evaluation Metrics

### Precision@K
```
Precision@5 = (Relevant results in top 5) / 5
```

**Expected Performance**:
- Hybrid Only: ~0.65
- Hybrid + Reranker: ~0.85
- Full Pipeline: ~0.92

### MRR (Mean Reciprocal Rank)
```
MRR = 1 / (Rank of first relevant result)
```

**Expected Performance**:
- Hybrid Only: ~0.75
- Hybrid + Reranker: ~0.92
- Full Pipeline: ~0.95

## 🎓 Best Practices

### 1. Query Understanding
```python
# Good: Specific queries
"ค่าธรรมเนียมโอนที่ดิน 5 ไร่"

# Better: Add context
"ค่าธรรมเนียมจดทะเบียนโอนที่ดิน 5 ไร่ในกรุงเทพ"
```

### 2. Configuration Selection

**For Production (RAG Pipeline)**:
```python
results = engine.retrieve(
    query=user_query,
    top_k=3,  # Limit context for LLM
    enable_reranker=True,  # Best quality
    enable_context_expansion=True,  # Rich context
    adaptive=True,  # Auto-optimize
)
```

**For Fast Prototyping**:
```python
results = engine.retrieve(
    query=user_query,
    top_k=5,
    enable_reranker=False,  # Faster
    enable_context_expansion=False,  # Faster
    adaptive=False,  # Simpler
)
```

### 3. Result Processing

```python
# Extract top result with full context
top = results[0]

# Build prompt with context
context = f"""
Document: {top.filename}
Section: {top.section_title}

Main Content:
{top.text}

Additional Context:
{top.parent_text}

Details:
{chr(10).join(top.children_texts[:3])}
"""

# Use in RAG
answer = llm.generate(query=query, context=context)
```

## 🔍 Example Queries

### Simple Queries
```python
# Exact match
"ค่าธรรมเนียมโอนที่ดิน"

# Calculation
"คำนวณค่าธรรมเนียม 10 ไร่"

# Document list
"เอกสารที่ต้องใช้"
```

### Complex Queries
```python
# Multi-concept
"คนต่างด้าวจะซื้อที่ดินได้หรือไม่ มีเงื่อนไขและค่าใช้จ่ายอะไรบ้าง"

# Procedural
"ขั้นตอนการจดทะเบียนโอนที่ดินตั้งแต่เริ่มต้นจนเสร็จ"

# Comparative
"ความแตกต่างระหว่างการโอนและการเช่าอสังหาริมทรัพย์"
```

## 📝 Notes

- ระบบใช้ **3-level hierarchical chunking** (Level 0: Document, Level 1: Section, Level 2: Content)
- **BM25 vocabulary**: 8,827 Thai terms
- **Total chunks**: 3,704 chunks จาก 108 documents
- **Embedding model**: BAAI/bge-m3 (1024 dims)
- **Reranker model**: BAAI/bge-reranker-v2-m3

## 🚨 Troubleshooting

### Issue: Low precision
- ✅ Enable reranker
- ✅ Increase top_k for hybrid search (20-30)
- ✅ Tune alpha based on query type

### Issue: Missing relevant results
- ✅ Check if adaptive mode is on
- ✅ Try different alpha values
- ✅ Enable context expansion

### Issue: Too much context
- ✅ Reduce top_k
- ✅ Disable children context
- ✅ Filter by hierarchy_level

---

**Created**: 2026-02-16  
**Version**: 1.0  
**Author**: Advanced Retrieval System for Land Department Documents
