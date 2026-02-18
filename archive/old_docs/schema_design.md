# Vector Database Schema & Chunking Strategy Design
## สำหรับระบบ RAG ข้อมูลกรมที่ดิน

วันที่: 12 กุมภาพันธ์ 2026

---

## 📊 1. Vector Database Schema Design

### 1.1 Collection Structure

```python
# แนะนำใช้ 2 Collections แยกกัน

Collection 1: "documents" (Document-level)
├── document_id
├── document_embedding (1536 dims)
└── document_metadata

Collection 2: "chunks" (Chunk-level) 
├── chunk_id
├── chunk_embedding (1536 dims)
├── chunk_metadata
└── parent_document_id (FK)
```

### 1.2 Detailed Schema

#### **Collection: documents**

```json
{
  "_id": "doc_001",
  "embedding": [0.123, 0.456, ...],  // Dense vector (OpenAI: 1536d, Cohere: 1024d)
  
  "metadata": {
    // === ข้อมูลเอกสาร ===
    "title": "จดทะเบียนประเภทโอนอสังหาริมทรัพย์กรณีไม่ต้องประกาศ",
    "document_type": "คู่มือปชช",  // คู่มือปชช | ระเบียบกรม | กฎหมาย | คู่มือเจ้าหน้าที่
    "file_path": "data/คู่มือปชช.รายละเอียดเนื้อหา/1.จดทะเบียน...",
    "file_size_kb": 45.2,
    "version": "N",  // N=New, หรือวันที่ปรับปรุง
    
    // === หมวดหมู่ ===
    "category_level1": "การโอน",  // การโอน | ภาระผูกพัน | อื่นๆ | ระเบียบ
    "category_level2": "โอนอสังหาริมทรัพย์",
    "category_level3": "ไม่ต้องประกาศ",
    "keywords": ["โอน", "ขาย", "ที่ดิน", "ห้องชุด", "โฉนด"],
    
    // === รายละเอียดบริการ ===
    "service_info": {
      "requires_announcement": false,
      "processing_time_minutes": 150,
      "processing_time_text": "150 นาที",
      "alternative_time_minutes": 60,  // กรณี e-QLands
      "alternative_time_text": "60 นาที (e-QLands)",
      "service_location": "สำนักงานที่ดิน",
      "office_hours": "08:30-16:30 น. วันจันทร์-ศุกร์"
    },
    
    // === ค่าธรรมเนียม ===
    "fees": [
      {
        "item": "ค่าคำขอ (ที่ดิน)",
        "amount": 5,
        "unit": "บาท",
        "type": "fixed",
        "per": "แปลง"
      },
      {
        "item": "ค่าธรรมเนียม",
        "amount": 2,
        "unit": "เปอร์เซ็นต์",
        "type": "percentage",
        "base": "ราคาประเมิน"
      }
    ],
    "total_fee_types": ["ค่าคำขอ", "ค่าธรรมเนียม", "ภาษี"],
    
    // === เอกสารที่ใช้ ===
    "required_documents": [
      {
        "name": "โฉนดที่ดิน",
        "type": "ต้นฉบับ",
        "copies": 1,
        "is_required": true
      },
      {
        "name": "บัตรประจำตัวประชาชน",
        "type": "ต้นฉบับ",
        "copies": 1,
        "is_required": true
      }
    ],
    "document_count": 22,
    
    // === กฎหมายที่เกี่ยวข้อง ===
    "legal_references": [
      {
        "law_type": "พ.ร.บ.",
        "law_name": "ประมวลกฎหมายที่ดิน",
        "year": "2497",
        "section": null
      },
      {
        "law_type": "กฎกระทรวง",
        "law_name": "กฎกระทรวงฉบับที่ 7",
        "year": "2497",
        "section": null
      }
    ],
    
    // === เงื่อนไขพิเศษ ===
    "conditions": {
      "applicable_to": ["บุคคลธรรมดา", "นิติบุคคล"],
      "restrictions": [
        "ผู้โอนต้องเป็นเจ้าของที่ดิน",
        "ผู้รับโอนต้องเป็นคนไทย (เว้นแต่กรณีพิเศษ)"
      ],
      "special_cases": ["คนต่างด้าว", "นิติบุคคลต่างด้าว"],
      "requires_court_order": false,
      "requires_consent": true,
      "consent_from": ["คู่สมรส"]
    },
    
    // === ขั้นตอน ===
    "steps": [
      {
        "step_number": 1,
        "title": "การพิจารณา",
        "duration_minutes": 110,
        "description": "ยื่นคำขอ - ตรวจเอกสาร - รับคำขอและสอบสวน..."
      },
      {
        "step_number": 2,
        "title": "การลงนาม",
        "duration_minutes": 40,
        "description": "เจ้าพนักงานที่ดินตรวจสอบ..."
      }
    ],
    
    // === สถิติและ Metrics ===
    "statistics": {
      "word_count": 3250,
      "line_count": 154,
      "char_count": 15234,
      "chunk_count": 8,
      "table_count": 3,
      "list_count": 5
    },
    
    // === สำหรับ Search ===
    "search_terms": [
      "โอนที่ดิน", "ขายที่ดิน", "โอนห้องชุด", "ขายห้องชุด",
      "จดทะเบียนโอน", "ไม่ต้องประกาศ"
    ],
    "synonyms": {
      "โอน": ["ขาย", "โอนกรรมสิทธิ์", "transfer"],
      "ที่ดิน": ["โฉนด", "อสังหาริมทรัพย์", "land"],
      "ห้องชุด": ["คอนโด", "condominium"]
    },
    
    // === Timestamps ===
    "created_at": "2026-02-12T10:00:00Z",
    "updated_at": "2026-02-12T10:00:00Z",
    "indexed_at": "2026-02-12T10:05:00Z",
    
    // === Status ===
    "status": "active",  // active | archived | outdated
    "is_latest": true,
    "related_documents": ["doc_002", "doc_003"]
  }
}
```

