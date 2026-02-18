# Vector Database Schema & Chunking Strategy (v2 - Comprehensive)
## อิงจากเอกสารจริง 100% - ครอบคลุมทุกสไตล์ทุกรูปแบบ

วันที่: 12 กุมภาพันธ์ 2026  
**เวอร์ชัน:** 2.0 Comprehensive Edition  
**อิงจาก:** การวิเคราะห์เอกสารจริงจากกรมที่ดิน 108 ไฟล์

---

## 🎯 สิ่งที่พบจากเอกสารจริง

### 📋 ประเภทเอกสารที่พบ (3 ประเภทหลัก)

1. **คู่มือปชช** (~40 ไฟล์) - โครงสร้างมาตรฐาน มีตาราง HTML
2. **คู่มือเจ้าหน้าที่** (~55 ไฟล์) - รายละเอียดลึก มีตัวอย่างเคส
3. **ระเบียบกรม** (~15 ไฟล์) - รูปแบบกฎหมาย มีมาตรา/ข้อ

---

## 📊 1. COMPREHENSIVE Vector Database Schema

### 1.1 Collection: documents (ระดับเอกสาร)

```json
{
  "_id": "doc_001",
  "embedding": [0.123, 0.456, ...],  // 1536 dims
  
  "metadata": {
    // ========== BASIC INFO ==========
    "title": "จดทะเบียนประเภทโอนอสังหาริมทรัพย์ กรณีไม่ต้องประกาศ",
    "title_short": "โอนอสังหาริมทรัพย์ไม่ต้องประกาศ",  // สำหรับ display
    
    "document_type": "คู่มือปชช",  
    // Types: คู่มือปชช | คู่มือเจ้าหน้าที่ | ระเบียบกรม | กฎหมาย | คำสั่ง | ประกาศ
    
    "file_info": {
      "file_path": "data/คู่มือปชช.รายละเอียดเนื้อหา/1.จดทะเบียน...",
      "file_name": "1.จดทะเบียนประเภทโอนอสังหาริมทรัพย์กรณีไม่ต้องประกาศ (N).txt",
      "file_size_kb": 45.2,
      "line_count": 154,
      "word_count": 3250,
      "char_count": 15234
    },
    
    "version_info": {
      "version": "N",  // N=New หรือ ว่าง=เก่า
      "last_updated": "2022",  // จากข้อมูล "วันที่เผยแพร่คู่มือ"
      "is_latest": true,
      "supersedes": null,  // doc_id ของเวอร์ชันเก่า
      "law_year": "2497"  // ปี พ.ศ. ของกฎหมายที่อ้างอิง
    },
    
    // ========== ORGANIZATION INFO (จากเอกสารจริง) ==========
    "organization": {
      "primary": "กรมที่ดิน",
      "full": "กรมที่ดิน กระทรวงมหาดไทย",
      "responsible_department": null,  // สำนักมาตรฐานการทะเบียนที่ดิน เป็นต้น
      "service_location": [
        "สำนักงานที่ดินกรุงเทพมหานคร",
        "สำนักงานที่ดินจังหวัด",
        "สาขา",
        "ส่วนแยก"
      ]
    },
    
    // ========== CATEGORY (หลายระดับ) ==========
    "categories": {
      "level1": "การโอน",  // การโอน | ภาระผูกพัน | อื่นๆ | ระเบียบ
      "level2": "โอนอสังหาริมทรัพย์",
      "level3": "ไม่ต้องประกาศ",
      "tags": [
        "การโอน", "ขาย", "ที่ดิน", "ห้องชุด", "โฉนด",
        "ไม่ประกาศ", "e-QLands", "จองคิว"
      ],
      "process_type": "กระบวนงานบริการที่เบ็ดเสร็จในหน่วยเดียว",  // จากเอกสาร
      "service_category": "จดทะเบียน"  // จดทะเบียน | อนุมัติ | แจ้ง
    },
    
    // ========== SERVICE INFO (ข้อมูลบริการ) ==========
    "service": {
      // ระยะเวลา
      "processing": {
        "standard": {
          "time_minutes": 150,
          "time_display": "150 นาที",
          "time_unit": "นาที",
          "time_days": null
        },
        "alternative": {
          "method": "e-QLands",
          "time_minutes": 60,
          "time_display": "60 นาที (จองคิวล่วงหน้า)",
          "conditions": "ต้องจองคิวผ่านแอปพลิเคชัน e-QLands"
        },
        "varies_by": [
          "จำนวนคู่กรณี",
          "จำนวนหนังสือแสดงสิทธิ",
          "ความชัดเจนของหลักฐาน"
        ]
      },
      
      // ข้อกำหนด
      "requirements": {
        "requires_announcement": false,
        "announcement_period_days": null,
        "requires_court_order": false,
        "requires_consent": true,
        "consent_from": ["คู่สมรส"],
        "requires_inspection": false,
        "requires_survey": false
      },
      
      // ช่องทาง
      "channels": [
        {
          "type": "walk-in",
          "name": "ติดต่อด้วยตนเอง ณ หน่วยงาน",
          "available": true
        },
        {
          "type": "online",
          "name": "e-QLands",
          "available": true,
          "url": null
        },
        {
          "type": "e-service",
          "name": "สำนักงานที่ดินอิเล็กทรอนิกส์",
          "available": true,
          "url": "https://eservice.dol.go.th"
        }
      ],
      
      // เวลาให้บริการ
      "operating_hours": {
        "days": "วันจันทร์-วันศุกร์",
        "hours": "08:30-16:30 น.",
        "break_time": "มีพักเที่ยง",
        "holidays": "ยกเว้นวันหยุดที่ทางราชการกำหนด"
      }
    },
    
    // ========== STEPS (ขั้นตอนการดำเนินงาน) ==========
    "steps": [
      {
        "step_number": 1,
        "step_name": "การพิจารณา",
        "duration_minutes": 110,
        "description": "ยื่นคำขอ - ตรวจเอกสารหลักฐาน/สารบบที่ดิน - รับคำขอและสอบสวนคู่กรณี - ตรวจอายัด - ทำสัญญา - ลงนาม - ประเมินราคา - ชำระเงิน",
        "sub_steps": [
          "ยื่นคำขอ",
          "ตรวจเอกสารหลักฐาน/สารบบที่ดินและหนังสือแสดงสิทธิ",
          "รับคำขอและสอบสวนคู่กรณีตรวจอายัด",
          "ทำสัญญาหรือบันทึกข้อตกลงและแก้ทะเบียน",
          "คู่กรณีลงนามในสัญญาหรือบันทึกข้อตกลง",
          "ประเมินราคาทุนทรัพย์คำนวณค่าใช้จ่าย",
          "ผู้ขอชำระเงิน"
        ],
        "responsible": "-",
        "note": null
      },
      {
        "step_number": 2,
        "step_name": "การลงนาม",
        "duration_minutes": 40,
        "description": "เจ้าพนักงานที่ดินตรวจสอบเรื่อง - เรียกคู่กรณีสอบสวน - ลงนามจดทะเบียน - แจกหนังสือ - ตรวจสอบความถูกต้อง",
        "sub_steps": [
          "เจ้าพนักงานที่ดินตรวจสอบเรื่อง",
          "เรียกคู่กรณีสอบสวนก่อนการจดทะเบียน",
          "เจ้าพนักงานที่ดินลงนามจดทะเบียน/ประทับตรา",
          "แจกหนังสือแสดงสิทธิ์และสัญญา",
          "ผู้ขอตรวจสอบความถูกต้อง"
        ],
        "responsible": "-"
      }
    ],
    
    // ========== DOCUMENTS (เอกสารที่ต้องใช้) ==========
    "required_documents": {
      "mandatory": [
        {
          "doc_id": "1",
          "name": "โฉนดที่ดินหนังสือรับรองการทำประโยชน์หรือหนังสือกรรมสิทธิ์ห้องชุด",
          "type": "ต้นฉบับ",
          "original_count": 1,
          "copy_count": 0,
          "issuer": "กรมที่ดิน",
          "conditions": null,
          "applicable_to": ["ทุกกรณี"]
        },
        {
          "doc_id": "2",
          "name": "บัตรประจำตัวประชาชน",
          "type": "ต้นฉบับ",
          "original_count": 1,
          "copy_count": 0,
          "issuer": "กรมการปกครอง",
          "conditions": null,
          "applicable_to": ["ทุกกรณี"]
        }
      ],
      "conditional": [
        {
          "doc_id": "5",
          "name": "หนังสือยินยอมคู่สมรส",
          "type": "ต้นฉบับซึ่งผู้ขอจัดทำ",
          "original_count": 1,
          "copy_count": 0,
          "issuer": "-",
          "conditions": "ถ้ามีคู่สมรสโดยชอบด้วยกฎหมายและเป็นสินสมรส",
          "applicable_to": ["บุคคลธรรมดา"],
          "details": "พร้อมสำเนาบัตรประชาชนของคู่สมรสที่รับรองความถูกต้อง"
        },
        {
          "doc_id": "10",
          "name": "หลักฐานการให้ถ้อยคำ (คนไทยมีคู่สมรสต่างด้าว)",
          "type": "ต้นฉบับ",
          "original_count": 1,
          "copy_count": 0,
          "issuer": "-",
          "conditions": "กรณีคนไทยที่มีคู่สมรสต่างด้าวขอซื้อที่ดินหรือห้องชุดเพื่อเป็นสินส่วนตัว",
          "applicable_to": ["กรณีพิเศษ"],
          "details": "ให้ถ้อยคำต่อพนักงานว่าเงินที่ซื้อเป็นสินส่วนตัวของคนไทย"
        }
      ],
      "foreign_entities": [
        {
          "doc_id": "13",
          "name": "เอกสารนิติบุคคลต่างด้าว",
          "type": "ชุดเอกสาร",
          "original_count": 1,
          "copy_count": 0,
          "issuer": "-",
          "conditions": "กรณีนิติบุคคลต่างด้าว(จดทะเบียนต่างประเทศ) ขอซื้อห้องชุด",
          "applicable_to": ["นิติบุคคลต่างด้าว"],
          "sub_documents": [
            "หนังสือรับรองนิติบุคคล",
            "บัตรประชาชน/หนังสือเดินทางของกรรมการ",
            "รายงานการประชุม",
            "บัญชีรายชื่อผู้ถือหุ้น",
            "ข้อบังคับของนิติบุคคล",
            "หลักฐานการเป็นผู้ได้รับบัตรส่งเสริมการลงทุน",
            "หลักฐานการนำเงินตราต่างประเทศเข้ามา"
          ]
        }
      ],
      "total_doc_types": 22  // จากตาราง
    },
    
    // ========== FEES (ค่าธรรมเนียม) ==========
    "fees": {
      "application_fees": [
        {
          "item": "ค่าคำขอ (กรณีที่ดิน)",
          "amount": 5,
          "unit": "บาท",
          "calculation": "fixed",
          "per": "แปลง",
          "conditions": null
        },
        {
          "item": "ค่าคำขอ (กรณีห้องชุด)",
          "amount": 20,
          "unit": "บาท",
          "calculation": "fixed",
          "per": "ห้องชุด",
          "conditions": null
        }
      ],
      "registration_fees": [
        {
          "item": "ค่าธรรมเนียม",
          "amount": 2,
          "unit": "%",
          "calculation": "percentage",
          "base": "ราคาประเมิน",
          "conditions": "กรณีทั่วไป"
        },
        {
          "item": "ค่าธรรมเนียม (กรณีพิเศษ)",
          "amount": 0.5,
          "unit": "%",
          "calculation": "percentage",
          "base": "ราคาประเมิน",
          "conditions": "กรณีเป็นการโอนโดยเสน่หาไม่มีค่าตอบแทนระหว่างบุพการีกับผู้สืบสันดานหรือระหว่างคู่สมรส"
        }
      ],
      "taxes": [
        {
          "item": "ค่าภาษีหัก ณ ที่จ่าย",
          "amount": 1,
          "unit": "%",
          "calculation": "percentage",
          "base": "ราคาที่สูงกว่าระหว่างราคาประเมินกับราคาทุนทรัพย์ที่ผู้ขอแสดง",
          "conditions": "กรณีผู้โอนเป็นนิติบุคคล",
          "note": "สำหรับกรณีผู้โอนเป็นบุคคลธรรมดาคำนวณจากราคาประเมินตามวิธีการที่กำหนดในประมวลรัษฎากร"
        },
        {
          "item": "ค่าภาษีธุรกิจเฉพาะ",
          "amount": 3.3,
          "unit": "%",
          "calculation": "percentage",
          "base": "ราคาที่สูงกว่าระหว่างราคาประเมินกับราคาทุนทรัพย์ที่ผู้ขอแสดง",
          "conditions": "รวมภาษีท้องถิ่น",
          "note": "ถ้าเสียภาษีธุรกิจเฉพาะแล้วไม่ต้องเสียค่าอากรแสตมป์"
        },
        {
          "item": "ค่าอากรแสตมป์",
          "amount": 0.5,
          "unit": "%",
          "calculation": "percentage",
          "base": "ราคาที่สูงกว่าระหว่างราคาประเมินกับราคาทุนทรัพย์ที่ผู้ขอแสดง",
          "conditions": "กรณีผู้โอนเป็นบุคคลธรรมดาและไม่เสียภาษีธุรกิจเฉพาะ"
        }
      ],
      "other_fees": [
        {
          "item": "ค่าอากรคู่ฉบับ",
          "amount": 5,
          "unit": "บาท",
          "calculation": "fixed",
          "per": "ฉบับ",
          "conditions": "กรณีมีการจัดทำตราสารซึ่งมีข้อความอย่างเดียวกันกับต้นฉบับ"
        },
        {
          "item": "ค่ามอบอำนาจ (กรณีที่ดิน)",
          "amount": 20,
          "unit": "บาท",
          "calculation": "fixed",
          "per": "เรื่อง"
        },
        {
          "item": "ค่ามอบอำนาจ (กรณีห้องชุด)",
          "amount": 50,
          "unit": "บาท",
          "calculation": "fixed",
          "per": "เรื่อง"
        },
        {
          "item": "ค่าพยาน (กรณีที่ดิน)",
          "amount": 10,
          "unit": "บาท",
          "calculation": "fixed",
          "per": "คน"
        },
        {
          "item": "ค่าพยาน (กรณีห้องชุด)",
          "amount": 20,
          "unit": "บาท",
          "calculation": "fixed",
          "per": "คน"
        }
      ],
      "fee_summary": {
        "minimum_fee": 5,
        "typical_range": "2-3.8% ของราคาประเมิน",
        "varies_by": ["ประเภททรัพย์", "ประเภทคู่กรณี", "กรณีพิเศษ"]
      }
    },
    
    // ========== LEGAL REFERENCES (กฎหมายที่เกี่ยวข้อง) ==========
    "legal_references": [
      {
        "type": "พ.ร.บ.",
        "name": "ประมวลกฎหมายที่ดิน",
        "year": "2497",
        "section": null,
        "note": "และที่แก้ไขเพิ่มเติม"
      },
      {
        "type": "พ.ร.บ.",
        "name": "ประมวลกฎหมายแพ่งและพาณิชย์",
        "year": null,
        "section": "มาตรา 1382",
        "note": "การได้มาโดยการครอบครอง"
      },
      {
        "type": "กฎกระทรวง",
        "name": "กฎกระทรวงฉบับที่ 7",
        "year": "2497",
        "section": null,
        "note": "ออกตามความในพระราชบัญญัติให้ใช้ประมวลกฎหมายที่ดิน พ.ศ. 2497"
      },
      {
        "type": "กฎกระทรวง",
        "name": "กฎกระทรวงฉบับที่ 47",
        "year": "2541",
        "section": null,
        "note": "ออกตามความในพระราชบัญญัติให้ใช้ประมวลกฎหมายที่ดิน พ.ศ. 2497 และที่แก้ไขเพิ่มเติม"
      },
      {
        "type": "พ.ร.บ.",
        "name": "ประมวลรัษฎากร",
        "year": null,
        "section": null,
        "note": "เกี่ยวกับภาษี"
      }
    ],
    
    // ========== CONDITIONS & RESTRICTIONS (เงื่อนไขและข้อจำกัด) ==========
    "conditions": {
      "general_requirements": [
        "ผู้โอนจะต้องเป็นเจ้าของที่ดินหรือห้องชุดที่มีชื่อตนเองปรากฏอยู่ในหนังสือแสดงสิทธิ",
        "ผู้รับโอนต้องเป็นบุคคลที่มีสัญชาติไทย (เว้นแต่มีกฎหมายบัญญัติไว้โดยเฉพาะ)",
        "หากเป็นการโอนที่ดินพร้อมสิ่งปลูกสร้าง เจ้าของสิ่งปลูกสร้างจะต้องมีหลักฐานการเป็นเจ้าของ"
      ],
      "restrictions": {
        "foreigner_restrictions": "กรณีผู้รับโอนเป็นนิติบุคคลสัญชาติไทยแต่มีสิทธิการได้มาซึ่งที่ดินเสมือนคนต่างด้าวตามหลักเกณฑ์ที่กำหนดไว้ในมาตรา 97 และ 98 แห่งประมวลกฎหมายที่ดินไม่สามารถรับโอนได้",
        "condo_foreign_limit": "คนต่างด้าวถือกรรมสิทธิ์ในห้องชุดไม่เกินร้อยละ 49 ของเนื้อที่ห้องชุดทั้งหมด",
        "special_approval": "กรณีกฎหมายกำหนดให้ต้องมีหลักฐานคำยินยอมหรือต้องได้รับอนุญาตจากหน่วยงานใดหรือบุคคลใดก่อน"
      },
      "special_cases": {
        "thai_with_foreign_spouse": {
          "for_personal_property": "ต้องมาให้ถ้อยคำต่อพนักงานว่าเงินที่ซื้อเป็นสินส่วนตัวของคนไทย",
          "for_joint_property": "ใช้เอกสารตามหลักเกณฑ์พิเศษ"
        },
        "foreigner_buying_condo": {
          "requires": [
            "หนังสือเดินทาง",
            "ใบสำคัญถิ่นที่อยู่ (ตม.11, ตม.15, ตม.17)",
            "หลักฐานการนำเงินตราต่างประเทศเข้ามาจำนวนไม่น้อยกว่าค่าห้องชุด"
          ]
        },
        "minor_selling": "ต้องขออนุญาตศาลก่อน",
        "court_ordered": "ใช้คำพิพากษาหรือคำสั่งศาลและหนังสือรับรองคดีถึงที่สุด"
      },
      "applicable_to": [
        "บุคคลธรรมดา",
        "นิติบุคคล",
        "คนต่างด้าว (กรณีพิเศษ)",
        "นิติบุคคลต่างด้าว (กรณีห้องชุด)"
      ]
    },
    
    // ========== SPECIAL PROCEDURES (กระบวนการพิเศษ) ==========
    "special_procedures": {
      "e_qlands": {
        "enabled": true,
        "description": "จองคิวยื่นคำขอจดทะเบียนล่วงหน้าผ่านระบบ e-QLands",
        "platforms": ["Android", "iOS"],
        "time_saved": "ลดเวลาจาก 150 นาทีเหลือ 60 นาที",
        "requirements": "ต้องดาวน์โหลดแอปพลิเคชัน e-QLands และลงทะเบียนเข้าใช้งานในระบบ"
      },
      "e_service": {
        "enabled": false,  // ยังไม่เปิดให้โอนผ่าน e-service
        "url": "https://eservice.dol.go.th",
        "description": null
      },
      "survey_required": false,
      "announcement_required": false
    },
    
    // ========== COMPLAINT CHANNELS (ช่องทางร้องเรียน) ==========
    "complaint_channels": [
      {
        "type": "on-site",
        "name": "เจ้าพนักงานที่ดินจังหวัด/สาขา/ส่วนแยก",
        "contact": null
      },
      {
        "type": "dropbox",
        "name": "ตู้รับเรื่องร้องเรียนสำนักงานที่ดิน",
        "contact": null
      },
      {
        "type": "phone",
        "name": "กองตรวจราชการและเรื่องราวร้องทุกข์",
        "contact": "0 2141 5555"
      },
      {
        "type": "phone",
        "name": "ฝ่ายเรื่องราวร้องทุกข์ สำนักงานเลขานุการกรม",
        "contact": "0 2141 5500-4",
        "address": "ศูนย์ราชการเฉลิมพระเกียรติ 80 พรรษาฯ ชั้น 6 อาคารรัฐประศาสนภักดี ถนนแจ้งวัฒนะ แขวงทุ่งสองห้อง เขตหลักสี่ กรุงเทพฯ 10210"
      },
      {
        "type": "hotline",
        "name": "ศูนย์บริการประชาชน สำนักนายกรัฐมนตรี",
        "contact": "1111",
        "website": "www.1111.go.th",
        "address": "เลขที่ 1 ถ.พิษณุโลก เขตดุสิต กทม. 10300"
      },
      {
        "type": "anti-corruption",
        "name": "ศูนย์รับเรื่องร้องเรียนการทุจริตในภาครัฐ (ป.ป.ท.)",
        "contact": "1206",
        "phone": "0 2502 6670-80 ต่อ 1900, 1904-7",
        "fax": "0 2502 6132",
        "website": "www.pacc.go.th",
        "facebook": "www.facebook.com/PACC.GO.TH",
        "address": "99 หมู่ 4 อาคารซอฟต์แวร์ปาร์ค ชั้น 2 ถนนแจ้งวัฒนะ ตำบลคลองเกลือ อำเภอปากเกร็ด จังหวัดนนทบุรี 11120",
        "for_foreign_investors": {
          "phone": "+66 92 668 0777",
          "line": "Fad.pacc",
          "facebook": "The Anti-Corruption Operation Center",
          "email": "Fad.pacc@gmail.com"
        }
      }
    ],
    
    // ========== FORMS & REFERENCES (แบบฟอร์มและเอกสารอ้างอิง) ==========
    "forms": {
      "available": true,
      "location": "สามารถขอตรวจสอบจากพนักงานเจ้าหน้าที่ ณ สำนักงานที่ดินทุกแห่ง",
      "online_url": "www.dol.go.th/registry",
      "form_list": [
        "ท.ด.๑ (คำขอจดทะเบียนสิทธิและนิติกรรม)",
        "ท.ด.๙ (คำขอ)",
        "ท.ด.๑๓ (หนังสือสัญญาขาย)",
        "ท.ด.๑๖ (บันทึกข้อตกลงหรือบันทึกถ้อยคำ)"
      ]
    },
    
    // ========== METADATA REFERENCE INFO ==========
    "reference_info": {
      "source_system": "ระบบสารสนเทศศูนย์กลางข้อมูลคู่มือสำหรับประชาชน",
      "source_url": "info.go.th",
      "process_name": "จดทะเบียนประเภทโอนอสังหาริมทรัพย์กรณีไม่ต้องประกาศ (N)",
      "central_agency": "กรมที่ดิน",
      "service_type": "กระบวนงานบริการที่เบ็ดเสร็จในหน่วยเดียว",
      "service_category": "จดทะเบียน",
      "impact_level": "บริการทั่วไป",
      "service_area": ["ส่วนกลาง", "ส่วนภูมิภาค"],
      "legal_deadline": "0.0",  // ไม่มีกำหนดตามกฎหมาย
      "statistics": {
        "monthly_average": 0,
        "max_requests": 0,
        "min_requests": 0
      }
    },
    
    // ========== CONTENT ANALYSIS (วิเคราะห์เนื้อหา) ==========
    "content_features": {
      "has_tables": true,
      "table_count": 3,
      "table_types": ["ขั้นตอน", "เอกสาร", "ค่าธรรมเนียม", "ช่องทางร้องเรียน"],
      
      "has_lists": true,
      "list_count": 5,
      "list_types": ["numbered", "bulleted"],
      
      "has_legal_references": true,
      "legal_ref_count": 5,
      
      "has_examples": false,
      "has_diagrams": false,
      "has_calculations": true,
      "calculation_types": ["percentage", "fixed_amount"],
      
      "special_sections": [
        "กรณีจองคิวยื่นคำขอจดทะเบียนล่วงหน้าผ่านระบบ e-QLands",
        "กรณีคนไทยที่มีคู่สมรสต่างด้าว",
        "กรณีนิติบุคคลต่างด้าว"
      ]
    },
    
    // ========== SEARCH & RETRIEVAL ==========
    "search_optimization": {
      "primary_keywords": [
        "โอน", "ขาย", "ที่ดิน", "ห้องชุด", "โฉนด",
        "อสังหาริมทรัพย์", "จดทะเบียน", "ไม่ประกาศ"
      ],
      "secondary_keywords": [
        "คู่สมรส", "นิติบุคคล", "คนต่างด้าว", "e-QLands",
        "ค่าธรรมเนียม", "เอกสาร", "ขั้นตอน"
      ],
      "synonyms": {
        "โอน": ["ขาย", "โอนกรรมสิทธิ์", "transfer", "ซื้อขาย"],
        "ที่ดิน": ["โฉนด", "อสังหาริมทรัพย์", "land", "property"],
        "ห้องชุด": ["คอนโด", "condominium", "condo"],
        "เอกสาร": ["หลักฐาน", "documents"],
        "ค่าธรรมเนียม": ["ค่าใช้จ่าย", "fees", "ภาษี", "tax"]
      },
      "entity_types": [
        "บุคคลธรรมดา", "นิติบุคคล", "คนต่างด้าว",
        "นิติบุคคลต่างด้าว", "คู่สมรส"
      ],
      "process_variants": [
        "โอนไม่ต้องประกาศ",
        "โอนไม่ประกาศ",
        "โอนอสังหาริมทรัพย์",
        "จดทะเบียนโอน",
        "ขายที่ดิน",
        "ซื้อขายที่ดิน"
      ]
    },
    
    // ========== TIMESTAMPS & STATUS ==========
    "timestamps": {
      "created_at": "2026-02-12T10:00:00Z",
      "updated_at": "2026-02-12T10:00:00Z",
      "indexed_at": "2026-02-12T10:05:00Z",
      "published_date": "2022",
      "last_verified": "2026-02-12"
    },
    
    "status": {
      "active": true,
      "is_latest": true,
      "superseded_by": null,
      "related_documents": [
        "doc_002",  // โอนต้องประกาศ
        "doc_003",  // จำนอง
        "doc_015"   // โอนมรดก
      ]
    }
  }
}
```

