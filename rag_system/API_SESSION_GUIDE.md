# 🔐 API Session Management Guide

## Overview

RAG API ตอนนี้รองรับ **Session Management** สำหรับการสนทนาแบบ multi-turn ที่แยก session ได้ หลายๆ user สามารถใช้ API พร้อมกันโดยแต่ละคนมี session ของตัวเอง

## ✨ Features

### 1. Session-based Conversations
- แต่ละ session มี conversation memory ของตัวเอง
- Session แยกกันอย่างสมบูรณ์ (isolated)
- สนับสนุน concurrent sessions (หลาย users พร้อมกัน)

### 2. Memory per Session
- แต่ละ session เก็บได้ถึง 50 messages
- Auto-save conversation history
- Context-aware responses

### 3. Session Management
- Create new session
- Get session info & statistics
- View conversation history
- Delete session

## 🚀 Quick Start

### 1. Start API Server

```bash
python rag_system/api_server.py
```

Server จะรันที่: `http://localhost:8000`

Docs (Swagger UI): `http://localhost:8000/docs`

### 2. Create Session

```bash
curl -X POST "http://localhost:8000/session/new"
```

Response:
```json
{
  "session_id": "abc123-def456-789ghi",
  "created_at": "2026-02-17T10:30:00",
  "message": "Session created successfully"
}
```

### 3. Query with Session

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่",
    "session_id": "abc123-def456-789ghi",
    "top_k": 3,
    "include_conversation_history": true
  }'
```

### 4. Follow-up Query (with Memory)

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "แล้วถ้าจำนองล่ะ",
    "session_id": "abc123-def456-789ghi",
    "include_conversation_history": true
  }'
```

Memory จะจำบริบทว่ากำลังพูดเรื่องที่ดิน!

## 📡 API Endpoints

### Session Management

#### POST `/session/new`
สร้าง session ใหม่

**Response:**
```json
{
  "session_id": "uuid-string",
  "created_at": "2026-02-17T10:30:00",
  "message": "Session created successfully"
}
```

#### GET `/session/{session_id}`
ดูข้อมูล session

**Response:**
```json
{
  "session_id": "uuid-string",
  "created_at": "2026-02-17T10:30:00",
  "last_activity": "2026-02-17T10:35:00",
  "total_messages": 4,
  "user_messages": 2,
  "assistant_messages": 2,
  "total_turns": 2
}
```

#### GET `/session/{session_id}/history`
ดูประวัติการสนทนา

**Query Parameters:**
- `max_messages` (optional): จำนวน messages สูงสุด

**Response:**
```json
{
  "session_id": "uuid-string",
  "total_messages": 4,
  "messages": [
    {
      "role": "user",
      "content": "ค่าธรรมเนียมโอนที่ดิน",
      "timestamp": "2026-02-17T10:30:00",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "[คำตอบ...]",
      "timestamp": "2026-02-17T10:30:05",
      "metadata": {"sources_count": 2}
    }
  ]
}
```

#### DELETE `/session/{session_id}`
ลบ session

**Response:**
```json
{
  "message": "Session deleted successfully",
  "session_id": "uuid-string"
}
```

#### GET `/sessions`
ดู sessions ทั้งหมด

**Response:**
```json
{
  "total_sessions": 3,
  "sessions": [
    {
      "session_id": "uuid-1",
      "created_at": "2026-02-17T10:00:00",
      "last_activity": "2026-02-17T10:35:00",
      "message_count": 6
    }
  ]
}
```

### Query Endpoint

#### POST `/query`
Query RAG system (with optional session)

**Request Body:**
```json
{
  "query": "คำถาม",
  "session_id": "uuid-string",  // Optional: null = single query mode
  "top_k": 3,
  "enable_reranker": true,
  "enable_context_expansion": true,
  "alpha": 0.5,
  "use_llm": false,
  "include_conversation_history": true,
  "max_history_turns": 3
}
```

**Response:**
```json
{
  "answer": "คำตอบ...",
  "query": "คำถาม",
  "session_id": "uuid-string",  // null if no session
  "sources": [...],
  "retrieved_chunks": [...],
  "metadata": {
    "num_chunks": 3,
    "memory_enabled": true,
    "history_included": true,
    ...
  }
}
```

## 💡 Usage Examples

### Python Example

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Create session
response = requests.post(f"{BASE_URL}/session/new")
session_id = response.json()['session_id']
print(f"Session ID: {session_id}")

# 2. First query
query1 = {
    "query": "ค่าธรรมเนียมโอนที่ดิน",
    "session_id": session_id,
    "include_conversation_history": True,
}
response = requests.post(f"{BASE_URL}/query", json=query1)
result1 = response.json()
print(f"Answer 1: {result1['answer'][:100]}...")

# 3. Follow-up query (memory remembers context)
query2 = {
    "query": "แล้วถ้าจำนองล่ะ",
    "session_id": session_id,
    "include_conversation_history": True,
}
response = requests.post(f"{BASE_URL}/query", json=query2)
result2 = response.json()
print(f"Answer 2: {result2['answer'][:100]}...")

# 4. Get session history
response = requests.get(f"{BASE_URL}/session/{session_id}/history")
history = response.json()
print(f"Total messages: {history['total_messages']}")

# 5. Delete session when done
requests.delete(f"{BASE_URL}/session/{session_id}")
```

### JavaScript Example

```javascript
const BASE_URL = "http://localhost:8000";

