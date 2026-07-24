import re


class PIIRedactor:
    """Redacts sensitive PII from search queries before caching or logging."""

    EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
    # Matches sequences of 9 to 16 digits, with optional spaces or dashes
    NUMBER_REGEX = re.compile(r'\b\d(?:[ -]*\d){8,15}\b')

    @classmethod
    def redact(cls, text: str) -> str:
        """Replace potential PII in text with placeholders."""
        if not text:
            return text

        redacted = cls.EMAIL_REGEX.sub("[EMAIL]", text)
        redacted = cls.NUMBER_REGEX.sub("[REDACTED_NUMBER]", redacted)
        return redacted