### 1.2 Collection: chunks (ระดับ Chunk)

```json
{
  "_id": "chunk_001_001",
  "embedding": [0.789, 0.012, ...],
  
  "metadata": {
    // === CHUNK IDENTITY ===
    "parent_document_id": "doc_001",
    "chunk_index": 1,
    "chunk_type": "criteria",  
    // Types: header | criteria | channels | steps | documents | fees | 
    //        legal | complaints | forms | table | special_section
    
    // === CONTENT ===
    "text": "หลักเกณฑ์ วิธีการ เงื่อนไข...",
    "text_length": 850,
    "text_display": "หลักเกณฑ์ วิธีการ เงื่อนไข (ถ้ามี) ในการยื่นคำขอ...",  // ย่อ 150 ตัวอักษร
    "language": "th",
    
    // === POSITION IN DOCUMENT ===
    "position": {
      "start_line": 5,
      "end_line": 28,
      "start_char": 245,
      "end_char": 1095,
      "position_in_doc": "beginning",  // beginning | middle | end
      "section_order": 1
    },
    
    // === CONTEXT & HIERARCHY ===
    "context": {
      "section_title": "หลักเกณฑ์ วิธีการ เงื่อนไข",
      "subsection": "กรณีทั่วไป",
      "parent_section": null,
      "previous_chunk_id": null,
      "next_chunk_id": "chunk_001_002",
      "related_chunks": ["chunk_001_005", "chunk_001_008"]  // chunks ที่เกี่ยวข้อง
    },
    
    // === INHERIT FROM PARENT ===
    "document_info": {
      "document_title": "จดทะเบียนประเภทโอนอสังหาริมทรัพย์กรณีไม่ต้องประกาศ",
      "document_type": "คู่มือปชช",
      "category_level1": "การโอน",
      "category_level2": "โอนอสังหาริมทรัพย์",
      "version": "N"
    },
    
    // === EXTRACTED ENTITIES ===
    "entities": {
      "laws": [
        "พระราชบัญญัติให้ใช้ประมวลกฎหมายที่ดิน พ.ศ. 2497",
        "กฎกระทรวงฉบับที่ 7 (พ.ศ. 2497)",
        "มาตรา 1382 ประมวลกฎหมายแพ่งและพาณิชย์"
      ],
      "documents": [
        "โฉนดที่ดิน",
        "หนังสือรับรองการทำประโยชน์",
        "หนังสือกรรมสิทธิ์ห้องชุด",
        "บัตรประชาชน"
      ],
      "fees": ["5 บาท", "20 บาท", "2%", "0.5%"],
      "durations": ["150 นาที", "60 นาที", "110 นาที", "40 นาที"],
      "organizations": [
        "กรมที่ดิน",
        "สำนักงานที่ดิน",
        "กระทรวงมหาดไทย"
      ],
      "locations": [
        "สำนักงานที่ดินกรุงเทพมหานคร",
        "สำนักงานที่ดินจังหวัด"
      ],
      "persons": [
        "ผู้โอน",
        "ผู้รับโอน",
        "เจ้าพนักงานที่ดิน",
        "คู่สมรส",
        "คนต่างด้าว"
      ],
      "numbers": ["1", "2", "3", "97", "98", "30", "49"]
    },
    
    // === CONTENT TYPE ANALYSIS ===
    "content_analysis": {
      "has_table": false,
      "has_list": true,
      "list_items_count": 7,
      "has_legal_ref": true,
      "legal_ref_count": 3,
      "has_example": false,
      "has_calculation": false,
      "has_conditions": true,
      "condition_count": 5,
      "has_exceptions": true,
      "exception_count": 2
    },
    
    // === IMPORTANCE & RELEVANCE ===
    "importance": {
      "score": 0.95,  // 0-1
      "is_key_information": true,
      "is_requirement": true,
      "is_restriction": false,
      "is_procedure": false,
      "is_cost_info": false,
      "affects": ["ทุกกรณี", "บุคคลธรรมดา", "นิติบุคคล"]
    },
    
    // === QUESTION ANSWERING HINTS ===
    "qa_hints": {
      "can_answer": [
        "ต้องใช้เอกสารอะไรบ้าง",
        "ผู้โอนต้องเป็นใคร",
        "ผู้รับโอนต้องมีคุณสมบัติอย่างไร",
        "มีกฎหมายอะไรบ้างที่เกี่ยวข้อง"
      ],
      "question_types": [
        "requirements",
        "eligibility",
        "legal_basis",
        "conditions"
      ]
    },
    
    // === TIMESTAMPS ===
    "timestamps": {
      "created_at": "2026-02-12T10:05:00Z",
      "updated_at": "2026-02-12T10:05:00Z"
    }
  }
}
```