#### **Collection: chunks**

```json
{
  "_id": "chunk_001_001",
  "embedding": [0.789, 0.012, ...],
  
  "metadata": {
    // === Chunk Identity ===
    "parent_document_id": "doc_001",
    "chunk_index": 1,
    "chunk_type": "criteria",  // criteria | documents | fees | steps | legal | table | contact
    
    // === Content ===
    "text": "หลักเกณฑ์ วิธีการ เงื่อนไข...",
    "text_length": 850,
    "language": "th",
    
    // === Position ===
    "start_line": 5,
    "end_line": 28,
    "position_in_doc": "beginning",  // beginning | middle | end
    
    // === Context ===
    "section_title": "หลักเกณฑ์ วิธีการ เงื่อนไข",
    "subsection": null,
    "previous_chunk_id": null,
    "next_chunk_id": "chunk_001_002",
    
    // === Inherit from Parent ===
    "document_title": "จดทะเบียนประเภทโอนอสังหาริมทรัพย์...",
    "document_type": "คู่มือปชช",
    "category_level1": "การโอน",
    "keywords": ["โอน", "ขาย", "ที่ดิน"],
    
    // === Specific Entities ===
    "entities": {
      "laws": ["พ.ร.บ. ที่ดิน พ.ศ. 2497", "ป.พ.พ. มาตรา 1382"],
      "documents": ["โฉนดที่ดิน", "บัตรประชาชน"],
      "fees": ["5 บาท", "2%"],
      "duration": ["150 นาที", "60 นาที"],
      "organizations": ["กรมที่ดิน", "สำนักงานที่ดิน"]
    },
    
    // === Content Features ===
    "has_table": false,
    "has_list": true,
    "has_legal_ref": true,
    "has_example": false,
    "has_calculation": false,
    
    // === Importance Score ===
    "importance_score": 0.85,  // 0-1
    "is_key_information": true,
    
    // === Timestamps ===
    "created_at": "2026-02-12T10:05:00Z",
    "updated_at": "2026-02-12T10:05:00Z"
  }
}
```

---

## 🔪 2. Chunking Strategy

### 2.1 Overview

```
Strategy: Hybrid Semantic + Structural Chunking

Primary Method: Content-Aware Sectioning
Fallback Method: Sliding Window with Overlap
```

### 2.2 Chunking Rules

#### **Rule 1: Section-Based Chunking** (ลำดับแรก)

```python
# แบ่งตามโครงสร้างหลัก
chunks = [
    {
        "type": "header",
        "content": "คู่มือสำหรับประชาชน : {title}"
    },
    {
        "type": "criteria",
        "content": "หลักเกณฑ์ วิธีการ เงื่อนไข...",
        "max_tokens": 1000
    },
    {
        "type": "channels",
        "content": "ช่องทางการให้บริการ...",
        "max_tokens": 500
    },
    {
        "type": "steps",
        "content": "ขั้นตอน ระยะเวลา...",
        "max_tokens": 800
    },
    {
        "type": "documents",
        "content": "รายการเอกสารหลักฐาน...",
        "max_tokens": 1200
    },
    {
        "type": "fees",
        "content": "ค่าธรรมเนียม...",
        "max_tokens": 600
    },
    {
        "type": "complaints",
        "content": "ช่องทางการร้องเรียน...",
        "max_tokens": 400
    }
]
```

