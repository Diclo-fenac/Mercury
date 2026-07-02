import re
import logging

logger = logging.getLogger(__name__)

SUSPICIOUS_PATTERNS = [
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"(?i)you\s+are\s+now\s+a\s+(different|new|developer)\s+(assistant|mode|ai)", re.IGNORECASE),
    re.compile(r"<\s*(system|assistant|admin)\s*>", re.IGNORECASE),
    re.compile(r"(DROP|DELETE|INSERT|UPDATE)\s+(TABLE|FROM|INTO)", re.IGNORECASE),
    re.compile(r"<\s*script[^>]*>", re.IGNORECASE),
    re.compile(r"(?i)reveal\s+(your|the)\s+(system\s+)?prompt", re.IGNORECASE),
    re.compile(r"(?i)show\s+(me\s+)?(your|the)\s+instructions", re.IGNORECASE),
]

SANITIZATION_REPLACEMENT = (
    "I'm only able to help with product search and recommendations within this store. "
    "Let me know what you're looking for!"
)

def sanitize_user_input(text: str) -> tuple[str, bool]:
    """
    Returns (sanitized_text, is_suspicious).
    If suspicious, returns the refusal protocol message.
    """
    if not text or len(text) > 2000:
        return SANITIZATION_REPLACEMENT, True
    
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.search(text):
            logger.warning(
                f"Input sanitization triggered: pattern={pattern.pattern}, "
                f"input_preview={text[:100]}...",
                extra={"sanitization_event": "blocked_input"},
            )
            return SANITIZATION_REPLACEMENT, True
    
    # Strip zero-width characters (encoding bypass technique)
    text = text.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    text = text.replace("\ufeff", "")
    
    return text, False
