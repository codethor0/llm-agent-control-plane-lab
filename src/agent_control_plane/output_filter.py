"""Output filter applied outside the model to block sensitive leaks."""

import base64
import binascii
import re

# Clearly fake patterns for detector tests only.
_SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"sk-[a-zA-Z0-9_-]{20,}"),
    re.compile(r"password\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*[:=]\s*\S+", re.IGNORECASE),
]
_PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----")
_JWT_PATTERN = re.compile(r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+")
_BASE64_BLOB_PATTERN = re.compile(
    r"(?:^|[^A-Za-z0-9+/])([A-Za-z0-9+/]{80,}={0,2})(?:$|[^A-Za-z0-9+/=])"
)


class OutputFilterResult:
    """Result of output filtering."""

    def __init__(self, allowed: bool, reason: str, filtered_text: str) -> None:
        self.allowed = allowed
        self.reason = reason
        self.filtered_text = filtered_text


def filter_model_output(text: str) -> OutputFilterResult:
    """
    Block model text that appears to contain secrets or sensitive material.

    Invariant: filtering happens outside the model; failures are fail-closed.
    """
    if not text:
        return OutputFilterResult(True, "empty_output_allowed", "")

    if _PRIVATE_KEY_PATTERN.search(text):
        return OutputFilterResult(False, "private_key_material_blocked", "")

    if _JWT_PATTERN.search(text):
        return OutputFilterResult(False, "jwt_like_token_blocked", "")

    for pattern in _SECRET_PATTERNS:
        if pattern.search(text):
            return OutputFilterResult(False, "secret_pattern_blocked", "")

    for match in _BASE64_BLOB_PATTERN.finditer(text):
        blob = match.group(1)
        if _looks_like_encoded_secret(blob):
            return OutputFilterResult(False, "encoded_blob_blocked", "")

    return OutputFilterResult(True, "output_allowed", text)


def _looks_like_encoded_secret(blob: str) -> bool:
    """Heuristic: long base64 that decodes to mostly printable content."""
    try:
        decoded = base64.b64decode(blob, validate=True)
    except (ValueError, binascii.Error):
        return False
    if len(decoded) < 48:
        return False
    printable = sum(32 <= b < 127 for b in decoded)
    ratio = printable / len(decoded)
    return ratio > 0.85