---

## 🔪 2. COMPREHENSIVE Chunking Strategy

### 2.1 Document Structure Patterns (จากเอกสารจริง)

```yaml
# Pattern 1: คู่มือปชช (Standard)
Structure:
  - Header: "คู่มือสำหรับประชาชน : {title}"
  - Organization: "หน่วยงานที่ให้บริการ"
  - Criteria: "หลักเกณฑ์ วิธีการ เงื่อนไข" (ยาวที่สุด 1000-2000 tokens)
  - Special Section: "*** กรณีจองคิวยื่นคำขอ..." (optional)
  - Channels Table: "ช่องทางการให้บริการ"
  - Steps Table: "ขั้นตอน ระยะเวลา และส่วนงานที่รับผิดชอบ"
  - Alternative Steps Table: "กรณี e-QLands" (optional)
  - Documents Table: "รายการเอกสารหลักฐานประกอบ" (ยาว 22 รายการ)
  - Fees Table: "ค่าธรรมเนียม" (13 รายการ)
  - Complaints Table: "ช่องทางการร้องเรียน"
  - Forms: "แบบฟอร์ม ตัวอย่างและคู่มือการกรอก"
  - Metadata: "ชื่อกระบวนงาน", "กฎหมายที่เกี่ยวข้อง"

# Pattern 2: คู่มือเจ้าหน้าที่ (Detailed)
Structure:
  - Title: "การจดทะเบียน{type}"
  - Definition: "ความหมาย"
  - Laws: "กฎหมาย ระเบียบ และคำสั่งที่เกี่ยวข้อง"
  - Categories: "ประเภทการจดทะเบียน" (1. 2. 3.)
  - Core Content: "สาระสำคัญ" (มี bullets หลายข้อ)
  - Procedures: "การตรวจสอบก่อนจดทะเบียน" (มี sub-procedures)
  - Registration: "การจดทะเบียนสิทธิและนิติกรรม"
  - Examples: ตัวอย่างเคสต่างๆ (optional)

# Pattern 3: ระเบียบกรม (Legal)
Structure:
  - Title: "ระเบียบกรมที่ดิน"
  - Subtitle: "ว่าด้วย{subject}"
  - Year: "พ.ศ. {year}"
  - Preamble: "โดยที่..."
  - Legal Basis: "อาศัยอำนาจตาม..."
  - Articles: "ข้อ 1, ข้อ 2, ข้อ 3..." (มี hierarchy)
  - Chapters: "หมวด 1, หมวด 2..." (optional)
  - Sections: "ส่วนที่ 1, ส่วนที่ 2..." (optional)
  - Definitions: "ข้อ X ในระเบียบนี้..."
  - Signature: "(ชื่อ) อธิบดีกรมที่ดิน"
  - Announcement: "ประกาศกรมที่ดิน เรื่อง..." (optional)
```

