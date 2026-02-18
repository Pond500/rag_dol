# 🚀 Postman Testing Guide - RAG API with Sessions

## Quick Start

### 1. Start the API Server

```bash
cd /Users/pond500/RAG/rag_dol
.venv/bin/python rag_system/api_server.py
```

Server จะรันที่: `http://localhost:8000`

เมื่อเห็นข้อความนี้แสดงว่าพร้อมแล้ว:
```
🚀 Starting Land Department RAG API with Session Support...
✅ RAG system initialized
💬 Session management ready
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Test with Postman

## 📋 Postman Collection

### Request 1: Health Check (GET)

**Method:** GET  
**URL:** `http://localhost:8000/health`  
**Headers:** None

**Expected Response:**
```json
{
  "status": "healthy",
  "rag_initialized": true
}
```

---

### Request 2: Create New Session (POST)

**Method:** POST  
**URL:** `http://localhost:8000/session/new`  
**Headers:** 
- `Content-Type: application/json`

**Body:** None (empty)

**Expected Response:**
```json
{
  "session_id": "abc123-def456-789ghi",
  "created_at": "2026-02-17T10:30:00.123456",
  "message": "Session created successfully"
}
```

⚠️ **เก็บ `session_id` ไว้ใช้ใน requests ถัดไป!**

---

### Request 3: First Query (POST)

**Method:** POST  
**URL:** `http://localhost:8000/query`  
**Headers:** 
- `Content-Type: application/json`

**Body (JSON):**
```json
{
  "query": "ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่",
  "session_id": "YOUR_SESSION_ID_HERE",
  "top_k": 3,
  "enable_reranker": true,
  "enable_context_expansion": true,
  "include_conversation_history": true
}
```

**Expected Response:**
```json
{
  "answer": "ค่าธรรมเนียมการจดทะเบียนโอนที่ดิน...",
  "query": "ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่",
  "session_id": "YOUR_SESSION_ID",
  "sources": [
    {
      "filename": "1.จดทะเบียนประเภทโอนอสังหาริมทรัพย์กรณีไม่ต้องประกาศ.txt",
      "section": "ค่าธรรมเนียม",
      "type": "section",
      "score": "0.8736"
    }
  ],
  "retrieved_chunks": [...],
  "metadata": {
    "num_chunks": 3,
    "memory_enabled": true,
    "history_included": true,
    ...
  }
}
```

---

### Request 4: Follow-up Query (POST)

**Method:** POST  
**URL:** `http://localhost:8000/query`  
**Headers:** 
- `Content-Type: application/json`

**Body (JSON):**
```json
{
  "query": "แล้วถ้าจำนองล่ะ",
  "session_id": "YOUR_SESSION_ID_HERE",
  "top_k": 3,
  "enable_reranker": true,
  "include_conversation_history": true
}
```

💡 **Memory จะจำว่ากำลังพูดถึงที่ดิน!**

---

### Request 5: Get Session Info (GET)

**Method:** GET  
**URL:** `http://localhost:8000/session/YOUR_SESSION_ID_HERE`  
**Headers:** None

**Expected Response:**
```json
{
  "session_id": "YOUR_SESSION_ID",
  "created_at": "2026-02-17T10:30:00",
  "last_activity": "2026-02-17T10:35:00",
  "total_messages": 4,
  "user_messages": 2,
  "assistant_messages": 2,
  "total_turns": 2
}
```

---

### Request 6: Get Session History (GET)

**Method:** GET  
**URL:** `http://localhost:8000/session/YOUR_SESSION_ID_HERE/history`  
**Headers:** None

**Optional Query Parameters:**
- `max_messages=10` (limit number of messages)

**Expected Response:**
```json
{
  "session_id": "YOUR_SESSION_ID",
  "total_messages": 4,
  "messages": [
    {
      "role": "user",
      "content": "ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่",
      "timestamp": "2026-02-17T10:30:00",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "[คำตอบ...]",
      "timestamp": "2026-02-17T10:30:05",
      "metadata": {"sources_count": 2}
    },
    ...
  ]
}
```

---

### Request 7: List All Sessions (GET)

**Method:** GET  
**URL:** `http://localhost:8000/sessions`  
**Headers:** None

