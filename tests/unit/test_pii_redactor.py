import pytest

from app.utils.pii_redactor import PIIRedactor


def test_redact_email():
    original = "User contact is john.doe@example.com."
    redacted = PIIRedactor.redact(original)
    assert redacted == "User contact is [EMAIL]."

def test_redact_credit_card():
    # 16 digits with spaces
    original = "My card is 1234 5678 1234 5678"
    redacted = PIIRedactor.redact(original)
    assert redacted == "My card is [REDACTED_NUMBER]"

    # 16 digits without spaces
    original2 = "Use 1234567812345678 for payment"
    redacted2 = PIIRedactor.redact(original2)
    assert redacted2 == "Use [REDACTED_NUMBER] for payment"

def test_redact_ssn():
    # 9 digits with dashes
    original = "SSN is 123-45-6789"
    redacted = PIIRedactor.redact(original)
    assert redacted == "SSN is [REDACTED_NUMBER]"

def test_redact_no_pii():
    original = "Looking for running shoes size 10"
    redacted = PIIRedactor.redact(original)
    assert redacted == original

def test_redact_empty():
    assert PIIRedactor.redact("") == ""
    assert PIIRedactor.redact(None) is None
