"""
Metadata Extractor for Land Department Documents

Extracts comprehensive metadata from Thai documents according to schema_design_v2_comprehensive.md
"""
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract metadata from Land Department documents"""
    
    def __init__(self):
        """Initialize extractor with patterns"""
        self.setup_patterns()
    
    def setup_patterns(self):
        """Setup regex patterns for extraction"""
        # Title patterns
        self.title_patterns = [
            r'คู่มือสำหรับประชาชน\s*:\s*(.+?)(?:\n|$)',
            r'ระเบียบกรมที่ดิน\s*\n\s*ว่าด้วย(.+?)(?:\n|พ\.ศ\.)',
            r'การจดทะเบียน(.+?)(?:\n|$)',
        ]
        
        # Organization pattern
        self.org_pattern = r'หน่วยงานที่ให้บริการ\s*:\s*(.+?)(?:\n|$)'
        
        # Time patterns
        self.time_patterns = {
            'minutes': r'(\d+)\s*นาที',
            'days': r'(\d+)\s*วัน',
        }
        
        # Fee patterns
        self.fee_patterns = {
            'baht': r'(\d+(?:\.\d+)?)\s*บาท',
            'percent': r'(\d+(?:\.\d+)?)\s*%',
            'percent_thai': r'ร้อยละ\s*(\d+(?:\.\d+)?)',
        }
        
        # Legal reference patterns
        self.legal_patterns = {
            'law': r'พ(?:ระ)?\.?ร(?:าช)?\.?บ(?:ัญญัติ)?\.?\s*([^\n]+?)(?:\s+พ\.ศ\.\s*(\d{4}))?',
            'ministerial': r'กฎกระทรวง(?:ฉบับที่\s*(\d+))?\s*\(พ\.ศ\.\s*(\d{4})\)',
            'section': r'มาตรา\s*(\d+(?:\s+ทวิ)?)',
            'article': r'ข้อ\s*(\d+)',
            'order': r'คำสั่ง(?:กระทรวง)?(?:ที่)?\s*(\d+(?:/\d+)?)',
        }
    
    def extract_metadata(self, text: str, file_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from document
        
        Args:
            text: Document text content
            file_path: Path to the document file
            
        Returns:
            Dictionary of extracted metadata
        """
        metadata = {
            'file_info': self._extract_file_info(text, file_path),
            'document_type': self._extract_document_type(text, file_path),
            'title': self._extract_title(text),
            'organization': self._extract_organization(text),
            'version_info': self._extract_version_info(text, file_path),
            'categories': self._extract_categories(text),
            'service': self._extract_service_info(text),
            'legal_references': self._extract_legal_references(text),
            'fees': self._extract_fees(text),
            'required_documents': self._extract_required_documents(text),
            'content_features': self._extract_content_features(text),
            'search_optimization': self._extract_search_keywords(text),
        }
        
        return metadata
    
    def _extract_file_info(self, text: str, file_path: str) -> Dict[str, Any]:
        """Extract file information"""
        path = Path(file_path)
        lines = text.split('\n')
        
        return {
            'file_path': str(path),
            'file_name': path.name,
            'file_size_kb': round(path.stat().st_size / 1024, 2) if path.exists() else 0,
            'line_count': len(lines),
            'word_count': len(text.split()),
            'char_count': len(text),
        }
    
    def _extract_document_type(self, text: str, file_path: str) -> str:
        """Extract document type"""
        first_500 = text[:500]
        
        if 'คู่มือสำหรับประชาชน' in first_500:
            return 'คู่มือปชช'
        elif 'ระเบียบกรมที่ดิน' in first_500:
            return 'ระเบียบกรม'
        elif 'การจดทะเบียน' in first_500:
            return 'คู่มือเจ้าหน้าที่'
        elif 'พระราชบัญญัติ' in first_500:
            return 'กฎหมาย'
        else:
            return 'อื่นๆ'
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Extract document title"""
        for pattern in self.title_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                title = match.group(1).strip()
                # Clean up
                title = re.sub(r'\s+', ' ', title)
                return title
        
        # Fallback: use first line
        first_line = text.split('\n')[0].strip()
        return first_line if first_line else None
    
    def _extract_organization(self, text: str) -> Dict[str, Any]:
        """Extract organization info"""
        match = re.search(self.org_pattern, text)
        org_name = match.group(1).strip() if match else "กรมที่ดิน"
        
        return {
            'primary': 'กรมที่ดิน',
            'full': org_name,
            'service_location': self._extract_service_locations(text),
        }
    
    def _extract_service_locations(self, text: str) -> List[str]:
        """Extract service locations"""
        locations = []
        location_keywords = [
            'สำนักงานที่ดินกรุงเทพมหานคร',
            'สำนักงานที่ดินจังหวัด',
            'สาขา',
            'ส่วนแยก',
        ]
        
        for keyword in location_keywords:
            if keyword in text:
                locations.append(keyword)
        
        return locations if locations else ['สำนักงานที่ดิน']
    
    def _extract_version_info(self, text: str, file_path: str) -> Dict[str, Any]:
        """Extract version information"""
        # Check for (N) marker
        is_new = '(N)' in file_path or '(N)' in text
        
        # Extract year
        year_match = re.search(r'พ\.ศ\.\s*(\d{4})', text)
        law_year = year_match.group(1) if year_match else None
        
        return {
            'version': 'N' if is_new else '',
            'is_latest': is_new,
            'law_year': law_year,
        }
    
    def _extract_categories(self, text: str) -> Dict[str, Any]:
        """Extract category information"""
        first_500 = text[:500]
        
        # Determine level1 category
        level1 = None
        if any(word in first_500 for word in ['โอน', 'ขาย', 'ซื้อ']):
            level1 = 'การโอน'
        elif 'จำนอง' in first_500:
            level1 = 'ภาระผูกพัน'
        elif 'เช่า' in first_500:
            level1 = 'ภาระผูกพัน'
        elif 'อายัด' in first_500:
            level1 = 'อื่นๆ'
        elif 'ระเบียบ' in first_500:
            level1 = 'ระเบียบ'
        
        # Extract service category
        service_category = None
        if 'จดทะเบียน' in first_500:
            service_category = 'จดทะเบียน'
        elif 'อนุมัติ' in first_500:
            service_category = 'อนุมัติ'
        
        # Extract tags
        tags = self._extract_tags(text)
        
        return {
            'level1': level1,
            'level2': None,  # Will be enhanced later
            'level3': None,
            'tags': tags,
            'service_category': service_category,
        }
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags"""
        tags = []
        
        keywords = {
            'โอน': ['โอน', 'ขาย', 'transfer'],
            'ที่ดิน': ['ที่ดิน', 'โฉนด'],
            'ห้องชุด': ['ห้องชุด', 'คอนโด'],
            'จำนอง': ['จำนอง'],
            'เช่า': ['เช่า'],
            'คนต่างด้าว': ['คนต่างด้าว', 'ต่างด้าว'],
            'e-QLands': ['e-QLands', 'จองคิว'],
        }
        
        for tag, patterns in keywords.items():
            if any(pattern in text for pattern in patterns):
                tags.append(tag)
        
        return tags
    
    def _extract_service_info(self, text: str) -> Dict[str, Any]:
        """Extract service information"""
        return {
            'processing': self._extract_processing_time(text),
            'requirements': self._extract_requirements(text),
            'channels': self._extract_service_channels(text),
        }
    
    def _extract_processing_time(self, text: str) -> Dict[str, Any]:
        """Extract processing time"""
        # Extract all time mentions in minutes
        minutes = []
        for match in re.finditer(self.time_patterns['minutes'], text):
            minutes.append(int(match.group(1)))
        
        # Extract days
        days = []
        for match in re.finditer(self.time_patterns['days'], text):
            days.append(int(match.group(1)))
        
        processing = {}
        
        if minutes:
            processing['standard'] = {
                'time_minutes': min(minutes),
                'time_display': f"{min(minutes)} นาที",
                'time_unit': 'นาที',
            }
        
        if days:
            processing['standard'] = processing.get('standard', {})
            processing['standard']['time_days'] = min(days)
        
        # Check for e-QLands
        if 'e-QLands' in text or 'e-Qlands' in text:
            # Try to find e-QLands specific time
            eqlands_match = re.search(r'e-QLands.*?(\d+)\s*นาที', text, re.IGNORECASE | re.DOTALL)
            if eqlands_match:
                processing['alternative'] = {
                    'method': 'e-QLands',
                    'time_minutes': int(eqlands_match.group(1)),
                    'time_display': f"{eqlands_match.group(1)} นาที (จองคิวล่วงหน้า)",
                }
        
        return processing
    
    def _extract_requirements(self, text: str) -> Dict[str, Any]:
        """Extract requirements"""
        return {
            'requires_announcement': 'ต้องประกาศ' in text,
            'requires_court_order': 'คำสั่งศาล' in text or 'คำพิพากษา' in text,
            'requires_consent': 'ยินยอม' in text and 'คู่สมรส' in text,
        }
    
    def _extract_service_channels(self, text: str) -> List[Dict[str, Any]]:
        """Extract service channels"""
        channels = []
        
        if 'e-QLands' in text or 'e-Qlands' in text:
            channels.append({
                'type': 'online',
                'name': 'e-QLands',
                'available': True,
            })
        
        if 'e-Service' in text or 'e-service' in text:
            channels.append({
                'type': 'e-service',
                'name': 'สำนักงานที่ดินอิเล็กทรอนิกส์',
                'available': True,
            })
        
        # Default walk-in
        channels.append({
            'type': 'walk-in',
            'name': 'ติดต่อด้วยตนเอง ณ หน่วยงาน',
            'available': True,
        })
        
        return channels
    
    def _extract_legal_references(self, text: str) -> List[Dict[str, Any]]:
        """Extract legal references"""
        references = []
        
        # พ.ร.บ.
        for match in re.finditer(self.legal_patterns['law'], text):
            references.append({
                'type': 'พ.ร.บ.',
                'name': match.group(1).strip(),
                'year': match.group(2) if match.lastindex >= 2 else None,
            })
        
        # กฎกระทรวง
        for match in re.finditer(self.legal_patterns['ministerial'], text):
            references.append({
                'type': 'กฎกระทรวง',
                'number': match.group(1),
                'year': match.group(2),
            })
        
        # มาตรา
        sections = set()
        for match in re.finditer(self.legal_patterns['section'], text):
            section = match.group(1).strip()
            if section not in sections:
                sections.add(section)
                references.append({
                    'type': 'มาตรา',
                    'section': section,
                })
        
        # คำสั่ง
        for match in re.finditer(self.legal_patterns['order'], text):
            references.append({
                'type': 'คำสั่ง',
                'number': match.group(1),
            })
        
        return references
    
    def _extract_fees(self, text: str) -> Dict[str, Any]:
        """Extract fee information"""
        fees = []
        
        # Baht fees
        for match in re.finditer(self.fee_patterns['baht'], text):
            fees.append({
                'amount': float(match.group(1)),
                'unit': 'บาท',
                'type': 'fixed',
            })
        
        # Percentage fees
        for match in re.finditer(self.fee_patterns['percent'], text):
            fees.append({
                'amount': float(match.group(1)),
                'unit': '%',
                'type': 'percentage',
            })
        
        # Thai percentage
        for match in re.finditer(self.fee_patterns['percent_thai'], text):
            fees.append({
                'amount': float(match.group(1)),
                'unit': '%',
                'type': 'percentage',
            })
        
        # Remove duplicates
        unique_fees = []
        seen = set()
        for fee in fees:
            key = (fee['amount'], fee['unit'])
            if key not in seen:
                seen.add(key)
                unique_fees.append(fee)
        
        return {
            'all_fees': unique_fees,
            'has_fees': len(unique_fees) > 0,
        }
    
    def _extract_required_documents(self, text: str) -> Dict[str, Any]:
        """Extract required documents count"""
        # Look for document list section
        doc_match = re.search(
            r'รายการเอกสาร\s+หลักฐานประกอบ(.*?)(?:ค่าธรรมเนียม|แบบฟอร์ม|$)',
            text,
            re.DOTALL
        )
        
        if doc_match:
            doc_section = doc_match.group(1)
            # Count numbered items
            doc_count = len(re.findall(r'^\d+\)', doc_section, re.MULTILINE))
            return {
                'count': doc_count,
                'has_documents': doc_count > 0,
            }
        
        return {
            'count': 0,
            'has_documents': False,
        }
    
    def _extract_content_features(self, text: str) -> Dict[str, Any]:
        """Extract content features"""
        return {
            'has_tables': '|' in text and '---' in text,
            'has_lists': bool(re.search(r'^\d+\.', text, re.MULTILINE)),
            'has_legal_references': 'พ.ร.บ.' in text or 'มาตรา' in text,
            'has_e_qlands': 'e-QLands' in text or 'e-Qlands' in text,
            'has_e_service': 'e-Service' in text or 'e-service' in text,
        }
    
    def _extract_search_keywords(self, text: str) -> Dict[str, Any]:
        """Extract keywords for search optimization"""
        # Primary keywords from title and first 500 chars
        first_500 = text[:500]
        
        keywords = []
        
        # Common keywords
        keyword_list = [
            'โอน', 'ขาย', 'ที่ดิน', 'ห้องชุด', 'จำนอง', 'เช่า',
            'อสังหาริมทรัพย์', 'จดทะเบียน', 'คนต่างด้าว',
            'ค่าธรรมเนียม', 'เอกสาร', 'ขั้นตอน'
        ]
        
        for kw in keyword_list:
            if kw in first_500:
                keywords.append(kw)
        
        return {
            'primary_keywords': keywords,
        }


if __name__ == "__main__":
    # Test the extractor
    import sys
    sys.path.insert(0, '/Users/pond500/RAG/rag_dol')
    
    logging.basicConfig(level=logging.INFO)
    
    # Test with a sample document
    test_file = Path("/Users/pond500/RAG/rag_dol/data/คู่มือปชช.รายละเอียดเนื้อหา/1.จดทะเบียนประเภทโอนอสังหาริมทรัพย์กรณีไม่ต้องประกาศ (N).txt")
    
    if test_file.exists():
        with open(test_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        extractor = MetadataExtractor()
        metadata = extractor.extract_metadata(text, str(test_file))
        
        print("\n📊 Extracted Metadata:")
        print(f"Document Type: {metadata['document_type']}")
        print(f"Title: {metadata['title']}")
        print(f"Categories: {metadata['categories']}")
        print(f"Processing Time: {metadata['service']['processing']}")
        print(f"Legal References: {len(metadata['legal_references'])} found")
        print(f"Fees: {len(metadata['fees']['all_fees'])} found")
        print(f"Features: {metadata['content_features']}")
    else:
        print(f"Test file not found: {test_file}")