**Expected Response:**
```json
{
  "total_sessions": 2,
  "sessions": [
    {
      "session_id": "abc-123",
      "created_at": "2026-02-17T10:00:00",
      "last_activity": "2026-02-17T10:35:00",
      "message_count": 4
    },
    {
      "session_id": "def-456",
      "created_at": "2026-02-17T10:10:00",
      "last_activity": "2026-02-17T10:20:00",
      "message_count": 2
    }
  ]
}
```

---

### Request 8: Query WITHOUT Session (POST)

**Method:** POST  
**URL:** `http://localhost:8000/query`  
**Headers:** 
- `Content-Type: application/json`

**Body (JSON):**
```json
{
  "query": "ค่าธรรมเนียมโอน",
  "top_k": 3,
  "enable_reranker": true
}
```

💡 **ไม่มี `session_id` = single query mode (ไม่มี memory)**

---

### Request 9: Delete Session (DELETE)

**Method:** DELETE  
**URL:** `http://localhost:8000/session/YOUR_SESSION_ID_HERE`  
**Headers:** None

**Expected Response:**
```json
{
  "message": "Session deleted successfully",
  "session_id": "YOUR_SESSION_ID"
}
```

---

### Request 10: Get Configuration (GET)

**Method:** GET  
**URL:** `http://localhost:8000/config`  
**Headers:** None

**Expected Response:**
```json
{
  "retrieval": {
    "default_top_k": 3,
    "max_top_k": 20,
    "default_alpha": 0.5,
    "reranker_available": true,
    "context_expansion_available": true
  },
  "models": {
    "embedding": "BAAI/bge-m3",
    "reranker": "BAAI/bge-reranker-v2-m3",
    "bm25_vocabulary_size": 8827
  },
  "database": {
    "total_documents": 108,
    "total_chunks": 3704
  },
  "session": {
    "max_messages_per_session": 50,
    "active_sessions": 2
  }
}
```

---

## 📥 Import to Postman

### Option 1: Manual Import (Recommended)

1. เปิด Postman
2. Click "New" → "Collection"
3. ตั้งชื่อ: "RAG API - Land Department"
4. Add requests ตามด้านบน (10 requests)
5. แก้ `YOUR_SESSION_ID_HERE` หลังจากสร้าง session

### Option 2: Use Postman Collection File

สร้างไฟล์ `RAG_API.postman_collection.json`:

```json
{
  "info": {
    "name": "RAG API - Land Department",
    "description": "API for querying Land Department documents with session management",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "1. Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/health",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["health"]
        }
      }
    },
    {
      "name": "2. Create Session",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "url": {
          "raw": "http://localhost:8000/session/new",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["session", "new"]
        }
      }
    },
    {
      "name": "3. Query (First)",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"query\": \"ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่\",\n  \"session_id\": \"{{session_id}}\",\n  \"top_k\": 3,\n  \"enable_reranker\": true,\n  \"include_conversation_history\": true\n}"
        },
        "url": {
          "raw": "http://localhost:8000/query",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["query"]
        }
      }
    },
    {
      "name": "4. Query (Follow-up)",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"query\": \"แล้วถ้าจำนองล่ะ\",\n  \"session_id\": \"{{session_id}}\",\n  \"top_k\": 3,\n  \"enable_reranker\": true,\n  \"include_conversation_history\": true\n}"
        },
        "url": {
          "raw": "http://localhost:8000/query",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["query"]
        }
      }
    },
    {
      "name": "5. Get Session Info",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/session/{{session_id}}",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["session", "{{session_id}}"]
        }
      }
    },
    {
      "name": "6. Get Session History",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/session/{{session_id}}/history",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["session", "{{session_id}}", "history"]
        }
      }
    },
    {
      "name": "7. List Sessions",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/sessions",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["sessions"]
        }
      }
    },
    {
      "name": "8. Delete Session",
      "request": {
        "method": "DELETE",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/session/{{session_id}}",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["session", "{{session_id}}"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "session_id",
      "value": ""
    }
  ]
}
```

Import ใน Postman:
1. File → Import → เลือกไฟล์นี้
2. Collection จะถูกสร้างพร้อม 8 requests

---

## 🎯 Testing Workflow

### Step-by-Step Testing

1. **Start Server**
   ```bash
   .venv/bin/python rag_system/api_server.py
   ```

2. **Health Check** (Request 1)
   - ตรวจสอบว่า server รันอยู่

3. **Create Session** (Request 2)
   - Copy `session_id` จาก response
   - วางใน requests ถัดไป

