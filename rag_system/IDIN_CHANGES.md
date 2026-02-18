# น้องไอดิน - Land Department RAG System Changes

## 📝 สรุปการเปลี่ยนแปลง

### ✅ ไฟล์ที่สร้างใหม่

#### 1. `rag_system/router.py`
**วัตถุประสงค์:** จัดการ routing queries
- ลดจาก 6 ประเภท → 3 ประเภท (`RAG`, `OUT_OF_SCOPE`, `ABOUT_BOT`)
- Prompt ปรับให้เหมาะกับงานกรมที่ดิน
- ตัวอย่างคำถามใหม่ทั้งหมด:
  * โอนที่ดิน, จำนองที่ดิน, ค่าธรรมเนียม → `RAG`
  * คนต่างชาติ ซื้อที่ดิน → `RAG`
  * สอนทำอาหาร, อากาศวันนี้ → `OUT_OF_SCOPE`
  * สวัสดี, เธอชื่ออะไร → `ABOUT_BOT`

#### 2. `rag_system/prompts.py`
**วัตถุประสงค์:** เก็บ system prompts ทั้งหมด
- `ROLE_INFO`: System prompt สำหรับ RAG (เปลี่ยนเป็น "น้องไอดิน")
- `OUT_OF_SCOPE_RESPONSE`: ข้อความสำหรับคำถามนอกขอบเขต (ปรับเป็นหัวข้อกรมที่ดิน)
- `ABOUT_BOT_RESPONSE`: แนะนำตัว "น้องไอดิน" (เปลี่ยนจากกรมการปกครอง → กรมที่ดิน)
- `CONDENSE_QUESTION_TEMPLATE`: Template สำหรับ condense คำถาม follow-up

### ✅ ไฟล์ที่แก้ไข

#### 1. `rag_system/api_server.py`
**การเปลี่ยนแปลง:**
- Import `router` และ `prompts` modules ใหม่
- Title: "น้องไอดิน" แทน generic name
- Startup message: "น้องไอดิน พร้อมให้บริการ"
- `/chat` endpoint:
  * เพิ่ม routing logic (เรียก `route_query`)
  * แยก handling ตาม decision: `RAG`, `OUT_OF_SCOPE`, `ABOUT_BOT`
  * บันทึก conversation history สำหรับทุก decision
  * ใช้ prompts จาก `prompts.py`

**Flow ใหม่:**
```
Request → Router → Decision
              ↓
    ┌─────────┴─────────┐
    ↓         ↓         ↓
  RAG   OUT_OF_SCOPE  ABOUT_BOT
    ↓         ↓         ↓
 Query    Fixed Msg   Fixed Msg
    ↓         ↓         ↓
Save to Memory (ทุกทาง)
    ↓
 Response
```

### 📊 เปรียบเทียบก่อน-หลัง

| ด้าน | ก่อน | หลัง |
|------|------|------|
| **ชื่อบอท** | ไม่ระบุ | น้องไอดิน |
| **Routing Types** | ไม่มี | 3 types (RAG, OUT_OF_SCOPE, ABOUT_BOT) |
| **Organization** | DOPA (กรมการปกครอง) | กรมที่ดิน |
| **หัวข้อที่ตอบ** | อาวุธปืน, มูลนิธิ, โรงแรม | โอนที่ดิน, จำนอง, ค่าธรรมเนียม |
| **Architecture** | Monolithic | Modular (router + prompts แยกไฟล์) |

### 🎯 ความสามารถใหม่

1. **Intelligent Routing:**
   - ตรวจจับคำถามเกี่ยวกับที่ดินโดยอัตโนมัติ
   - ปฏิเสธคำถามนอกขอบเขตอย่างสุภาพ
   - แนะนำตัวเองเมื่อถูกถาม

2. **Better UX:**
   - คำทักทาย (สวัสดี) → แนะนำตัว
   - คำถามนอกเรื่อง → บอกขอบเขตงาน + ยกตัวอย่างหัวข้อที่ตอบได้
   - คำถามเกี่ยวกับที่ดิน → ตอบจากฐานความรู้

3. **Maintainability:**
   - Prompts แยกไฟล์ (ง่ายต่อการแก้ไข)
   - Router แยกไฟล์ (ทดสอบ logic ได้อิสระ)
   - Clean separation of concerns

### 🚀 การใช้งาน

#### ทดสอบ Routing:
```bash
# ถามเกี่ยวกับที่ดิน → RAG
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "query": "ค่าธรรมเนียมโอนที่ดิน"}'

# ถามนอกเรื่อง → OUT_OF_SCOPE
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "query": "สอนทำอาหาร"}'

# ทักทาย → ABOUT_BOT
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "query": "สวัสดีครับ"}'
```

### ⚠️ หมายเหตุ

1. **LLM Requirement:** Router ต้องการ LLM เพื่อจัดประเภทคำถาม
2. **Memory:** ทุก decision จะบันทึกใน conversation memory
3. **ROLE_INFO:** ถ้าต้องการใช้ใน `rag_engine.py` ให้ import จาก `prompts.py`

### 📝 Todo (ถ้าต้องการ)

- [ ] เพิ่ม streaming support สำหรับ RAG responses
- [ ] เพิ่ม analytics tracking ตาม routing decision
- [ ] เพิ่ม confidence score จาก router
- [ ] สร้าง unit tests สำหรับ router logic
- [ ] เพิ่ม rate limiting per session