#### **Rule 2: Table Preservation** (สำคัญมาก!)

```python
# ห้ามตัดตารางเด็ดขาด!
if contains_table(section):
    # Option A: เก็บทั้งตาราง
    chunk = extract_complete_table(section)
    
    # Option B: แปลงเป็น Markdown
    chunk = table_to_markdown(section)
    
    # Option C: แปลงเป็น Key-Value
    chunk = table_to_structured_data(section)
```

#### **Rule 3: List Handling**

```python
# รักษาความต่อเนื่องของรายการ
if contains_numbered_list(section):
    # เก็บรายการครบ
    chunk = extract_complete_list(section)
    
    # หรือถ้ายาวเกิน แบ่งเป็นกลุ่มๆ
    if len(chunk) > max_tokens:
        sub_chunks = split_list_logically(chunk)
```

#### **Rule 4: Legal Reference Integrity**

```python
# รักษาความสมบูรณ์ของการอ้างอิงกฎหมาย
if contains_legal_reference(text):
    # เก็บบริบทรอบๆ การอ้างอิง
    chunk = extract_with_context(
        text, 
        reference,
        context_before=100,
        context_after=100
    )
```

### 2.3 Chunk Size Guidelines

```python
CHUNK_SETTINGS = {
    "min_chunk_size": 200,      # tokens
    "max_chunk_size": 1000,     # tokens
    "target_chunk_size": 600,   # tokens (sweet spot)
    
    "overlap_size": 100,        # tokens
    "overlap_percentage": 0.15, # 15%
    
    # Special handling
    "table_max_size": 1500,     # ตารางอาจยาวกว่า
    "list_max_size": 1200,      # รายการอาจยาวกว่า
    "legal_context": 150,       # context รอบกฎหมาย
}
```

### 2.4 Chunking Algorithm (Pseudocode)

```python
def chunk_document(document):
    chunks = []
    
    # 1. Parse structure
    sections = parse_document_structure(document)
    
    for section in sections:
        section_type = identify_section_type(section)
        
        # 2. Section-based chunking
        if section_type == "table":
            chunk = handle_table(section)
            chunks.append(chunk)
            
        elif section_type == "list":
            if len(section) > MAX_CHUNK_SIZE:
                sub_chunks = split_list(section)
                chunks.extend(sub_chunks)
            else:
                chunks.append(section)
                
        elif section_type == "criteria":
            # ข้อความยาว ใช้ semantic split
            sub_chunks = semantic_split(
                section,
                max_size=TARGET_CHUNK_SIZE,
                overlap=OVERLAP_SIZE
            )
            chunks.extend(sub_chunks)
            
        elif section_type == "legal":
            # รักษา legal context
            chunk = preserve_legal_context(section)
            chunks.append(chunk)
            
        else:
            # Default: sliding window
            sub_chunks = sliding_window_split(
                section,
                window_size=TARGET_CHUNK_SIZE,
                overlap=OVERLAP_SIZE
            )
            chunks.extend(sub_chunks)
    
    # 3. Post-processing
    chunks = add_metadata(chunks)
    chunks = add_cross_references(chunks)
    chunks = calculate_importance(chunks)
    
    return chunks
```

---

## 🎯 3. Chunking Examples

### Example 1: หลักเกณฑ์ (Criteria Section)

**Original (ยาว ~1,500 tokens):**
```
หลักเกณฑ์ วิธีการ เงื่อนไข (ถ้ามี) ในการยื่นคำขอ และในการพิจารณาอนุญาต

1.กรณียื่นคำขอและจดทะเบียนเสร็จในวันเดียว...
2.การขอจดทะเบียนประเภทการโอน...
3.ผู้โอนจะต้องเป็นเจ้าของที่ดิน...
...
```

**Chunked (แบ่งเป็น 2-3 chunks):**