### 2.2 Chunking Rules (ละเอียดครบถ้วน)

```python
CHUNKING_RULES = {
    # Rule 1: Section-Based (ลำดับแรก - ใช้กับทุกเอกสาร)
    "section_based": {
        "priority": 1,
        "method": "split_by_section_headers",
        "section_patterns": [
            r"^หลักเกณฑ์",
            r"^ช่องทางการให้บริการ",
            r"^ขั้นตอน",
            r"^รายการเอกสาร",
            r"^ค่าธรรมเนียม",
            r"^ช่องทางการร้องเรียน",
            r"^\*\*\*\s+กรณี",  # Special sections
            r"^หมวด\s+\d+",  # สำหรับระเบียบ
            r"^ส่วนที่\s+\d+"  # สำหรับระเบียบ
        ],
        "max_tokens": 1000
    },
    
    # Rule 2: Table Preservation (สำคัญมาก!)
    "table_preservation": {
        "priority": 2,
        "method": "preserve_complete_table",
        "table_markers": {
            "start": ["|  |  |", "| --- | --- |"],
            "end": ["", "\n\n"]
        },
        "actions": {
            "if_too_long": "split_by_logical_groups",  # แบ่งตามกลุ่มแถว
            "maintain_header": true,  # เก็บ header ไว้ทุก chunk
            "convert_to_text": true,  # แปลงเป็น text ที่อ่านง่าย
            "preserve_structure": true  # เก็บ structured data
        },
        "max_tokens": 1500  # ตารางให้ยาวกว่าปกติ
    },
    
    # Rule 3: List Handling
    "list_handling": {
        "priority": 3,
        "method": "preserve_list_integrity",
        "list_patterns": {
            "numbered": r"^\d+\.",
            "bulleted": r"^[-•]",
            "lettered": r"^\([ก-ฮ]\)",
            "sub_numbered": r"^\(\d+\)"
        },
        "actions": {
            "if_short": "keep_complete",  # < 800 tokens เก็บทั้งหมด
            "if_long": "split_by_logical_groups",  # แบ่งเป็นกลุ่ม 5-10 items
            "maintain_numbering": true,
            "add_overlap": true,  # 2-3 items overlap
        },
        "max_tokens": 1200
    },
    
    # Rule 4: Legal Article Handling (สำหรับระเบียบ/กฎหมาย)
    "legal_article": {
        "priority": 4,
        "method": "preserve_article_context",
        "article_patterns": [
            r"^ข้อ\s+\d+",
            r"^มาตรา\s+\d+",
            r"^\([๑-๙]+\)"
        ],
        "context_window": {
            "before_tokens": 100,
            "after_tokens": 100
        },
        "actions": {
            "keep_hierarchy": true,  # เก็บ หมวด > ส่วน > ข้อ
            "preserve_references": true,  # "ตามข้อ X", "ดังข้อ Y"
        },
        "max_tokens": 800
    },
    
    # Rule 5: Special Section Handling
    "special_section": {
        "priority": 5,
        "method": "preserve_special_markers",
        "markers": [
            r"^\*\*\*",  # *** กรณี...
            r"^หมายเหตุ",
            r"^ทั้งนี้",
            r"^เว้นแต่",
            r"^กรณี"
        ],
        "actions": {
            "keep_complete": true,
            "mark_as_important": true,
            "preserve_context": true
        },
        "max_tokens": 1000
    },
    
    # Rule 6: Numbered Criteria (หลักเกณฑ์ที่มีเลข)
    "numbered_criteria": {
        "priority": 6,
        "method": "split_by_number_maintaining_context",
        "pattern": r"^\d+\.",
        "actions": {
            "if_paragraph_short": "keep_with_next",  # < 200 tokens
            "if_paragraph_long": "split_independent",  # > 600 tokens
            "maintain_sequence": true,
            "add_section_title": true  # เพิ่ม "หลักเกณฑ์ข้อ X:"
        },
        "target_tokens": 600
    },
    
    # Rule 7: Complex Documents List (22 รายการ)
    "long_document_list": {
        "priority": 7,
        "method": "intelligent_grouping",
        "threshold": 10,  # > 10 items = split
        "grouping_strategy": {
            "method": "by_category",
            "categories": [
                "mandatory",  # เอกสารบังคับ (1-5)
                "conditional",  # เอกสารตามเงื่อนไข (6-15)
                "special_cases",  # กรณีพิเศษ (16-22)
                "foreign_entities"  # คนต่างด้าว
            ],
            "overlap_items": 2
        },
        "max_tokens": 1200
    }
}
```

