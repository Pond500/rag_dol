# 🧠 Conversation Memory Guide

## Overview

RAG System ตอนนี้รองรับ **ConversationBufferMemory** สำหรับการสนทนาแบบ multi-turn ที่สามารถจำบริบทจากการสนทนาก่อนหน้าได้

## ✨ Features

### 1. **ConversationBufferMemory**
- เก็บประวัติการสนทนาใน FIFO buffer (ตั้งค่า max_messages ได้)
- บันทึกทั้ง user messages และ assistant messages
- ติดตาม timestamp และ metadata ของแต่ละข้อความ
- รองรับการ clear และ export history

### 2. **Context Window Management**
- ดึง context จากการสนทนาล่าสุด (configurable turns)
- จำกัดความยาว context เพื่อไม่ให้ prompt เกินขนาด
- Automatic truncation ถ้า context ยาวเกินไป

### 3. **Memory Statistics**
- Conversation ID และ timestamp
- จำนวนข้อความทั้งหมด (user/assistant)
- Buffer utilization
- Duration ของการสนทนา

### 4. **Multi-turn Conversation Support**
- RAG Engine ส่ง conversation history ไปยัง LLM
- รองรับคำถามแบบ follow-up (เช่น "แล้วถ้าจำนองล่ะ")
- Context-aware retrieval

## 🚀 Quick Start

### 1. การเปิดใช้งาน Memory

```python
from rag_system.rag_engine import LandDepartmentRAG

# Initialize with memory enabled (default)
rag = LandDepartmentRAG(
    enable_memory=True,  # เปิดใช้งาน memory
    memory_max_messages=20,  # เก็บได้สูงสุด 20 messages
)
```

### 2. การ Query พร้อม Memory

```python
# Query ครั้งแรก
response1 = rag.query(
    query="ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่",
    include_conversation_history=True,  # รวม history ใน context
    max_history_turns=3,  # ใช้ 3 turns ล่าสุด
)

# Follow-up query (memory จะจำบริบทจาก query แรก)
response2 = rag.query(
    query="แล้วถ้าจำนองล่ะ",
    include_conversation_history=True,
)

# Memory จะเข้าใจว่า "จำนอง" หมายถึงจำนองที่ดิน
```

### 3. การดู Memory

```python
# จำนวนข้อความใน buffer
print(f"Total messages: {len(rag.memory)}")

# ประวัติการสนทนา
print(rag.memory.format_history())

# สถิติ
stats = rag.memory.get_statistics()
print(stats)
```

### 4. การล้าง Memory

```python
# ล้างประวัติทั้งหมด
rag.memory.clear()
```

## 💬 Chat Interface with Memory

### การใช้งาน CLI

```bash
python rag_system/chat_interface.py
```

### คำสั่งใหม่

- `/history` - แสดงประวัติการสนทนาจาก Memory
- `/stats` - แสดงสถิติของ Memory
- `/clear` - ล้าง Memory

### ตัวอย่างการใช้งาน

```
💬 คุณ: ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่
🤖 ระบบ: [ตอบคำถามพร้อมแสดงที่มา]

💬 คุณ: แล้วถ้าจำนองล่ะ
🤖 ระบบ: [ตอบโดยอ้างอิงจากบริบทก่อนหน้า - รู้ว่าพูดถึงที่ดิน]

💬 คุณ: /stats
📊 Memory Statistics:
  Total Messages: 4
  User Messages: 2
  Assistant Messages: 2
  ...
```

## 🔧 Advanced Configuration

### Memory Parameters

```python
rag = LandDepartmentRAG(
    enable_memory=True,
    memory_max_messages=20,  # FIFO buffer size
)
```

### Query Parameters

```python
response = rag.query(
    query="คำถาม",
    include_conversation_history=True,  # รวม history หรือไม่
    max_history_turns=3,  # จำนวน turns ที่จะรวม (1 turn = user + assistant)
    use_llm=True,  # ต้องเปิดเพื่อให้ LLM เข้าใจ context
)
```

### Context Window

```python
# ดึง context สำหรับ LLM
context = rag.memory.get_context_window(max_turns=3)

# Format:
# User: คำถาม1
# Assistant: คำตอบ1
# User: คำถาม2
# Assistant: คำตอบ2
# ...
```

## 📊 Memory Metadata

แต่ละ message สามารถเก็บ metadata:

```python
# User message
rag.memory.add_user_message(
    "คำถาม",
    metadata={'source': 'cli', 'language': 'th'}
)

# Assistant message
rag.memory.add_assistant_message(
    "คำตอบ",
    metadata={'sources_count': 3, 'retrieval_time': 0.5}
)
```

## 🎯 Use Cases

### 1. Follow-up Questions