```python
# Chunk 1: Overview + กรณีทั่วไป (600 tokens)
chunk_1 = {
    "text": """หลักเกณฑ์ วิธีการ เงื่อนไข (ถ้ามี) ในการยื่นคำขอ...
    1.กรณียื่นคำขอและจดทะเบียนเสร็จในวันเดียว...
    2.การขอจดทะเบียนประเภทการโอน...""",
    "type": "criteria_general",
    "importance": 0.95
}

# Chunk 2: คุณสมบัติและเงื่อนไข (650 tokens)
chunk_2 = {
    "text": """3.ผู้โอนจะต้องเป็นเจ้าของที่ดิน...
    4.หากเป็นการโอนที่ดินพร้อมสิ่งปลูกสร้าง...
    5.ผู้ขอต้องยื่นเอกสารหลักฐาน...""",
    "type": "criteria_requirements",
    "importance": 0.90,
    "previous_chunk": "chunk_1"
}

# Chunk 3: ระยะเวลาและกระบวนการ (550 tokens)
chunk_3 = {
    "text": """6.พนักงานเจ้าหน้าที่ต้องสอบสวน...
    7.ระยะเวลาดำเนินการอาจใช้เวลาน้อยกว่า 150 นาที...""",
    "type": "criteria_process",
    "importance": 0.85,
    "previous_chunk": "chunk_2"
}
```

### Example 2: ตารางค่าธรรมเนียม (Table)

**Original:**
```html
<table>
  <tr>
    <td>ลำดับ</td>
    <td>รายละเอียดค่าธรรมเนียม</td>
    <td>ค่าธรรมเนียม (บาท / ร้อยละ)</td>
  </tr>
  <tr>
    <td>1)</td>
    <td>ค่าคำขอ (กรณีที่ดิน) แปลงละ 5 บาท</td>
    <td>5 บาท</td>
  </tr>
  ...
</table>
```

**Chunked (เก็บทั้งตาราง + แปลงเป็น text):**

```python
chunk_table = {
    "text": """ค่าธรรมเนียม:
    
    1. ค่าคำขอ (กรณีที่ดิน): 5 บาท ต่อแปลง
    2. ค่าคำขอ (กรณีห้องชุด): 20 บาท ต่อห้อง
    3. ค่าธรรมเนียม: 2% ของราคาประเมิน
    4. ค่าธรรมเนียม (กรณีให้ระหว่างบุพการี): 0.5% ของราคาประเมิน
    ...""",
    "type": "fees_table",
    "structured_data": {
        "fees": [
            {"item": "ค่าคำขอ (ที่ดิน)", "amount": 5, "unit": "บาท"},
            {"item": "ค่าคำขอ (ห้องชุด)", "amount": 20, "unit": "บาท"},
            {"item": "ค่าธรรมเนียม", "amount": 2, "unit": "%"}
        ]
    },
    "importance": 0.95
}
```

### Example 3: รายการเอกสาร (Long List)

**Original (22 items):**
```
รายการเอกสาร หลักฐานประกอบ

1) โฉนดที่ดิน... ฉบับจริง1ฉบับ
2) บัตรประจำตัวประชาชน... ฉบับจริง1ฉบับ
...
22) หนังสือมอบอำนาจ... ฉบับจริง1ฉบับ
```

**Chunked (แบ่งเป็น 2 chunks แต่มี overlap):**

```python
# Chunk 1: เอกสารหลักและทั่วไป (items 1-12)
chunk_docs_1 = {
    "text": """รายการเอกสารหลักฐานประกอบ:
    
    1) โฉนดที่ดิน (ต้นฉบับ) - ฉบับจริง 1 ฉบับ
    2) บัตรประจำตัวประชาชน (ต้นฉบับ) - ฉบับจริง 1 ฉบับ
    ...
    12) กรณีคนไทยที่มีคู่สมรสต่างด้าว...""",
    "type": "documents_general",
    "importance": 0.90
}

# Chunk 2: เอกสารพิเศษและเงื่อนไข (items 10-22, overlap 10-12)
chunk_docs_2 = {
    "text": """เอกสารพิเศษและกรณีเฉพาะ:
    
    10) กรณีคนไทยที่มีคู่สมรสต่างด้าว...
    11) กรณีคนไทยที่มีคู่สมรสต่างด้าวขอซื้อห้องชุด...
    ...
    22) หนังสือมอบอำนาจ (กรณีนิติบุคคล)...""",
    "type": "documents_special",
    "importance": 0.75,
    "previous_chunk": "chunk_docs_1"
}
```

---

## 🔍 4. Indexing Strategy

### 4.1 Multiple Index Types