async function chatWithRAG() {
  // 1. Create session
  const sessionResp = await fetch(`${BASE_URL}/session/new`, {
    method: 'POST'
  });
  const { session_id } = await sessionResp.json();
  console.log("Session ID:", session_id);
  
  // 2. First query
  const query1Resp = await fetch(`${BASE_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: "ค่าธรรมเนียมโอนที่ดิน",
      session_id: session_id,
      include_conversation_history: true,
    })
  });
  const result1 = await query1Resp.json();
  console.log("Answer 1:", result1.answer.substring(0, 100));
  
  // 3. Follow-up query
  const query2Resp = await fetch(`${BASE_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: "แล้วถ้าจำนองล่ะ",
      session_id: session_id,
      include_conversation_history: true,
    })
  });
  const result2 = await query2Resp.json();
  console.log("Answer 2:", result2.answer.substring(0, 100));
  
  // 4. Get history
  const historyResp = await fetch(`${BASE_URL}/session/${session_id}/history`);
  const history = await historyResp.json();
  console.log("Messages:", history.total_messages);
  
  // 5. Delete session
  await fetch(`${BASE_URL}/session/${session_id}`, {
    method: 'DELETE'
  });
}

chatWithRAG();
```

## 🎯 Use Cases

### 1. Web Chat Application

```javascript
// User starts conversation
const session = await createSession();

// User sends messages
await sendQuery("ค่าธรรมเนียมโอนที่ดิน", session.session_id);
await sendQuery("แล้วถ้าจำนองล่ะ", session.session_id);
await sendQuery("ขอสรุปให้หน่อย", session.session_id);

// Show history in UI
const history = await getHistory(session.session_id);
displayMessages(history.messages);
```

### 2. Mobile App

```swift
// Swift example
class ChatSession {
    var sessionId: String?
    
    func startChat() async {
        let response = await createSession()
        self.sessionId = response.sessionId
    }
    
    func sendMessage(_ text: String) async -> String {
        let result = await query(text, sessionId: sessionId)
        return result.answer
    }
}
```

### 3. Multi-user Support

```python
# Server can handle multiple users simultaneously
user1_session = create_session()  # User 1
user2_session = create_session()  # User 2

# Both can query independently
query(user1_session, "ค่าธรรมเนียมโอน")
query(user2_session, "เอกสารจดทะเบียน")

# Memories are separated
```

## 🔧 Configuration

### Session Settings

In `api_server.py`:

```python
# Max messages per session
memory = ConversationBufferMemory(max_messages=50)

# Adjust as needed
max_messages=100  # For longer conversations
```

### Query Settings

```json
{
  "top_k": 3,                          // 1-20
  "enable_reranker": true,             // Better quality
  "enable_context_expansion": true,    // More context
  "alpha": 0.5,                        // BM25 vs Dense (0-1)
  "use_llm": false,                    // LLM generation
  "include_conversation_history": true,// Use memory
  "max_history_turns": 3               // Context window (1-10)
}
```

## ⚠️ Important Notes

### 1. Session Storage
- **Current**: In-memory (sessions lost on restart)
- **Production**: Use Redis or database
- **Alternative**: Implement session persistence

### 2. Session Cleanup
- Sessions persist until explicitly deleted
- Consider implementing auto-cleanup for inactive sessions
- Monitor memory usage with many sessions

### 3. Concurrent Access
- API is thread-safe per session
- Each session has its own memory
- No conflicts between sessions

### 4. Single Query Mode
- Set `session_id: null` for stateless queries
- No memory, no history
- Faster for one-off questions

## 📊 Monitoring

### Check Active Sessions

```bash
curl http://localhost:8000/sessions
```

### Session Statistics

```bash
curl http://localhost:8000/session/{session_id}
```

### Health Check

```bash
curl http://localhost:8000/health
```

## 🔒 Security Considerations

### Production Recommendations

1. **Authentication**: Add API keys or JWT tokens
2. **Rate Limiting**: Prevent abuse
3. **Session Limits**: Max sessions per user
4. **Timeout**: Auto-delete inactive sessions
5. **HTTPS**: Use SSL in production

### Example with Authentication

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header()):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.post("/query", dependencies=[Depends(verify_api_key)])
async def query_rag(request: QueryRequest):
    ...
```

## 🚀 Deployment

### Docker Example

```dockerfile
FROM python:3.10

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "rag_system/api_server.py"]
```

### Environment Variables

```bash
export RAG_HOST=0.0.0.0
export RAG_PORT=8000
export RAG_MAX_SESSIONS=1000
export RAG_SESSION_MAX_MESSAGES=50
```

## 📚 Testing

Run test script:

```bash
# Make sure server is running
python rag_system/api_server.py

# In another terminal
python test_api_sessions.py
```

Test coverage:
- ✅ Session creation
- ✅ Multi-turn conversations
- ✅ Memory persistence
- ✅ Session info retrieval
- ✅ History viewing
- ✅ Session deletion
- ✅ Single query mode

## 🔮 Future Enhancements

### Phase 1 (Planned)
- Session persistence (Redis/Database)
- Auto-cleanup for inactive sessions
- Session authentication
- Rate limiting per session

### Phase 2 (Future)
- WebSocket support for real-time chat
- Session sharing/collaboration
- Session export/import
- Analytics dashboard

## 📖 API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🆘 Troubleshooting

### Session not found
**Error**: `404 Session {id} not found`
**Solution**: 
- Session was deleted or expired
- Create new session with POST `/session/new`

### Memory not working
**Problem**: Follow-up queries don't use context
**Solution**:
- Ensure `include_conversation_history: true`
- Check `session_id` is provided
- Verify session exists

### Server not starting
**Problem**: Import errors
**Solution**:
```bash
pip install fastapi uvicorn
```

---

**Version**: 1.1.0 (Session Support)  
**Last Updated**: 2026-02-17  
**API Server**: `rag_system/api_server.py`
