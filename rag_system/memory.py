"""
Conversation Memory Management for RAG System

Implements ConversationBufferMemory for multi-turn conversations:
- Stores conversation history
- Manages context window
- Provides relevant history for RAG context
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Single message in conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        time_str = self.timestamp.strftime("%H:%M:%S")
        role_emoji = "👤" if self.role == "user" else "🤖"
        return f"[{time_str}] {role_emoji} {self.role}: {self.content}"


class ConversationBufferMemory:
    """
    Buffer-based conversation memory
    
    Features:
    - Fixed-size buffer (FIFO when full)
    - Context window management
    - Conversation summarization
    - Memory statistics
    """
    
    def __init__(
        self,
        max_messages: int = 20,
        max_context_length: int = 2000,
        enable_summarization: bool = False,
    ):
        """
        Initialize conversation memory
        
        Args:
            max_messages: Maximum number of messages to keep in buffer
            max_context_length: Maximum character length for context
            enable_summarization: Enable automatic summarization (future)
        """
        self.max_messages = max_messages
        self.max_context_length = max_context_length
        self.enable_summarization = enable_summarization
        
        # Use deque for efficient FIFO operations
        self.messages: deque = deque(maxlen=max_messages)
        
        # Conversation metadata
        self.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now()
        self.total_turns = 0
        
        logger.info(f"📝 ConversationBufferMemory initialized (max_messages={max_messages})")
    
    def add_user_message(self, content: str, metadata: Optional[Dict] = None) -> Message:
        """Add user message to memory"""
        message = Message(
            role="user",
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.total_turns += 1
        logger.debug(f"Added user message: {content[:50]}...")
        return message
    
    def add_assistant_message(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Message:
        """Add assistant message to memory"""
        message = Message(
            role="assistant",
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        logger.debug(f"Added assistant message: {content[:50]}...")
        return message
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> Message:
        """Generic add message method"""
        if role == "user":
            return self.add_user_message(content, metadata)
        elif role == "assistant":
            return self.add_assistant_message(content, metadata)
        else:
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")
    
    def get_messages(self, last_n: Optional[int] = None) -> List[Message]:
        """
        Get messages from buffer
        
        Args:
            last_n: Number of last messages to retrieve (None = all)
        
        Returns:
            List of messages (oldest to newest)
        """
        if last_n is None:
            return list(self.messages)
        else:
            # Get last N messages
            return list(self.messages)[-last_n:] if len(self.messages) >= last_n else list(self.messages)
    
    def get_context_window(self, max_turns: int = 5) -> str:
        """
        Get formatted context window for LLM
        
        Args:
            max_turns: Maximum number of conversation turns to include
        
        Returns:
            Formatted conversation history string
        """
        messages = self.get_messages(last_n=max_turns * 2)  # *2 because each turn = user + assistant
        
        if not messages:
            return ""
        
        # Format as conversation history
        context_lines = []
        for msg in messages:
            prefix = "User" if msg.role == "user" else "Assistant"
            context_lines.append(f"{prefix}: {msg.content}")
        
        context = "\n".join(context_lines)
        
        # Truncate if too long
        if len(context) > self.max_context_length:
            context = context[-self.max_context_length:]
            context = "..." + context
            logger.debug(f"Context truncated to {self.max_context_length} chars")
        
        return context
    
    def get_recent_user_queries(self, n: int = 3) -> List[str]:
        """Get N most recent user queries"""
        user_messages = [msg for msg in self.messages if msg.role == "user"]
        return [msg.content for msg in user_messages[-n:]]
    
    def clear(self):
        """Clear all messages from buffer"""
        self.messages.clear()
        self.total_turns = 0
        self.start_time = datetime.now()
        logger.info("🗑️  Memory cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        user_count = sum(1 for msg in self.messages if msg.role == "user")
        assistant_count = sum(1 for msg in self.messages if msg.role == "assistant")
        
        duration = datetime.now() - self.start_time
        
        return {
            'conversation_id': self.conversation_id,
            'total_messages': len(self.messages),
            'user_messages': user_count,
            'assistant_messages': assistant_count,
            'total_turns': self.total_turns,
            'duration_seconds': duration.total_seconds(),
            'buffer_utilization': f"{len(self.messages)}/{self.max_messages}",
        }
    
    def format_history(self, max_messages: Optional[int] = None) -> str:
        """
        Format conversation history for display
        
        Args:
            max_messages: Maximum number of messages to display
        
        Returns:
            Formatted history string
        """
        messages = self.get_messages(last_n=max_messages)
        
        if not messages:
            return "ยังไม่มีประวัติการสนทนา"
        
        lines = ["\n" + "=" * 80]
        lines.append("📜 ประวัติการสนทนา")
        lines.append("=" * 80)
        
        for i, msg in enumerate(messages, 1):
            time_str = msg.timestamp.strftime("%H:%M:%S")
            role_emoji = "👤" if msg.role == "user" else "🤖"
            role_name = "คุณ" if msg.role == "user" else "ระบบ"
            
            lines.append(f"\n[{i}] {time_str} {role_emoji} {role_name}:")
            
            # Wrap long content
            content = msg.content
            if len(content) > 200:
                content = content[:200] + "..."
            
            lines.append(f"  {content}")
            
            # Show metadata if available
            if msg.metadata and msg.metadata.get('sources_count'):
                lines.append(f"  📚 Sources: {msg.metadata['sources_count']}")
        
        lines.append("=" * 80)
        return "\n".join(lines)
    
    def export_history(self) -> List[Dict[str, Any]]:
        """Export conversation history as JSON-serializable list"""
        return [msg.to_dict() for msg in self.messages]
    
    def __len__(self) -> int:
        """Return number of messages in buffer"""
        return len(self.messages)
    
    def __repr__(self) -> str:
        """String representation"""
        stats = self.get_statistics()
        return (
            f"ConversationBufferMemory("
            f"messages={stats['total_messages']}, "
            f"turns={stats['total_turns']}, "
            f"utilization={stats['buffer_utilization']})"
        )


class ConversationMemoryManager:
    """
    Advanced memory manager with multiple memory types
    
    Future enhancements:
    - Summary memory (for very long conversations)
    - Entity memory (track entities mentioned)
    - Vector memory (semantic search in history)
    """
    
    def __init__(self, buffer_size: int = 20):
        """Initialize memory manager"""
        self.buffer_memory = ConversationBufferMemory(max_messages=buffer_size)
        logger.info("🧠 ConversationMemoryManager initialized")
    
    def add_exchange(
        self,
        user_query: str,
        assistant_response: str,
        metadata: Optional[Dict] = None
    ):
        """Add complete user-assistant exchange"""
        self.buffer_memory.add_user_message(user_query, metadata)
        self.buffer_memory.add_assistant_message(assistant_response, metadata)
    
    def get_context_for_rag(self, max_turns: int = 3) -> str:
        """Get formatted context for RAG system"""
        return self.buffer_memory.get_context_window(max_turns=max_turns)
    
    def clear_all(self):
        """Clear all memory types"""
        self.buffer_memory.clear()
    
    def get_full_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        return {
            'buffer_memory': self.buffer_memory.get_statistics(),
        }
    
    def __repr__(self) -> str:
        return f"ConversationMemoryManager({self.buffer_memory})"


if __name__ == "__main__":
    # Example usage
    print("\n" + "=" * 80)
    print("🧪 Testing ConversationBufferMemory")
    print("=" * 80)
    
    # Create memory
    memory = ConversationBufferMemory(max_messages=10)
    
    # Simulate conversation
    memory.add_user_message("ค่าธรรมเนียมโอนที่ดิน 5 ไร่เท่าไหร่?")
    memory.add_assistant_message("ค่าธรรมเนียมโอนที่ดิน 5 ไร่ คิดเป็น 2% ของราคาประเมิน...")
    
    memory.add_user_message("แล้วถ้าจำนองล่ะ?")
    memory.add_assistant_message("ค่าธรรมเนียมจำนองคิด 1% ของยอดจำนอง...")
    
    memory.add_user_message("ขอบคุณครับ")
    memory.add_assistant_message("ยินดีครับ มีอะไรให้ช่วยเพิ่มเติมไหมครับ?")
    
    # Show history
    print(memory.format_history())
    
    # Get context window
    print("\n" + "=" * 80)
    print("📝 Context Window (for LLM):")
    print("=" * 80)
    print(memory.get_context_window(max_turns=2))
    
    # Show statistics
    print("\n" + "=" * 80)
    print("📊 Statistics:")
    print("=" * 80)
    stats = memory.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Memory system test completed!")