```python
INDEXES = {
    # 1. Dense Vector Index (Semantic Search)
    "vector_index": {
        "type": "HNSW",  # Hierarchical Navigable Small World
        "metric": "cosine",
        "ef_construction": 200,
        "m": 16
    },
    
    # 2. Sparse Vector Index (Keyword Search - BM25)
    "sparse_index": {
        "type": "inverted_index",
        "tokenizer": "thai_tokenizer",  # pythainlp
        "stopwords": True
    },
    
    # 3. Metadata Filters
    "filter_indexes": [
        "document_type",
        "category_level1",
        "category_level2",
        "service_info.requires_announcement",
        "status"
    ],
    
    # 4. Full-Text Search Index
    "fts_index": {
        "fields": ["title", "text", "search_terms"],
        "language": "thai"
    }
}
```

### 4.2 Hybrid Search Strategy

```python
def hybrid_search(query, top_k=10):
    # 1. Dense retrieval (semantic)
    dense_results = vector_search(
        query_embedding=embed(query),
        top_k=top_k * 2  # ดึงมาเยอะหน่อย
    )
    
    # 2. Sparse retrieval (BM25)
    sparse_results = bm25_search(
        query_tokens=tokenize(query),
        top_k=top_k * 2
    )
    
    # 3. Reciprocal Rank Fusion
    combined_results = rrf_fusion(
        dense_results,
        sparse_results,
        k=60  # RRF constant
    )
    
    # 4. Reranking
    reranked = cross_encoder_rerank(
        query=query,
        candidates=combined_results[:top_k * 3],
        top_k=top_k
    )
    
    return reranked
```

---

## 📈 5. Performance Optimization

### 5.1 Embedding Cache

```python
EMBEDDING_CACHE = {
    "enabled": True,
    "ttl_seconds": 86400 * 7,  # 7 days
    "max_size_mb": 500,
    "strategy": "LRU"  # Least Recently Used
}
```

### 5.2 Chunk Size vs Performance

```
Chunk Size Analysis:

200 tokens:  ⚡ Fast retrieval, ❌ Loss context
500 tokens:  ⚡ Good balance, ✅ Better context
1000 tokens: 🐌 Slower, ✅ Full context
1500 tokens: 🐌 Much slower, ⚠️ Too much noise

Recommendation: 500-800 tokens (sweet spot)
```

### 5.3 Query Optimization

```python
QUERY_OPTIMIZATION = {
    # Query expansion
    "expand_synonyms": True,
    "add_related_terms": True,
    
    # Query rewriting
    "colloquial_to_formal": True,  # "ซื้อบ้าน" → "จดทะเบียนโอน"
    
    # Multi-query
    "generate_variants": 3,  # สร้าง query หลายแบบ
    
    # Filtering
    "pre_filter": True,  # กรองก่อน search
    "post_filter": False
}
```

---

## 🎨 6. Metadata Extraction Strategy

### 6.1 Automated Extraction

```python
def extract_metadata(document_text):
    metadata = {}
    
    # 1. Extract title
    metadata['title'] = extract_title(document_text)
    
    # 2. Extract processing time
    time_pattern = r'(\d+)\s*นาที'
    metadata['processing_time'] = find_all(time_pattern)
    
    # 3. Extract fees
    fee_patterns = [
        r'(\d+)\s*บาท',
        r'(\d+(?:\.\d+)?)\s*%',
        r'ร้อยละ\s*(\d+)'
    ]
    metadata['fees'] = extract_fees(fee_patterns)
    
    # 4. Extract legal references
    law_pattern = r'(พ\.ร\.บ\.|ป\.พ\.พ\.|มาตรา\s*\d+)'
    metadata['legal_refs'] = find_all(law_pattern)
    
    # 5. Extract document types
    metadata['required_docs'] = extract_document_list(document_text)
    
    # 6. Classify category
    metadata['category'] = classify_category(document_text)
    
    return metadata
```

### 6.2 Entity Recognition (NER)

```python
ENTITIES_TO_EXTRACT = {
    "ORGANIZATION": ["กรมที่ดิน", "สำนักงานที่ดิน", "กระทรวงมหาดไทย"],
    "LAW": ["พ.ร.บ.", "กฎกระทรวง", "ระเบียบ", "มาตรา"],
    "DOCUMENT": ["โฉนด", "บัตรประชาชน", "หนังสือมอบอำนาจ"],
    "MONEY": ["บาท", "ร้อยละ", "%"],
    "TIME": ["นาที", "วัน", "ชั่วโมง"],
    "LOCATION": ["กรุงเทพมหานคร", "จังหวัด", "สาขา"]
}
```