4. **First Query** (Request 3)
   - ถามคำถามแรก
   - ดู `sources` และ `answer`

5. **Follow-up Query** (Request 4)
   - ถามคำถามต่อเนื่อง
   - สังเกต `history_included: true`

6. **Check History** (Request 6)
   - ดูว่า memory เก็บข้อมูลถูกต้องไหม
   - ควรเห็น 4 messages (2 user + 2 assistant)

7. **Get Session Info** (Request 5)
   - ดูสถิติ session

8. **Delete Session** (Request 9)
   - ลบ session เมื่อเสร็จ

---

## 💡 Tips & Tricks

### Use Environment Variables in Postman

1. คลิกที่ Collection → Variables
2. เพิ่ม variable:
   - `base_url`: `http://localhost:8000`
   - `session_id`: (empty, จะเซ็ตทีหลัง)

3. ใช้ใน URL:
   ```
   {{base_url}}/query
   {{base_url}}/session/{{session_id}}
   ```

### Auto-set session_id with Tests

ใน Request "Create Session", เพิ่ม Test script:

```javascript
// Tests tab
var jsonData = pm.response.json();
pm.environment.set("session_id", jsonData.session_id);
pm.test("Session created", function () {
    pm.response.to.have.status(200);
});
```

ตอนนี้ `{{session_id}}` จะถูกเซ็ตอัตโนมัติ!

### Save Common Queries

สร้าง Examples ใน request:

```json
// Example 1: Transfer fee
{
  "query": "ค่าธรรมเนียมโอนที่ดิน",
  "session_id": "{{session_id}}"
}

// Example 2: Mortgage fee
{
  "query": "ค่าธรรมเนียมจำนอง",
  "session_id": "{{session_id}}"
}

// Example 3: Required documents
{
  "query": "เอกสารที่ต้องใช้จดทะเบียน",
  "session_id": "{{session_id}}"
}
```

---

## 🔍 Common Issues

### Error: Connection Refused

**Problem:**
```json
{
  "error": "connect ECONNREFUSED 127.0.0.1:8000"
}
```

**Solution:**
- ตรวจสอบว่า server รันอยู่หรือไม่
- ลอง `http://localhost:8000/health` ใน browser

### Error: Session not found

**Problem:**
```json
{
  "detail": "Session abc-123 not found"
}
```

**Solution:**
- สร้าง session ใหม่ด้วย POST `/session/new`
- ตรวจสอบว่าคัดลอก `session_id` ถูกต้อง

### Error: 503 Service Unavailable

**Problem:**
```json
{
  "detail": "RAG system not initialized"
}
```

**Solution:**
- รอให้ server โหลดเสร็จ (ประมาณ 10-15 วินาที)
- ดู logs ว่าโหลด models เสร็จแล้วหรือยัง

---

## 📊 Sample Conversation

### Complete Multi-turn Example

```
1. POST /session/new
   → session_id: "abc-123"

2. POST /query
   Body: {
     "query": "ค่าธรรมเนียมโอนที่ดิน",
     "session_id": "abc-123"
   }
   → Answer: [ข้อมูลค่าธรรมเนียมโอนที่ดิน]

3. POST /query
   Body: {
     "query": "แล้วถ้าจำนองล่ะ",
     "session_id": "abc-123"
   }
   → Answer: [ข้อมูลค่าธรรมเนียมจำนอง - รู้ว่าพูดถึงที่ดิน!]

4. POST /query
   Body: {
     "query": "ขอสรุปค่าใช้จ่ายทั้งสองอย่างให้หน่อย",
     "session_id": "abc-123"
   }
   → Answer: [สรุปค่าโอนและจำนอง]

5. GET /session/abc-123/history
   → 6 messages (3 user + 3 assistant)

6. DELETE /session/abc-123
   → Session deleted
```

---

## 🚀 Advanced Testing

### Performance Testing

Use Postman Runner:

1. Create Collection Runner
2. Set iterations: 10
3. Add delay: 1000ms
4. Monitor response times

### Load Testing

Use Newman (Postman CLI):

```bash
npm install -g newman

newman run RAG_API.postman_collection.json \
  -n 100 \
  --delay-request 500
```

---

## 📖 Additional Resources

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Session Guide**: `rag_system/API_SESSION_GUIDE.md`

---

**Happy Testing! 🎉**
