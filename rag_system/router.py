"""
Query Router for Land Department RAG System
Classifies user queries into 3 categories: RAG, OUT_OF_SCOPE, ABOUT_BOT
"""
from typing import List, Any


async def route_query(query: str, chat_history: List[Any], llm: Any) -> str:
    """
    Routes user query to appropriate handler
    
    Args:
        query: User's question
        chat_history: List of chat messages (with .role.value and .content attributes)
        llm: LLM instance for classification
    
    Returns:
        - 'RAG': Query about land department services
        - 'OUT_OF_SCOPE': Query outside land department domain
        - 'ABOUT_BOT': Query about the chatbot itself
    """
    conversation_history = '\n'.join([
        f'{m.role}: {m.content}' if hasattr(m, 'role') and hasattr(m, 'content')
        else f'user: {m}' if isinstance(m, str)
        else str(m)
        for m in chat_history[-4:]
    ]) if chat_history else 'ไม่มี'

    routing_prompt = f"""คุณคือ AI Query Classifier สำหรับแชทบอท "น้องไอดิน" ของกรมที่ดิน
หน้าที่: วิเคราะห์คำถามของผู้ใช้และจัดประเภทไปยังเส้นทางที่ถูกต้อง

---
# ข้อมูลที่น้องไอดินมี
น้องไอดินสามารถตอบคำถามเกี่ยวกับงานของกรมที่ดิน ได้แก่:
- การจดทะเบียนที่ดิน (โอน, จำนอง, เช่า)
- ค่าธรรมเนียมต่างๆ (โอน, จำนอง, เช่า)
- เอกสารและขั้นตอนการทำธุรกรรม
- สิทธิในที่ดิน
- โฉนดที่ดิน, น.ส.3, ส.ค.1
- การโอนมรดก
- คนต่างด้าวกับการถือครองที่ดิน
- กฎหมายและระเบียบที่เกี่ยวข้องกับที่ดิน

---
# หลักการวิเคราะห์
1. **เจตนาหลัก**: ผู้ใช้ต้องการรู้อะไร?
2. **ขอบเขต**: คำถามเกี่ยวข้องกับงานกรมที่ดินหรือไม่?
3. **ประวัติ**: มีบริบทจากการสนทนาก่อนหน้าหรือไม่?

---
# ตัวอย่างการตัดสินใจ

**คำถาม:** "ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่"
**วิเคราะห์:** เกี่ยวกับค่าธรรมเนียมโอนที่ดิน (งานของกรมที่ดิน)
**ตัดสินใจ:** `RAG`

**คำถาม:** "ขั้นตอนจดทะเบียนจำนองที่ดินยังไง"
**วิเคราะห์:** เกี่ยวกับขั้นตอนจดทะเบียน (งานของกรมที่ดิน)
**ตัดสินใจ:** `RAG`

**คำถาม:** "คนต่างชาติซื้อที่ดินได้ไหม"
**วิเคราะห์:** เกี่ยวกับสิทธิของคนต่างชาติในการถือครองที่ดิน (งานของกรมที่ดิน)
**ตัดสินใจ:** `RAG`

**คำถาม:** "โฉนดกับ น.ส.3 ต่างกันอย่างไร"
**วิเคราะห์:** เกี่ยวกับประเภทของเอกสารสิทธิที่ดิน (งานของกรมที่ดิน)
**ตัดสินใจ:** `RAG`

**คำถาม:** "สอนทำอาหารหน่อย"
**วิเคราะห์:** ไม่เกี่ยวข้องกับงานของกรมที่ดินเลย
**ตัดสินใจ:** `OUT_OF_SCOPE`

**คำถาม:** "อากาศวันนี้เป็นยังไง"
**วิเคราะห์:** คำถามทั่วไป ไม่เกี่ยวกับที่ดิน
**ตัดสินใจ:** `OUT_OF_SCOPE`

**คำถาม:** "เธอทำอะไรได้บ้าง"
**วิเคราะห์:** ถามเกี่ยวกับความสามารถของบอท
**ตัดสินใจ:** `ABOUT_BOT`

**คำถาม:** "สวัสดีครับ"
**วิเคราะห์:** คำทักทาย ถามเกี่ยวกับบอท
**ตัดสินใจ:** `ABOUT_BOT`

**คำถาม:** "เธอชื่ออะไร"
**วิเคราะห์:** ถามเกี่ยวกับตัวตนของบอท
**ตัดสินใจ:** `ABOUT_BOT`

---
# คำสั่ง
วิเคราะห์คำถามด้านล่างและตอบด้วยเส้นทางเดียวเท่านั้น:
- `RAG` - คำถามเกี่ยวกับงานของกรมที่ดิน
- `OUT_OF_SCOPE` - คำถามนอกเหนือขอบเขตงานของกรมที่ดิน
- `ABOUT_BOT` - คำถามเกี่ยวกับตัวบอทเอง

**ประวัติการสนทนา:**
{conversation_history}

**คำถามปัจจุบัน:** "{query}"

**ตอบเฉพาะชื่อเส้นทาง:**"""

    response = await llm.acomplete(routing_prompt)
    raw_text = response.text.strip()
    
    # Clean response
    cleaned_text = raw_text.replace("`", "").replace("json", "").strip().upper()
    
    # Validate
    valid_routes = ['RAG', 'OUT_OF_SCOPE', 'ABOUT_BOT']
    if cleaned_text not in valid_routes:
        print(f"⚠️ Router returned unexpected value: '{cleaned_text}'. Defaulting to 'OUT_OF_SCOPE'.")
        return 'OUT_OF_SCOPE'
    
    print(f"✅ Routing decision: '{cleaned_text}' for query: '{query}'")
    return cleaned_text