---

## 💡 7. Best Practices Summary

### ✅ DO's

1. **รักษาความสมบูรณ์ของตาราง** - อย่าตัดตารางครึ่งๆ กลางๆ
2. **ใช้ overlap** - 15-20% เพื่อความต่อเนื่อง
3. **เก็บ metadata ครบถ้วน** - ยิ่งมากยิ่งดี
4. **ทำ hybrid search** - Dense + Sparse = ดีที่สุด
5. **มี reranking** - ช่วยเพิ่มความแม่นยำ
6. **Cache embeddings** - ประหยัดเวลาและเงิน
7. **Version control** - เก็บเวอร์ชันเอกสาร
8. **Link related chunks** - เชื่อมโยงข้อมูลที่เกี่ยวข้อง

### ❌ DON'Ts

1. **อย่าทำ chunk เล็กเกินไป** - สูญเสีย context
2. **อย่าทำ chunk ใหญ่เกินไป** - มี noise มาก
3. **อย่าตัดกฎหมายครึ่งๆ** - ต้องเก็บบริบทให้ครบ
4. **อย่าลืม normalize text** - ช่องว่าง, encoding
5. **อย่าพึ่ง vector อย่างเดียว** - ต้องมี keyword search ด้วย
6. **อย่าเก็บเอกสารเก่า** - ต้องมีการ update
7. **อย่าลืม handle special characters** - ไทย, ตัวเลข, สัญลักษณ์

---

## 🚀 8. Implementation Roadmap

### Phase 1: Basic Setup (Week 1-2)
- [ ] Setup Vector DB (Qdrant/Pinecone/Weaviate)
- [ ] Implement basic chunking
- [ ] Create document schema
- [ ] Build ingestion pipeline

### Phase 2: Enhanced Features (Week 3-4)
- [ ] Add metadata extraction
- [ ] Implement hybrid search
- [ ] Add reranking
- [ ] Build query optimization

### Phase 3: Optimization (Week 5-6)
- [ ] Performance tuning
- [ ] Add caching
- [ ] Optimize chunk sizes
- [ ] A/B testing

### Phase 4: Production (Week 7-8)
- [ ] Monitoring & logging
- [ ] Error handling
- [ ] Documentation
- [ ] Deployment

---

## 📚 9. Technology Stack Recommendations

```yaml
Vector Database:
  Primary: Qdrant (Open source, Python-friendly, good for Thai)
  Alternative: Weaviate, Pinecone
  
Embedding Models:
  Thai-specific: WangchanBERTa, PhayaThaiBERT
  Multilingual: OpenAI text-embedding-3-large, Cohere embed-multilingual-v3
  
Chunking:
  Library: LangChain, LlamaIndex
  Custom: tiktoken + pythainlp
  
Tokenizer:
  Thai: pythainlp (newmm, attacut)
  Multilingual: sentencepiece
  
Search:
  Dense: FAISS, HNSW
  Sparse: BM25 (rank_bm25)
  Hybrid: Reciprocal Rank Fusion (RRF)
  
Reranking:
  Model: cross-encoder/ms-marco-MiniLM-L-12-v2
  Thai: Fine-tuned Thai reranker
```

---

## 📊 10. Evaluation Metrics

```python
EVALUATION_METRICS = {
    "retrieval": {
        "precision@k": [1, 3, 5, 10],
        "recall@k": [1, 3, 5, 10],
        "mrr": True,  # Mean Reciprocal Rank
        "ndcg": True  # Normalized Discounted Cumulative Gain
    },
    
    "latency": {
        "p50": "< 100ms",
        "p95": "< 300ms",
        "p99": "< 500ms"
    },
    
    "relevance": {
        "manual_eval": True,
        "sample_size": 100,
        "annotators": 2
    }
}
```

---

## 🎯 Conclusion

Schema และ Chunking Strategy นี้ออกแบบมาเพื่อ:
- ✅ รักษาความสมบูรณ์ของข้อมูล
- ✅ เพิ่มประสิทธิภาพการค้นหา
- ✅ รองรับข้อมูลภาษาไทย
- ✅ Scale ได้ในอนาคต
- ✅ Easy to maintain

**Next Steps:**
1. Review และปรับแต่ง schema ตามความต้องการ
2. ทดสอบ chunking กับข้อมูลจริง
3. Evaluate retrieval performance
4. Iterate และปรับปรุง
