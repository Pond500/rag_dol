"""
Interactive Chat Interface for Land Department RAG

Provides conversational interface with:
- Chat history
- Context management
- Configuration options
"""
import sys
sys.path.insert(0, '/Users/pond500/RAG/rag_dol')

import logging
from typing import List, Dict
from datetime import datetime

from rag_system.rag_engine import LandDepartmentRAG, RAGResponse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class ChatInterface:
    """Interactive chat interface for RAG system"""
    
    def __init__(self):
        """Initialize chat interface"""
        print("\n" + "=" * 80)
        print("🏛️  ระบบตอบคำถามอัตโนมัติ - กรมที่ดิน")
        print("=" * 80)
        print("\nกำลังโหลดระบบ...")
        
        self.rag = LandDepartmentRAG()
        self.chat_history: List[Dict] = []
        
        # Default configuration
        self.config = {
            'top_k': 3,
            'enable_reranker': True,
            'enable_context_expansion': True,
            'alpha': 0.5,
            'use_llm': False,  # Set to True when LLM integrated
        }
        
        print("\n✅ ระบบพร้อมใช้งาน!")
        self._show_help()
    
    def _show_help(self):
        """Show help message"""
        print("\n" + "=" * 80)
        print("📖 คำสั่งที่ใช้ได้:")
        print("=" * 80)
        print("  /help     - แสดงคำสั่งทั้งหมด")
        print("  /config   - แสดง/เปลี่ยนการตั้งค่า")
        print("  /history  - แสดงประวัติการสนทนา (จาก Memory)")
        print("  /clear    - ล้างประวัติ (Memory)")
        print("  /stats    - แสดงสถิติ Memory")
        print("  /quit     - ออกจากโปรแกรม")
        print("  [คำถาม]  - ถามคำถามโดยตรง (รองรับ multi-turn)")
        print("=" * 80)
        
        if self.rag.memory is not None:
            print(f"\n💬 Memory Status: {len(self.rag.memory)} messages in buffer")
            print(f"   (รองรับการสนทนาต่อเนื่อง - context จาก 3 turns ล่าสุด)")
    
    def _show_stats(self):
        """Show memory statistics"""
        if self.rag.memory is None:
            print("\n❌ Memory ไม่ได้เปิดใช้งาน")
            return
        
        print("\n" + "=" * 80)
        print("📊 Memory Statistics")
        print("=" * 80)
        
        stats = self.rag.memory.get_statistics()
        print(f"  Conversation ID:     {stats['conversation_id']}")
        print(f"  Total Messages:      {stats['total_messages']}")
        print(f"  User Messages:       {stats['user_messages']}")
        print(f"  Assistant Messages:  {stats['assistant_messages']}")
        print(f"  Total Turns:         {stats['total_turns']}")
        print(f"  Duration:            {stats['duration_seconds']:.1f}s")
        print(f"  Buffer Utilization:  {stats['buffer_utilization']}")
        print("=" * 80)
        
        # Show recent context
        recent_context = self.rag.memory.get_context_window(max_turns=2)
        if recent_context:
            print("\n📝 Recent Context (2 turns):")
            print("-" * 80)
            print(recent_context[:300] + "..." if len(recent_context) > 300 else recent_context)
            print("-" * 80)
    
    def _show_config(self):
        """Show current configuration"""
        print("\n⚙️  การตั้งค่าปัจจุบัน:")
        print("-" * 80)
        for key, value in self.config.items():
            print(f"  {key}: {value}")
        print("-" * 80)
    
    def _update_config(self):
        """Interactive configuration update"""
        print("\n🔧 ปรับการตั้งค่า (กด Enter เพื่อข้าม)")
        print("-" * 80)
        
        try:
            # Top-k
            new_top_k = input(f"top_k ({self.config['top_k']}): ").strip()
            if new_top_k:
                self.config['top_k'] = int(new_top_k)
            
            # Reranker
            new_reranker = input(f"enable_reranker ({self.config['enable_reranker']}) [y/n]: ").strip().lower()
            if new_reranker:
                self.config['enable_reranker'] = new_reranker in ['y', 'yes', 'true', '1']
            
            # Context expansion
            new_context = input(f"enable_context_expansion ({self.config['enable_context_expansion']}) [y/n]: ").strip().lower()
            if new_context:
                self.config['enable_context_expansion'] = new_context in ['y', 'yes', 'true', '1']
            
            # Alpha
            new_alpha = input(f"alpha ({self.config['alpha']}) [0.0-1.0]: ").strip()
            if new_alpha:
                self.config['alpha'] = float(new_alpha)
            
            print("\n✅ การตั้งค่าได้รับการอัปเดตแล้ว")
            self._show_config()
            
        except ValueError as e:
            print(f"\n❌ ค่าไม่ถูกต้อง: {e}")
    
    def _show_history(self):
        """Show chat history from memory"""
        if not self.rag.memory or len(self.rag.memory) == 0:
            print("\n📝 ยังไม่มีประวัติการสนทนา")
            return
        
        # Use memory's format_history method
        print(self.rag.memory.format_history())
        
        # Show statistics
        stats = self.rag.memory.get_statistics()
        print("\n📊 สถิติการสนทนา:")
        print(f"  - จำนวนข้อความทั้งหมด: {stats['total_messages']}")
        print(f"  - คำถาม: {stats['user_messages']}")
        print(f"  - คำตอบ: {stats['assistant_messages']}")
        print(f"  - ระยะเวลา: {stats['duration_seconds']:.1f} วินาที")
    
    def _clear_history(self):
        """Clear chat history and memory"""
        if self.rag.memory is not None:
            self.rag.memory.clear()
        self.chat_history.clear()
        print("\n✅ ล้างประวัติเรียบร้อยแล้ว")
    
    def _process_query(self, query: str):
        """Process user query"""
        print("\n🔍 กำลังค้นหา...")
        
        # Query RAG system
        response = self.rag.query(
            query=query,
            **self.config
        )
        
        # Display response
        print(self.rag.format_response(
            response,
            include_chunks=True,
            include_sources=True,
        ))
        
        # Save to history
        self.chat_history.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'query': query,
            'answer': response.answer[:500],  # Truncate
            'score': response.metadata['top_score'],
            'num_sources': len(response.sources),
        })
    
    def run(self):
        """Run interactive chat loop"""
        while True:
            try:
                # Get user input
                print("\n" + "=" * 80)
                user_input = input("💬 คุณ: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    command = user_input[1:].lower()
                    
                    if command == 'help':
                        self._show_help()
                    elif command == 'config':
                        self._show_config()
                        if input("\nต้องการเปลี่ยน? (y/n): ").lower() == 'y':
                            self._update_config()
                    elif command == 'history':
                        self._show_history()
                    elif command == 'stats':
                        self._show_stats()
                    elif command == 'clear':
                        self._clear_history()
                    elif command == 'quit':
                        print("\n👋 ขอบคุณที่ใช้บริการ")
                        break
                    else:
                        print(f"\n❌ ไม่รู้จักคำสั่ง: {command}")
                        print("💡 พิมพ์ /help เพื่อดูคำสั่งที่ใช้ได้")
                    
                    continue
                
                # Process query
                self._process_query(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 ขอบคุณที่ใช้บริการ")
                break
            except Exception as e:
                print(f"\n❌ เกิดข้อผิดพลาด: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    chat = ChatInterface()
    chat.run()