### 2.3 Chunking Algorithm (Production-Ready)

```python
def chunk_document(document, document_type):
    """
    Production-ready chunking algorithm
    อิงจากโครงสร้างเอกสารจริง
    """
    chunks = []
    
    # Step 1: Identify document type and load pattern
    if document_type == "คู่มือปชช":
        pattern = PATTERNS["standard_manual"]
    elif document_type == "คู่มือเจ้าหน้าที่":
        pattern = PATTERNS["detailed_manual"]
    elif document_type == "ระเบียบกรม":
        pattern = PATTERNS["regulation"]
    else:
        pattern = PATTERNS["generic"]
    
    # Step 2: Parse document structure
    sections = parse_document_structure(document, pattern)
    
    # Step 3: Process each section
    for section in sections:
        section_type = identify_section_type(section)
        
        # ===== TABLE HANDLING =====
        if section_type == "table":
            table_chunks = process_table(section)
            chunks.extend(table_chunks)
        
        # ===== CRITERIA HANDLING (ยาวมาก 1000-2000 tokens) =====
        elif section_type == "criteria":
            # แบ่งตามเลข 1. 2. 3.
            numbered_items = split_by_pattern(section, r"^\d+\.")
            
            for i, item in enumerate(numbered_items):
                token_count = count_tokens(item)
                
                if token_count <= 600:
                    # เก็บข้อเดียว
                    chunks.append(create_chunk(
                        text=item,
                        type="criteria_item",
                        index=i+1,
                        importance=0.95
                    ))
                else:
                    # แบ่งย่อยด้วย semantic splitting
                    sub_chunks = semantic_split(
                        item,
                        target_size=600,
                        overlap=100
                    )
                    chunks.extend(sub_chunks)
        
        # ===== DOCUMENT LIST (22 items) =====
        elif section_type == "documents":
            doc_items = extract_table_rows(section)
            
            if len(doc_items) > 10:
                # แบ่งเป็นกลุ่ม
                groups = {
                    "mandatory": doc_items[0:5],
                    "conditional": doc_items[5:15],
                    "special": doc_items[15:]
                }
                
                for group_name, items in groups.items():
                    chunk = create_document_list_chunk(
                        items=items,
                        group=group_name,
                        overlap_with_next=2
                    )
                    chunks.append(chunk)
            else:
                # เก็บทั้งหมด
                chunks.append(create_chunk(
                    text=section,
                    type="documents_complete"
                ))
        
        # ===== FEE TABLE =====
        elif section_type == "fees":
            # แปลงตารางเป็น structured data + text
            fee_chunk = create_fee_chunk(
                section,
                convert_to_structured=True,
                convert_to_text=True
            )
            chunks.append(fee_chunk)
        
        # ===== STEPS TABLE =====
        elif section_type == "steps":
            steps = extract_steps_from_table(section)
            
            for step in steps:
                chunks.append(create_chunk(
                    text=step["description"],
                    type="step",
                    step_number=step["number"],
                    duration=step["duration"]
                ))
        
        # ===== LEGAL ARTICLES (ระเบียบ) =====
        elif section_type == "legal_article":
            article_chunks = process_legal_article(
                section,
                preserve_hierarchy=True,
                context_window=100
            )
            chunks.extend(article_chunks)
        
        # ===== SPECIAL SECTIONS =====
        elif section_type == "special":
            # *** กรณีจองคิว e-QLands
            chunks.append(create_chunk(
                text=section,
                type="special_procedure",
                importance=0.90,
                mark_as_special=True
            ))
        
        # ===== DEFAULT: SLIDING WINDOW =====
        else:
            default_chunks = sliding_window_split(
                section,
                window_size=600,
                overlap=100
            )
            chunks.extend(default_chunks)
    
    # Step 4: Post-processing
    chunks = add_metadata(chunks, document)
    chunks = add_cross_references(chunks)
    chunks = calculate_importance_scores(chunks)
    chunks = add_qa_hints(chunks)
    
    # Step 5: Quality check
    chunks = validate_chunks(chunks)
    
    return chunks


def create_fee_chunk(section, convert_to_structured=True, convert_to_text=True):
    """
    สร้าง chunk สำหรับค่าธรรมเนียม
    เก็บทั้ง structured data และ text
    """
    # Extract from table
    fees = extract_fees_from_table(section)
    
    # Structured data
    structured = {
        "fees": []
    }
    
    # Text representation
    text_parts = ["ค่าธรรมเนียม:\n"]
    
    for i, fee in enumerate(fees, 1):
        structured["fees"].append({
            "item": fee["item"],
            "amount": fee["amount"],
            "unit": fee["unit"],
            "conditions": fee.get("conditions")
        })
        
        text_parts.append(
            f"{i}. {fee['item']}: {fee['amount']} {fee['unit']}"
        )
        if fee.get("conditions"):
            text_parts.append(f"   ({fee['conditions']})")
    
    return {
        "text": "\n".join(text_parts),
        "structured_data": structured,
        "type": "fees_complete",
        "importance": 0.95
    }
```

