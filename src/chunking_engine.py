"""
Chunking Engine for Land Department Documents

Implements 7 chunking rules from schema_design_v2_comprehensive.md
"""
import re
import tiktoken
import uuid
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a document chunk with hierarchical relationships"""
    text: str
    chunk_type: str
    chunk_index: int
    start_line: int
    end_line: int
    section_title: Optional[str] = None
    importance_score: float = 0.5
    metadata: Dict[str, Any] = None
    
    # Hierarchical relationships (PageIndex-style)
    parent_chunk_id: Optional[str] = None  # ID of parent chunk
    child_chunk_ids: List[str] = None  # IDs of child chunks
    hierarchy_level: int = 0  # 0=document, 1=section, 2=subsection, 3=paragraph
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.child_chunk_ids is None:
            self.child_chunk_ids = []
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert chunk to Qdrant payload format"""
        return {
            "text": self.text,
            "chunk_type": self.chunk_type,
            "chunk_index": self.chunk_index,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "section_title": self.section_title,
            "importance_score": self.importance_score,
            "parent_chunk_id": self.parent_chunk_id,
            "child_chunk_ids": self.child_chunk_ids,
            "hierarchy_level": self.hierarchy_level,
            **self.metadata  # Spread metadata fields
        }


class ChunkingEngine:
    """
    Chunking engine implementing 7 rules from v2 schema:
    1. Section-based chunking
    2. Table preservation
    3. List handling
    4. Legal article handling
    5. Special section handling
    6. Numbered criteria
    7. Long document list grouping
    """
    
    def __init__(
        self,
        min_tokens: int = 200,
        max_tokens: int = 1000,
        target_tokens: int = 600,
        overlap_tokens: int = 100,
    ):
        """Initialize chunking engine"""
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        
        # Special limits
        self.table_max_tokens = 1500
        self.list_max_tokens = 1200
        self.legal_max_tokens = 800
        
        # Initialize tokenizer
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Setup patterns
        self.setup_patterns()
        
        logger.info(f"ChunkingEngine initialized: {min_tokens}-{max_tokens} tokens, target={target_tokens}")
    
    def setup_patterns(self):
        """Setup regex patterns for chunking"""
        # Section headers
        self.section_patterns = [
            r'^หลักเกณฑ์',
            r'^ช่องทางการให้บริการ',
            r'^ขั้นตอน',
            r'^รายการเอกสาร',
            r'^ค่าธรรมเนียม',
            r'^ช่องทางการร้องเรียน',
            r'^\*\*\*\s+กรณี',
            r'^หมวด\s+\d+',
            r'^ส่วนที่\s+\d+',
            r'^แบบฟอร์ม',
            r'^กฎหมายที่เกี่ยวข้อง',
        ]
        
        # Table markers
        self.table_start_pattern = r'\|\s+\|'
        self.table_row_pattern = r'\|.*\|'
        
        # List patterns
        self.list_patterns = {
            'numbered': r'^\d+\.',
            'lettered': r'^\([ก-ฮ]\)',
            'sub_numbered': r'^\(\d+\)',
        }
        
        # Legal patterns
        self.legal_patterns = {
            'article': r'^ข้อ\s+\d+',
            'section': r'^มาตรา\s+\d+',
            'chapter': r'^หมวด\s+\d+',
        }
        
        # Special markers
        self.special_markers = [
            r'^\*\*\*',
            r'^หมายเหตุ',
            r'^ทั้งนี้',
            r'^เว้นแต่',
        ]
        
        # Sentence endings for Thai text
        self.sentence_endings = [
            '.',
            '!',
            '?',
            '๏',
            '\n\n',
        ]
    
    def _split_by_sentence_boundary(self, text: str, max_tokens: int) -> List[str]:
        """
        Split text at sentence boundaries to avoid mid-sentence cuts
        
        Args:
            text: Text to split
            max_tokens: Maximum tokens per chunk
            
        Returns:
            List of text chunks
        """
        sentences = []
        current = []
        
        # Split by sentence endings
        for char in text:
            current.append(char)
            if char in self.sentence_endings:
                sentences.append(''.join(current))
                current = []
        
        if current:
            sentences.append(''.join(current))
        
        # Group sentences into chunks
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            if current_tokens + sentence_tokens > max_tokens and current_chunk:
                # Start new chunk
                chunks.append(''.join(current_chunk))
                
                # Add overlap (last 2 sentences)
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_tokens = self.count_tokens(''.join(current_chunk))
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        if current_chunk:
            chunks.append(''.join(current_chunk))
        
        return chunks
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))
    
    def chunk_document(
        self,
        text: str,
        document_type: str,
        document_id: str,
    ) -> List[Chunk]:
        """
        Main chunking method - applies all 7 rules + hierarchical structure
        
        Args:
            text: Document text
            document_type: Type of document (คู่มือปชช, ระเบียบกรม, etc.)
            document_id: Document identifier
            
        Returns:
            List of chunks with parent-child relationships
        """
        logger.info(f"Chunking document {document_id} (type: {document_type})")
        
        lines = text.split('\n')
        chunks = []
        
        # Step 1: Create document-level chunk (Level 0 - root)
        doc_summary = self._create_document_summary(text, document_id, document_type)
        chunks.append(doc_summary)
        parent_doc_id = doc_summary.metadata['chunk_id']  # Use the generated UUID
        
        # Step 2: Identify sections
        sections = self._identify_sections(lines)
        logger.info(f"Found {len(sections)} sections")
        
        # Step 3: Process each section (Level 1)
        section_chunks = []
        for section_idx, section in enumerate(sections):
            # Generate UUID for section
            section_chunk_id = str(uuid.uuid4())
            
            # Create section-level chunk
            section_chunk = self._create_section_chunk(
                section,
                section_chunk_id,
                parent_doc_id,
                section_idx,
            )
            section_chunks.append(section_chunk)
            
            # Process subsections (Level 2+)
            subsection_chunks = self._process_section(
                section,
                document_type,
                section_chunk_id,  # Use the section's UUID as parent
            )
            
            # Generate UUIDs for subsection chunks and link to parent
            subsection_ids = []
            for i, chunk in enumerate(subsection_chunks):
                chunk_uuid = str(uuid.uuid4())
                chunk.parent_chunk_id = section_chunk_id
                chunk.metadata['chunk_id'] = chunk_uuid
                chunk.hierarchy_level = 2
                subsection_ids.append(chunk_uuid)
            
            # Link children to parent
            section_chunk.child_chunk_ids = subsection_ids
            
            section_chunks.extend(subsection_chunks)
        
        # Link sections to document (use actual section UUIDs)
        doc_summary.child_chunk_ids = [
            chunk.metadata['chunk_id'] for chunk in section_chunks 
            if chunk.hierarchy_level == 1
        ]
        
        chunks.extend(section_chunks)
        
        # Step 4: Add metadata and indices
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i
            chunk.metadata['document_id'] = document_id
            chunk.metadata['document_type'] = document_type
            chunk.metadata['total_chunks'] = len(chunks)
        
        # Step 5: Add cross-references (previous/next at same level)
        chunks = self._add_cross_references(chunks)
        
        logger.info(f"Created {len(chunks)} chunks with hierarchical structure")
        return chunks
    
    def _create_document_summary(
        self,
        text: str,
        document_id: str,
        document_type: str,
    ) -> Chunk:
        """Create document-level summary chunk (Level 0)"""
        # Extract first 500 characters as summary
        lines = text.split('\n')
        summary_lines = []
        char_count = 0
        
        for line in lines:
            if char_count > 500:
                break
            summary_lines.append(line)
            char_count += len(line)
        
        summary_text = '\n'.join(summary_lines)
        
        return Chunk(
            text=summary_text,
            chunk_type='document_summary',
            chunk_index=0,
            start_line=0,
            end_line=len(summary_lines),
            section_title=None,
            importance_score=1.0,
            metadata={
                'chunk_id': str(uuid.uuid4()),  # Generate UUID
                'is_summary': True,
                'document_id': document_id,  # Keep original doc ID for reference
            },
            parent_chunk_id=None,
            child_chunk_ids=[],
            hierarchy_level=0,
        )
    
    def _create_section_chunk(
        self,
        section: Dict[str, Any],
        section_id: str,
        parent_id: str,
        section_idx: int,
    ) -> Chunk:
        """Create section-level chunk (Level 1)"""
        section_text = '\n'.join(section['lines'][:20])  # First 20 lines as section summary
        
        return Chunk(
            text=section_text,
            chunk_type=f"section_{section['type']}",
            chunk_index=0,
            start_line=section['start_line'],
            end_line=min(section['start_line'] + 20, section['end_line']),
            section_title=section['title'],
            importance_score=0.9,
            metadata={
                'chunk_id': section_id,
                'section_index': section_idx,
                'is_section_summary': True,
            },
            parent_chunk_id=parent_id,
            child_chunk_ids=[],
            hierarchy_level=1,
        )
    
    def _identify_sections(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Identify sections in document (Rule 1: Section-based)"""
        sections = []
        current_section = {
            'title': None,
            'start_line': 0,
            'lines': [],
            'type': 'default',
        }
        
        for i, line in enumerate(lines):
            # Check if this is a section header
            is_header = False
            section_type = 'default'
            
            for pattern in self.section_patterns:
                if re.match(pattern, line.strip()):
                    is_header = True
                    # Determine section type
                    if 'หลักเกณฑ์' in line:
                        section_type = 'criteria'
                    elif 'ช่องทางการให้บริการ' in line:
                        section_type = 'channels'
                    elif 'ขั้นตอน' in line:
                        section_type = 'steps'
                    elif 'รายการเอกสาร' in line:
                        section_type = 'documents'
                    elif 'ค่าธรรมเนียม' in line:
                        section_type = 'fees'
                    elif 'ช่องทางการร้องเรียน' in line:
                        section_type = 'complaints'
                    elif '***' in line or 'กรณี' in line:
                        section_type = 'special'
                    elif 'หมวด' in line:
                        section_type = 'chapter'
                    elif 'แบบฟอร์ม' in line:
                        section_type = 'forms'
                    break
            
            if is_header and current_section['lines']:
                # Save previous section
                current_section['end_line'] = i - 1
                sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': line.strip(),
                    'start_line': i,
                    'lines': [line],
                    'type': section_type,
                }
            else:
                current_section['lines'].append(line)
        
        # Add last section
        if current_section['lines']:
            current_section['end_line'] = len(lines) - 1
            sections.append(current_section)
        
        return sections
    
    def _process_section(
        self,
        section: Dict[str, Any],
        document_type: str,
        parent_section_id: str = None,
    ) -> List[Chunk]:
        """Process a section and return chunks with parent reference"""
        section_text = '\n'.join(section['lines'])
        section_type = section['type']
        section_title = section['title']
        
        chunks = []
        
        # Check if this is a table section (Rule 2)
        if self._is_table_section(section_text):
            chunks = self._chunk_table(
                section_text,
                section_type,
                section_title,
                section['start_line'],
            )
        
        # Check if this is a list section (Rule 3)
        elif self._is_list_section(section_text):
            chunks = self._chunk_list(
                section_text,
                section_type,
                section_title,
                section['start_line'],
            )
        
        # Check if this is legal article section (Rule 4)
        elif document_type == 'ระเบียบกรม' and section_type in ['chapter', 'default']:
            chunks = self._chunk_legal_articles(
                section_text,
                section_title,
                section['start_line'],
            )
        
        # Check if this is special section (Rule 5)
        elif section_type == 'special':
            chunks = self._chunk_special_section(
                section_text,
                section_title,
                section['start_line'],
            )
        
        # Check if this is numbered criteria (Rule 6)
        elif section_type == 'criteria':
            chunks = self._chunk_criteria(
                section_text,
                section_title,
                section['start_line'],
            )
        
        # Check if this is long document list (Rule 7)
        elif section_type == 'documents':
            chunks = self._chunk_document_list(
                section_text,
                section_title,
                section['start_line'],
            )
        
        # Default: sliding window
        else:
            chunks = self._chunk_sliding_window(
                section_text,
                section_type,
                section_title,
                section['start_line'],
            )
        
        # Set hierarchy level for all chunks
        for chunk in chunks:
            chunk.hierarchy_level = 2  # Subsection level
            if parent_section_id:
                chunk.parent_chunk_id = parent_section_id
        
        return chunks
    
    def _is_table_section(self, text: str) -> bool:
        """Check if text contains a table"""
        return '|' in text and '---' in text
    
    def _is_list_section(self, text: str) -> bool:
        """Check if text contains a list"""
        # Check for numbered list
        numbered = len(re.findall(r'^\d+\.', text, re.MULTILINE)) >= 3
        return numbered
    
    def _chunk_table(
        self,
        text: str,
        section_type: str,
        section_title: Optional[str],
        start_line: int,
    ) -> List[Chunk]:
        """Rule 2: Table preservation"""
        lines = text.split('\n')
        chunks = []
        
        # Extract table
        table_lines = [line for line in lines if '|' in line]
        header = table_lines[0] if table_lines else ""
        rows = table_lines[2:] if len(table_lines) > 2 else []
        
        # Calculate tokens
        table_text = '\n'.join([header] + rows)
        tokens = self.count_tokens(table_text)
        
        if tokens <= self.table_max_tokens:
            # Keep entire table
            chunk = Chunk(
                text=table_text,
                chunk_type=f"{section_type}_table",
                chunk_index=0,
                start_line=start_line,
                end_line=start_line + len(lines) - 1,
                section_title=section_title,
                importance_score=0.9,
                metadata={
                    'has_table': True,
                    'row_count': len(rows),
                }
            )
            chunks.append(chunk)
        else:
            # Split table into groups
            group_size = 10
            for i in range(0, len(rows), group_size):
                group_rows = rows[i:i + group_size]
                group_text = '\n'.join([header, '| --- | --- |'] + group_rows)
                
                chunk = Chunk(
                    text=group_text,
                    chunk_type=f"{section_type}_table_part",
                    chunk_index=0,
                    start_line=start_line + i,
                    end_line=start_line + i + len(group_rows),
                    section_title=section_title,
                    importance_score=0.85,
                    metadata={
                        'has_table': True,
                        'is_partial': True,
                        'part_number': i // group_size + 1,
                    }
                )
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_list(
        self,
        text: str,
        section_type: str,
        section_title: Optional[str],
        start_line: int,
    ) -> List[Chunk]:
        """Rule 3: List handling"""
        lines = text.split('\n')
        chunks = []
        
        # Find list items
        list_items = []
        current_item = []
        
        for line in lines:
            if re.match(r'^\d+\.', line.strip()):
                if current_item:
                    list_items.append('\n'.join(current_item))
                current_item = [line]
            elif current_item:
                current_item.append(line)
        
        if current_item:
            list_items.append('\n'.join(current_item))
        
        # Group items
        if len(list_items) <= 5:
            # Keep all together
            chunk = Chunk(
                text=text,
                chunk_type=f"{section_type}_list",
                chunk_index=0,
                start_line=start_line,
                end_line=start_line + len(lines) - 1,
                section_title=section_title,
                importance_score=0.85,
                metadata={'has_list': True, 'list_items': len(list_items)}
            )
            chunks.append(chunk)
        else:
            # Split into groups of 5-7 items
            group_size = 6
            for i in range(0, len(list_items), group_size - 2):  # Overlap of 2
                group = list_items[i:i + group_size]
                group_text = '\n\n'.join(group)
                
                chunk = Chunk(
                    text=group_text,
                    chunk_type=f"{section_type}_list_part",
                    chunk_index=0,
                    start_line=start_line,
                    end_line=start_line + len(lines) - 1,
                    section_title=section_title,
                    importance_score=0.80,
                    metadata={
                        'has_list': True,
                        'list_items': len(group),
                        'part_number': i // (group_size - 2) + 1,
                    }
                )
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_legal_articles(
        self,
        text: str,
        section_title: Optional[str],
        start_line: int,
    ) -> List[Chunk]:
        """Rule 4: Legal article handling"""
        lines = text.split('\n')
        chunks = []
        
        # Find articles
        articles = []
        current_article = []
        
        for line in lines:
            if re.match(r'^ข้อ\s+\d+', line.strip()):
                if current_article:
                    articles.append('\n'.join(current_article))
                current_article = [line]
            elif current_article:
                current_article.append(line)
        
        if current_article:
            articles.append('\n'.join(current_article))
        
        # Create chunks (one per article)
        for i, article in enumerate(articles):
            tokens = self.count_tokens(article)
            
            if tokens <= self.legal_max_tokens:
                chunk = Chunk(
                    text=article,
                    chunk_type='legal_article',
                    chunk_index=0,
                    start_line=start_line,
                    end_line=start_line + len(article.split('\n')),
                    section_title=section_title,
                    importance_score=0.95,
                    metadata={'is_legal': True}
                )
                chunks.append(chunk)
            else:
                # Split long article
                sub_chunks = self._chunk_sliding_window(
                    article,
                    'legal_article_long',
                    section_title,
                    start_line,
                )
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _chunk_special_section(
        self,
        text: str,
        section_title: Optional[str],
        start_line: int,
    ) -> List[Chunk]:
        """Rule 5: Special section handling"""
        tokens = self.count_tokens(text)
        
        chunk = Chunk(
            text=text,
            chunk_type='special_procedure',
            chunk_index=0,
            start_line=start_line,
            end_line=start_line + len(text.split('\n')) - 1,
            section_title=section_title,
            importance_score=0.90,
            metadata={'is_special': True}
        )
        
        return [chunk]
    
    def _chunk_criteria(
        self,
        text: str,
        section_title: Optional[str],
        start_line: int,
    ) -> List[Chunk]:
        """Rule 6: Numbered criteria"""
        # Similar to list handling but with different importance
        return self._chunk_list(text, 'criteria', section_title, start_line)
    
    def _chunk_document_list(
        self,
        text: str,
        section_title: Optional[str],
        start_line: int,
    ) -> List[Chunk]:
        """Rule 7: Long document list grouping"""
        lines = text.split('\n')
        
        # Find document items
        doc_items = []
        current_doc = []
        
        for line in lines:
            if re.match(r'^\d+\)', line.strip()):
                if current_doc:
                    doc_items.append('\n'.join(current_doc))
                current_doc = [line]
            elif current_doc:
                current_doc.append(line)
        
        if current_doc:
            doc_items.append('\n'.join(current_doc))
        
        chunks = []
        
        if len(doc_items) > 10:
            # Group by category (mandatory, conditional, special)
            # Heuristic: first 5 = mandatory, next = conditional, last = special
            groups = {
                'mandatory': doc_items[:5],
                'conditional': doc_items[5:15] if len(doc_items) > 15 else doc_items[5:],
                'special': doc_items[15:] if len(doc_items) > 15 else [],
            }
            
            for group_name, items in groups.items():
                if not items:
                    continue
                
                group_text = '\n\n'.join(items)
                chunk = Chunk(
                    text=f"รายการเอกสาร ({group_name}):\n\n" + group_text,
                    chunk_type=f'documents_{group_name}',
                    chunk_index=0,
                    start_line=start_line,
                    end_line=start_line + len(lines) - 1,
                    section_title=section_title,
                    importance_score=0.95 if group_name == 'mandatory' else 0.85,
                    metadata={
                        'doc_group': group_name,
                        'doc_count': len(items),
                    }
                )
                chunks.append(chunk)
        else:
            # Keep all together
            chunk = Chunk(
                text=text,
                chunk_type='documents_complete',
                chunk_index=0,
                start_line=start_line,
                end_line=start_line + len(lines) - 1,
                section_title=section_title,
                importance_score=0.95,
                metadata={'doc_count': len(doc_items)}
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_sliding_window(
        self,
        text: str,
        chunk_type: str,
        section_title: Optional[str],
        start_line: int,
    ) -> List[Chunk]:
        """
        Default sliding window chunking with sentence-aware splitting
        
        Improved to avoid mid-sentence cuts
        """
        # Use sentence-aware splitting
        text_chunks = self._split_by_sentence_boundary(text, self.target_tokens)
        
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk = Chunk(
                text=chunk_text.strip(),
                chunk_type=chunk_type,
                chunk_index=i,
                start_line=start_line,
                end_line=start_line,  # Approximate
                section_title=section_title,
                importance_score=0.7,
            )
            chunks.append(chunk)
        
        return chunks
    
    def _add_cross_references(self, chunks: List[Chunk]) -> List[Chunk]:
        """Add previous/next chunk references"""
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk.metadata['previous_chunk_id'] = chunks[i-1].chunk_index
            if i < len(chunks) - 1:
                chunk.metadata['next_chunk_id'] = chunks[i+1].chunk_index
        
        return chunks


if __name__ == "__main__":
    # Test the chunking engine
    import sys
    sys.path.insert(0, '/Users/pond500/RAG/rag_dol')
    
    logging.basicConfig(level=logging.INFO)
    
    test_file = Path("/Users/pond500/RAG/rag_dol/data/คู่มือปชช.รายละเอียดเนื้อหา/1.จดทะเบียนประเภทโอนอสังหาริมทรัพย์กรณีไม่ต้องประกาศ (N).txt")
    
    if test_file.exists():
        with open(test_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        engine = ChunkingEngine()
        chunks = engine.chunk_document(text, 'คู่มือปชช', 'doc_001')
        
        print(f"\n📄 Created {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks[:5], 1):
            print(f"\nChunk {i}:")
            print(f"  Type: {chunk.chunk_type}")
            print(f"  Tokens: {engine.count_tokens(chunk.text)}")
            print(f"  Section: {chunk.section_title}")
            print(f"  Importance: {chunk.importance_score}")
            print(f"  Text preview: {chunk.text[:100]}...")
    else:
        print(f"Test file not found: {test_file}")