```python
# Turn 1
"ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่"

# Turn 2 (memory จะรู้ว่าพูดถึงที่ดิน)
"แล้วถ้าจำนองล่ะ"

# Turn 3 (memory จะรู้ว่าพูดถึงค่าธรรมเนียมโอนและจำนอง)
"ขอสรุปค่าใช้จ่ายทั้งสองอย่างให้หน่อย"
```

### 2. Clarification

```python
# Turn 1
"จดทะเบียนโอนที่ดินต้องใช้เอกสารอะไรบ้าง"

# Turn 2
"ถ้าเป็นที่ดินมรดกล่ะ"  # Memory รู้ว่ายังพูดถึงการโอนที่ดิน
```

### 3. Context Refinement

```python
# Turn 1
"ค่าธรรมเนียมโอน"

# Turn 2 (ระบบอาจถามกลับ)
"โอนที่ดิน อสังหาริมทรัพย์ หรือห้องชุดครับ"

# Turn 3
"ที่ดินครับ"  # Memory รู้ว่ากำลังพูดเรื่องค่าธรรมเนียม
```

## ⚠️ Important Notes

### 1. Memory is Session-based
- Memory จะหายเมื่อปิดโปรแกรม
- แต่ละ session จะมี conversation_id ใหม่
- ถ้าต้องการ persistent memory ต้อง implement export/import

### 2. Buffer Size Limitation
- ตั้งค่า `max_messages` ให้เหมาะสม
- เกิน limit จะเป็น FIFO (ข้อความเก่าหายไป)
- แนะนำ: 20-50 messages สำหรับ casual chat

### 3. Context Length
- LLM มี context window limit
- Memory จะ truncate context ถ้ายาวเกิน `max_context_length`
- Default: 2000 chars

### 4. Empty Memory Issue
- **IMPORTANT**: ใช้ `if memory is not None:` แทน `if memory:`
- Empty memory object (len=0) จะ evaluate เป็น False
- ปัญหานี้แก้ไขแล้วใน codebase

## 🔮 Future Enhancements

### Phase 1 (Future)
- **Summary Memory**: สรุปการสนทนาเมื่อ buffer เต็ม
- **Entity Memory**: จำ entities ที่ถูกพูดถึง (เช่น ชื่อบุคคล, ที่อยู่)
- **Vector Memory**: ค้นหา semantic ในประวัติการสนทนา

### Phase 2 (Future)
- **Persistent Memory**: บันทึกลง database
- **Multi-session Memory**: จำ user preferences ข้าม sessions
- **Conversation Templates**: Template สำหรับ conversation types ต่างๆ

## 📖 Example Scripts

### Test Scripts
- `test_memory_rag.py` - ทดสอบ memory functionality พื้นฐาน
- `test_interactive_memory.py` - ทดสอบ multi-turn conversation
- `debug_memory.py` - Debug memory behavior

### Run Tests

```bash
# Basic memory test
python test_memory_rag.py

# Interactive conversation test
python test_interactive_memory.py

# Memory debugging
python debug_memory.py
```

## 🆘 Troubleshooting

### Memory ไม่บันทึกข้อความ

**Problem**: `len(rag.memory) == 0` หลัง query

**Solution**: 
- ตรวจสอบว่า `enable_memory=True`
- ใช้ `if memory is not None:` แทน `if memory:`
- ดูใน code ว่า `add_user_message()` ถูกเรียกหรือไม่

### Context Window ว่างเปล่า

**Problem**: `get_context_window()` return ""

**Solution**:
- ตรวจสอบว่ามี messages ใน buffer หรือไม่
- เพิ่ม `max_turns` parameter
- ตรวจสอบ `max_context_length`

### Memory เต็มเร็วเกินไป

**Problem**: Buffer เต็มหลังสนทนาไม่กี่ turn

**Solution**:
- เพิ่ม `memory_max_messages` ตอน init
- ใช้ summary memory (future feature)
- Clear memory เป็นระยะ

## 📚 API Reference

### ConversationBufferMemory

```python
memory = ConversationBufferMemory(
    max_messages=20,
    max_context_length=2000,
)

# Methods
memory.add_user_message(content, metadata=None)
memory.add_assistant_message(content, metadata=None)
memory.get_messages(last_n=None)
memory.get_context_window(max_turns=5)
memory.clear()
memory.get_statistics()
memory.format_history(max_messages=None)
```

### LandDepartmentRAG with Memory

```python
rag = LandDepartmentRAG(
    enable_memory=True,
    memory_max_messages=20,
)

response = rag.query(
    query="คำถาม",
    include_conversation_history=True,
    max_history_turns=3,
)
```

---

**Last Updated**: 2026-02-17  
**Version**: 1.0.0  
**Author**: RAG Development Team