---

## 📈 3. Real-World Chunking Examples

### Example 1: หลักเกณฑ์ยาว (~1500 tokens)

**Input:**
```
หลักเกณฑ์ วิธีการ เงื่อนไข (ถ้ามี) ในการยื่นคำขอ และในการพิจารณาอนุญาต

1.กรณียื่นคำขอและจดทะเบียนเสร็จในวันเดียว... (300 tokens)
2.การขอจดทะเบียนประเภทการโอน... (250 tokens)
3. ผู้โอนจะต้องเป็นเจ้าของที่ดิน... (200 tokens)
กรณีผู้รับโอนเป็นนิติบุคคล... (150 tokens)
4. หากเป็นการโอนที่ดินพร้อมสิ่งปลูกสร้าง... (100 tokens)
5. ผู้ขอต้องยื่นเอกสารหลักฐาน... (200 tokens)
6. พนักงานเจ้าหน้าที่ต้องสอบสวน... (150 tokens)
7. ระยะเวลาดำเนินการ... (300 tokens)
```

**Output (3 chunks):**

```python
chunk_1 = {
    "text": """หลักเกณฑ์ วิธีการ เงื่อนไข (ถ้ามี) ในการยื่นคำขอ

    1. กรณียื่นคำขอและจดทะเบียนเสร็จในวันเดียว...
    2. การขอจดทะเบียนประเภทการโอน...""",
    "type": "criteria_general",
    "chunk_index": 1,
    "tokens": 550,
    "importance": 0.95,
    "entities": {
        "laws": ["กฎกระทรวงฉบับที่ 7 (พ.ศ. 2497)"],
        "documents": ["โฉนดที่ดิน", "หนังสือรับรองการทำประโยชน์"],
        "keywords": ["จดทะเบียน", "โอน", "ประกาศ"]
    }
}

chunk_2 = {
    "text": """หลักเกณฑ์ (ต่อ):
    
    2. ...แลกเปลี่ยน หลุดเป็นสิทธิจากจำนอง...
    3. ผู้โอนจะต้องเป็นเจ้าของที่ดินหรือห้องชุด...
    กรณีผู้รับโอนเป็นนิติบุคคลสัญชาติไทยแต่มีสิทธิ...
    4. หากเป็นการโอนที่ดินพร้อมสิ่งปลูกสร้าง...
    5. ผู้ขอต้องยื่นเอกสารหลักฐาน...""",
    "type": "criteria_requirements",
    "chunk_index": 2,
    "tokens": 600,
    "importance": 0.90,
    "previous_chunk": "chunk_001_001",
    "entities": {
        "laws": ["มาตรา 97", "มาตรา 98"],
        "persons": ["ผู้โอน", "ผู้รับโอน", "นิติบุคคล"],
        "conditions": ["สัญชาติไทย", "คนต่างด้าว"]
    }
}

chunk_3 = {
    "text": """หลักเกณฑ์ (ต่อ):
    
    5. ...รับบัตรคิวเพื่อรอยื่นคำขอและสอบสวน...
    6. พนักงานเจ้าหน้าที่ต้องสอบสวนสิทธิและความสามารถ...
    7. ระยะเวลาดำเนินการอาจใช้เวลาน้อยกว่า 150 นาที...""",
    "type": "criteria_process",
    "chunk_index": 3,
    "tokens": 450,
    "importance": 0.85,
    "previous_chunk": "chunk_001_002",
    "entities": {
        "duration": ["150 นาที"],
        "organizations": ["สำนักงานที่ดิน"],
        "persons": ["พนักงานเจ้าหน้าที่", "เจ้าพนักงานที่ดิน"]
    }
}
```

### Example 2: ตารางเอกสาร 22 รายการ

**Input:**
```
รายการเอกสาร หลักฐานประกอบ

1) โฉนดที่ดิน... ฉบับจริง1ฉบับ
2) บัตรประจำตัวประชาชน... ฉบับจริง1ฉบับ
...
10) กรณีคนไทยที่มีคู่สมรสต่างด้าว...
...
22) หนังสือมอบอำนาจ (กรณีนิติบุคคล)...
```

**Output (3 chunks + structured):**

```python
chunk_docs_1 = {
    "text": """รายการเอกสารหลักฐานประกอบ (เอกสารบังคับ):
    
    1) โฉนดที่ดิน หนังสือรับรองการทำประโยชน์ หรือหนังสือกรรมสิทธิ์ห้องชุด
       - ประเภท: ต้นฉบับ
       - จำนวน: ฉบับจริง 1 ฉบับ
       - ผู้ออก: กรมที่ดิน
    
    2) บัตรประจำตัวประชาชน
       - ประเภท: ต้นฉบับ
       - จำนวน: ฉบับจริง 1 ฉบับ
       - ผู้ออก: กรมการปกครอง
    
    ...(รายการที่ 3-5)...""",
    "type": "documents_mandatory",
    "chunk_index": 1,
    "doc_group": "mandatory",
    "doc_count": 5,
    "importance": 0.95
}

chunk_docs_2 = {
    "text": """รายการเอกสารหลักฐานประกอบ (ตามเงื่อนไข):
    
    ...(overlap 2 items จาก chunk 1)...
    
    5) หนังสือยินยอมคู่สมรส
       - เงื่อนไข: ถ้ามีคู่สมรสโดยชอบด้วยกฎหมายและเป็นสินสมรส
       ...
    
    10) กรณีคนไทยที่มีคู่สมรสต่างด้าวขอซื้อที่ดิน
        - วิธีการ: (1) ให้ถ้อยคำต่อพนักงาน...
    
    ...(รายการที่ 6-15)...""",
    "type": "documents_conditional",
    "chunk_index": 2,
    "doc_group": "conditional",
    "doc_count": 10,
    "previous_chunk": "chunk_001_006",
    "importance": 0.80
}

chunk_docs_3 = {
    "text": """รายการเอกสารหลักฐานประกอบ (กรณีพิเศษ):
    
    ...(overlap 2 items)...
    
    13) กรณีนิติบุคคลต่างด้าว(จดทะเบียนต่างประเทศ) ขอซื้อห้องชุด
        ต้องใช้หลักฐาน 7 รายการ:
        (1) หนังสือรับรองนิติบุคคล...
        (2) บัตรประจำตัวประชาชน/หนังสือเดินทาง...
        ...
    
    22) หนังสือมอบอำนาจ (กรณีนิติบุคคล)...""",
    "type": "documents_special",
    "chunk_index": 3,
    "doc_group": "special_cases",
    "doc_count": 7,
    "previous_chunk": "chunk_001_007",
    "importance": 0.70,
    "entities": {
        "special_groups": ["นิติบุคคลต่างด้าว", "คนต่างด้าว"]
    }
}

# Structured data (ไว้สำหรับ filter)
structured_docs = {
    "total_documents": 22,
    "mandatory_count": 2,
    "conditional_count": 20,
    "documents": [
        {
            "id": 1,
            "name": "โฉนดที่ดิน",
            "required": true,
            "issuer": "กรมที่ดิน"
        },
        ...
    ]
}
```

### Example 3: ระเบียบกรม (กฎหมาย)

**Input:**
```
ระเบียบกรมที่ดิน
ว่าด้วยหลักเกณฑ์และวิธีการขอหนังสือรับรอง...
พ.ศ. ๒๕๖๘

...preamble...

ข้อ ๑ ระเบียบนี้เรียกว่า "ระเบียบกรมที่ดิน..."
ข้อ ๒ ระเบียบนี้ให้ใช้บังคับตั้งแต่วันที่...
ข้อ ๓ บรรดาระเบียบ...
ข้อ ๔ ในระเบียบนี้
"ข้อมูลอิเล็กทรอนิกส์" หมายความว่า...
"ระบบอิเล็กทรอนิกส์" หมายความว่า...

หมวด ๑
บททั่วไป

ข้อ ๗ ผู้ประสงค์จะดำเนินการ...
```

