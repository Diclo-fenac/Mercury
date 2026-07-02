"""
ID Generator - Infrastructure Layer
Handles ID and timestamp generation
"""
import os
import time
import uuid
from datetime import datetime


def uuid7() -> str:
    """
    Generate a UUID v7 (time-ordered).
    Layout: 48-bit unix_ms | 4-bit ver(7) | 12-bit rand_a | 2-bit var | 62-bit rand_b
    """
    ms = int(time.time() * 1000)
    rand = int.from_bytes(os.urandom(10), 'big')
    # rand_a: 12 bits, rand_b: 62 bits
    rand_a = (rand >> 62) & 0xFFF
    rand_b = rand & 0x3FFFFFFFFFFFFFFF
    hi = (ms << 16) | (0x7 << 12) | rand_a
    lo = (0b10 << 62) | rand_b
    return str(uuid.UUID(int=(hi << 64) | lo))


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