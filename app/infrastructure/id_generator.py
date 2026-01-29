"""
ID Generator - Infrastructure Layer
Handles ID and timestamp generation
"""
import uuid
from datetime import datetime


class IDGenerator:
    """Generates unique IDs for various entities"""
    
    @staticmethod
    def conversation_id(user_id: str) -> str:
        """Generate conversation ID"""
        return f"conv_{user_id}_{uuid.uuid4().hex[:8]}"
    
    @staticmethod
    def message_id() -> str:
        """Generate message ID"""
        return f"msg_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def user_id() -> str:
        """Generate user ID"""
        return f"user_{uuid.uuid4().hex[:10]}"
    
    @staticmethod
    def product_id() -> str:
        """Generate product ID"""
        return f"prod_{uuid.uuid4().hex[:10]}"
    
    @staticmethod
    def session_id() -> str:
        """Generate session ID"""
        return f"sess_{uuid.uuid4().hex[:16]}"
    
    @staticmethod
    def timestamp() -> datetime:
        """Get current timestamp"""
        return datetime.now()
    
    @staticmethod
    def timestamp_iso() -> str:
        """Get current timestamp as ISO string"""
        return datetime.now().isoformat()