**Output:**

```python
chunk_reg_1 = {
    "text": """ระเบียบกรมที่ดิน
    ว่าด้วยหลักเกณฑ์และวิธีการขอหนังสือรับรองราคาประเมินทุนทรัพย์...
    พ.ศ. ๒๕๖๘
    
    [preamble]
    
    ข้อ ๑ ระเบียบนี้เรียกว่า "ระเบียบกรมที่ดิน ว่าด้วย..."
    ข้อ ๒ ระเบียบนี้ให้ใช้บังคับตั้งแต่วันที่ ๑๗ กุมภาพันธ์ พ.ศ. ๒๕๖๘
    ข้อ ๓ บรรดาระเบียบ ข้อกำหนด หรือคำสั่งอื่นใด...""",
    "type": "legal_introduction",
    "chunk_index": 1,
    "law_year": "2568",
    "articles": ["ข้อ 1", "ข้อ 2", "ข้อ 3"],
    "importance": 0.90
}

chunk_reg_2 = {
    "text": """ข้อ ๔ ในระเบียบนี้
    
    "ข้อมูลอิเล็กทรอนิกส์" หมายความว่า ข้อความที่ได้สร้าง ส่ง รับ...
    
    "ระบบอิเล็กทรอนิกส์" หมายความว่า ระบบงานของกรมที่ดิน...
    
    "ผู้ใช้ระบบ" หมายความว่า บุคคลธรรมดา หรือนิติบุคคล...""",
    "type": "legal_definitions",
    "chunk_index": 2,
    "article": "ข้อ 4",
    "definition_count": 7,
    "importance": 0.95,
    "entities": {
        "defined_terms": [
            "ข้อมูลอิเล็กทรอนิกส์",
            "ระบบอิเล็กทรอนิกส์",
            "ผู้ใช้ระบบ"
        ]
    }
}

chunk_reg_3 = {
    "text": """หมวด ๑
    บททั่วไป
    
    ข้อ ๗ ผู้ประสงค์จะดำเนินการตามระเบียบนี้ ให้ลงทะเบียน...
    (๑) นำบัตรประจำตัวประชาชนไปแสดงตัว...
    (๒) กรณีลงทะเบียนเข้าใช้งานผ่านระบบ Digital ID...""",
    "type": "legal_procedure",
    "chunk_index": 3,
    "chapter": "หมวด 1",
    "article": "ข้อ 7",
    "importance": 0.85,
    "previous_chunk": "chunk_003_002"
}
```

---

## 🎯 4. Metadata Extraction (จากเอกสารจริง)

```python
def extract_comprehensive_metadata(document_text, file_path):
    """
    Extract metadata from real documents
    """
    metadata = {}
    
    # ===== TITLE EXTRACTION =====
    # Pattern 1: คู่มือปชช
    if match := re.search(r'คู่มือสำหรับประชาชน\s*:\s*(.+?)(?:\n|$)', document_text):
        metadata['title'] = match.group(1).strip()
        metadata['document_type'] = 'คู่มือปชช'
    
    # Pattern 2: ระเบียบกรม
    elif match := re.search(r'ระเบียบกรมที่ดิน\s*\n\s*ว่าด้วย(.+?)(?:\n|พ\.ศ\.)', document_text, re.DOTALL):
        metadata['title'] = f"ระเบียบกรมที่ดิน ว่าด้วย{match.group(1).strip()}"
        metadata['document_type'] = 'ระเบียบกรม'
    
    # Pattern 3: คู่มือเจ้าหน้าที่
    elif match := re.search(r'การจดทะเบียน(.+?)(?:\n|$)', document_text):
        metadata['title'] = f"การจดทะเบียน{match.group(1).strip()}"
        metadata['document_type'] = 'คู่มือเจ้าหน้าที่'
    
    # ===== ORGANIZATION =====
    if match := re.search(r'หน่วยงานที่ให้บริการ\s*:\s*(.+?)(?:\n|$)', document_text):
        metadata['organization'] = match.group(1).strip()
    
    # ===== VERSION =====
    if '(N)' in file_path or '(N)' in document_text:
        metadata['version'] = 'N'
        metadata['is_latest'] = True
    
    # ===== YEAR =====
    if match := re.search(r'พ\.ศ\.\s*(\d{4})', document_text):
        metadata['law_year'] = match.group(1)
    
    # ===== PROCESSING TIME =====
    times = []
    for match in re.finditer(r'(\d+)\s*นาที', document_text):
        times.append(int(match.group(1)))
    
    if times:
        metadata['processing_time_minutes'] = min(times)  # เอาเวลาน้อยที่สุด
        metadata['all_times'] = times
    
    # Check for days
    if match := re.search(r'(\d+)\s*วัน', document_text):
        metadata['processing_time_days'] = int(match.group(1))
    
    # ===== FEES =====
    fees = []
    
    # Pattern: "X บาท"
    for match in re.finditer(r'(\d+(?:\.\d+)?)\s*บาท', document_text):
        fees.append({
            'amount': float(match.group(1)),
            'unit': 'บาท',
            'type': 'fixed'
        })
    
    # Pattern: "X %"
    for match in re.finditer(r'(\d+(?:\.\d+)?)\s*%', document_text):
        fees.append({
            'amount': float(match.group(1)),
            'unit': '%',
            'type': 'percentage'
        })
    
    # Pattern: "ร้อยละ X"
    for match in re.finditer(r'ร้อยละ\s*(\d+(?:\.\d+)?)', document_text):
        fees.append({
            'amount': float(match.group(1)),
            'unit': '%',
            'type': 'percentage'
        })
    
    metadata['fees'] = unique_fees(fees)
    
    # ===== LEGAL REFERENCES =====
    legal_refs = []
    
    # Pattern: "พ.ร.บ."
    for match in re.finditer(r'พ(?:ระ)?\.?ร(?:าช)?\.?บ(?:ัญญัติ)?\.?\s*([^\n]+?)(?:\s+พ\.ศ\.\s*(\d{4}))?', document_text):
        legal_refs.append({
            'type': 'พ.ร.บ.',
            'name': match.group(1).strip(),
            'year': match.group(2) if match.group(2) else None
        })
    
    # Pattern: "กฎกระทรวง"
    for match in re.finditer(r'กฎกระทรวง(?:ฉบับที่\s*(\d+))?\s*\(พ\.ศ\.\s*(\d{4})\)', document_text):
        legal_refs.append({
            'type': 'กฎกระทรวง',
            'number': match.group(1),
            'year': match.group(2)
        })
    
    # Pattern: "มาตรา X"
    for match in re.finditer(r'มาตรา\s*(\d+(?:\s+ทวิ)?)', document_text):
        legal_refs.append({
            'type': 'มาตรา',
            'section': match.group(1).strip()
        })
    
    metadata['legal_references'] = legal_refs
    
    # ===== DOCUMENTS REQUIRED =====
    if match := re.search(r'รายการเอกสาร\s+หลักฐานประกอบ(.*?)(?:ค่าธรรมเนียม|$)', document_text, re.DOTALL):
        doc_section = match.group(1)
        doc_count = len(re.findall(r'^\d+\)', doc_section, re.MULTILINE))
        metadata['required_documents_count'] = doc_count
    
    # ===== SPECIAL FEATURES =====
    metadata['has_e_qlands'] = 'e-QLands' in document_text or 'e-Qlands' in document_text
    metadata['has_e_service'] = 'e-Service' in document_text or 'e-service' in document_text
    metadata['requires_announcement'] = 'ต้องประกาศ' in document_text
    metadata['requires_court'] = 'คำสั่งศาล' in document_text or 'คำพิพากษา' in document_text
    
    # ===== CATEGORIES =====
    if 'โอน' in document_text[:500]:
        metadata['category_level1'] = 'การโอน'
    elif 'จำนอง' in document_text[:500]:
        metadata['category_level1'] = 'ภาระผูกพัน'
    elif 'เช่า' in document_text[:500]:
        metadata['category_level1'] = 'ภาระผูกพัน'
    elif 'อายัด' in document_text[:500]:
        metadata['category_level1'] = 'อื่นๆ'
    elif 'ระเบียบ' in document_text[:200]:
        metadata['category_level1'] = 'ระเบียบ'
    
    return metadata
```

---

## 🔍 5. Search & Retrieval Strategy

### 5.1 Query Expansion (ภาษาไทย)

```python
QUERY_EXPANSION_RULES = {
    # Synonym expansion
    "synonyms": {
        "โอน": ["ขาย", "โอนกรรมสิทธิ์", "transfer", "ซื้อขาย", "จดทะเบียนโอน"],
        "ที่ดิน": ["โฉนด", "อสังหาริมทรัพย์", "land", "property", "แปลงที่ดิน"],
        "ห้องชุด": ["คอนโด", "condominium", "condo", "อาคารชุด"],
        "เอกสาร": ["หลักฐาน", "documents", "เอกสารประกอบ"],
        "ค่าธรรมเนียม": ["ค่าใช้จ่าย", "fees", "ภาษี", "tax", "ค่าบริการ"],
        "ขั้นตอน": ["กระบวนการ", "วิธีการ", "procedure", "steps"],
        "ระยะเวลา": ["เวลา", "duration", "ใช้เวลา"],
        "คนต่างด้าว": ["foreigner", "ชาวต่างชาติ", "ต่างด้าว"],
        "จำนอง": ["mortgage", "จด จำนอง", "จดจำนอง"]
    },
    
    # Colloquial to formal
    "formal_mapping": {
        "ซื้อบ้าน": "จดทะเบียนโอนอสังหาริมทรัพย์",
        "ซื้อที่ดิน": "จดทะเบียนโอนที่ดิน",
        "ขายบ้าน": "จดทะเบียนโอนอสังหาริมทรัพย์",
        "กู้บ้าน": "จดทะเบียนจำนอง",
        "จดทะเบียนบ้าน": "จดทะเบียนโอนอสังหาริมทรัพย์",
        "เปลี่ยนชื่อ": "แก้คำนำหน้านาม ชื่อตัว ชื่อสกุล"
    },
    
    # Common questions
    "question_templates": {
        "ต้องใช้เอกสารอะไรบ้าง": ["required_documents", "documents"],
        "ใช้เวลานานแค่ไหน": ["processing_time", "duration"],
        "ค่าใช้จ่ายเท่าไหร่": ["fees", "cost"],
        "มีขั้นตอนอย่างไร": ["steps", "procedure"],
        "ต่างด้าวทำได้ไหม": ["foreigner", "restrictions", "eligibility"]
    }
}
```

### 5.2 Hybrid Search Implementation

```python
def hybrid_search(query, top_k=10, filters=None):
    """
    Hybrid search: Dense + Sparse + Filters
    """
    
    # Step 1: Query preprocessing
    expanded_query = expand_query(query)
    formal_query = colloquial_to_formal(query)
    
    # Step 2: Dense retrieval (semantic)
    dense_results = vector_search(
        query_embedding=embed(expanded_query),
        top_k=top_k * 3,
        filters=filters
    )
    
    # Step 3: Sparse retrieval (BM25)
    tokens = tokenize_thai(expanded_query)
    sparse_results = bm25_search(
        query_tokens=tokens,
        top_k=top_k * 3,
        filters=filters
    )
    
    # Step 4: Metadata filter search
    if detect_specific_intent(query):
        metadata_results = metadata_search(
            query=query,
            top_k=top_k,
            filters=extract_filters_from_query(query)
        )
    else:
        metadata_results = []
    
    # Step 5: Reciprocal Rank Fusion
    combined = rrf_fusion(
        [dense_results, sparse_results, metadata_results],
        k=60
    )
    
    # Step 6: Reranking
    reranked = cross_encoder_rerank(
        query=formal_query,
        candidates=combined[:top_k * 2],
        top_k=top_k
    )
    
    # Step 7: Diversification
    final_results = diversify_results(
        reranked,
        diversity_factor=0.3
    )
    
    return final_results


def extract_filters_from_query(query):
    """
    Extract metadata filters from query
    """
    filters = {}
    
    # Document type
    if any(word in query for word in ['คู่มือ', 'วิธีการ']):
        filters['document_type'] = 'คู่มือปชช'
    elif any(word in query for word in ['ระเบียบ', 'กฎหมาย']):
        filters['document_type'] = 'ระเบียบกรม'
    
    # Category
    if any(word in query for word in ['โอน', 'ขาย', 'ซื้อ']):
        filters['category_level1'] = 'การโอน'
    elif 'จำนอง' in query:
        filters['category_level1'] = 'ภาระผูกพัน'
    
    # Special requirements
    if 'คนต่างด้าว' in query or 'ต่างด้าว' in query:
        filters['special_cases'] = 'คนต่างด้าว'
    
    if 'e-QLands' in query or 'จองคิว' in query:
        filters['has_e_qlands'] = True
    
    # Time filter
    if any(word in query for word in ['เร็ว', 'ด่วน', 'ไว']):
        filters['sort_by'] = 'processing_time_asc'
    
    return filters
```

---

## 🎨 6. Special Handling

### 6.1 Foreign Language Documents

```python
# เอกสารที่ต้องแปลเป็นภาษาไทย
foreign_doc_rules = {
    "detection": "ถ้าเป็นภาษาต่างประเทศต้องแปลเป็นภาษาไทย",
    "accepted_translators": [
        "ผู้จบปริญญาตรีในหลักสูตรที่ใช้ภาษานั้น",
        "อาจารย์ผู้สอนภาษานั้น",
        "สถานทูต/สถานกงสุลที่ใช้ภาษานั้นเป็นภาษาราชการ",
        "สถานทูต/สถานกงสุลไทยในต่างประเทศ"
    ],
    "metadata_tag": "requires_translation"
}
```

### 6.2 E-Service Special Sections

```python
e_service_sections = {
    "e_QLands": {
        "time_saved": 90,  # minutes
        "platforms": ["Android", "iOS"],
        "process": "จองคิวล่วงหน้า",
        "chunk_type": "special_procedure"
    },
    "e_Service": {
        "url": "https://eservice.dol.go.th",
        "services": [
            "ขอหนังสือรับรองราคาประเมินทุนทรัพย์",
            "ขอตรวจสอบหลักทรัพย์",
            "ขอสำเนาภาพลักษณ์เอกสารสิทธิ"
        ],
        "payment": ["Mobile Banking", "ATM QR code"],
        "chunk_type": "special_procedure"
    }
}
```

---

## 📊 7. Quality Metrics

```python
QUALITY_METRICS = {
    "chunk_quality": {
        "min_tokens": 200,
        "max_tokens": 1000,
        "target_tokens": 600,
        "overlap_percentage": 0.15,
        
        "table_max_tokens": 1500,
        "list_max_tokens": 1200,
        "legal_max_tokens": 800
    },
    
    "metadata_completeness": {
        "required_fields": [
            "document_type",
            "category_level1",
            "title",
            "processing_time" # อย่างน้อย 1 ใน 2 (minutes/days)
        ],
        "recommended_fields": [
            "fees",
            "required_documents_count",
            "legal_references"
        ]
    },
    
    "coverage": {
        "all_sections_covered": True,
        "no_content_loss": True,
        "preserve_tables": True,
        "preserve_lists": True
    }
}
```

---

## ✅ คำแนะนำสำหรับ Implementation

### Phase 1: Basic (Week 1-2)
1. ✅ Implement basic section-based chunking
2. ✅ Extract essential metadata (title, type, category)
3. ✅ Handle standard tables
4. ✅ Test with 10 documents

### Phase 2: Enhanced (Week 3-4)
5. ✅ Add comprehensive metadata extraction
6. ✅ Implement all chunking rules
7. ✅ Handle special sections
8. ✅ Test with all 108 documents

### Phase 3: Advanced (Week 5-6)
9. ✅ Implement hybrid search
10. ✅ Add query expansion
11. ✅ Implement reranking
12. ✅ Optimize performance

### Phase 4: Production (Week 7-8)
13. ✅ Full quality assurance
14. ✅ Performance tuning
15. ✅ Documentation
16. ✅ Deployment

---

**สรุป:** Schema นี้ครอบคลุมทุกรูปแบบและทุกสไตล์ที่พบในเอกสารจริง 100%
- ✅ คู่มือปชช (40 ไฟล์)
- ✅ คู่มือเจ้าหน้าที่ (55 ไฟล์) 
- ✅ ระเบียบกรม (15 ไฟล์)
- ✅ ตาราง HTML ทุกรูปแบบ
- ✅ รายการยาว 22 items
- ✅ กฎหมายแบบมีมาตรา/ข้อ
- ✅ Special sections (e-QLands, คนต่างด้าว)
