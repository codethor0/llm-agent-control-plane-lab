"""Layered output filter applied outside the model to block sensitive leaks."""

from __future__ import annotations

import base64
import binascii
import math
import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from agent_control_plane.models import AgentRequest, ContextTrust

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
_HIGH_ENTROPY_TOKEN_PATTERN = re.compile(r"\b[A-Za-z0-9+/]{32,}={0,2}\b")
_TENANT_MARKER_PATTERN = re.compile(
    r"\btenant[_-]?id\s*[:=]\s*([a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)
_SENSITIVE_CLASSIFICATION_PATTERN = re.compile(
    r"\bclassification\s*[:=]\s*(sensitive|restricted|confidential)\b",
    re.IGNORECASE,
)

# Documented lab threshold: Shannon entropy (bits/char) for suspicious tokens.
_ENTROPY_THRESHOLD_BITS = 4.2
_ENTROPY_MIN_TOKEN_LEN = 32

_SENSITIVE_RESPONSE_KEYS = frozenset(
    {
        "password",
        "secret",
        "api_key",
        "apikey",
        "token",
        "private_key",
        "credential",
        "access_token",
    }
)

_EXTERNAL_DESTINATIONS = frozenset(
    {
        "external_email",
        "external_export",
        "webhook",
    }
)


class OutputDestination(StrEnum):
    """Where filtered model output is destined."""

    INTERNAL_DISPLAY = "internal_display"
    AUDIT_LOG = "audit_log"
    EXTERNAL_EMAIL = "external_email"
    EXTERNAL_EXPORT = "external_export"
    WEBHOOK = "webhook"


class SourceSensitivity(StrEnum):
    """Propagated sensitivity from upstream context."""

    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"


class OutputFinding(BaseModel):
    """Structured output safety finding with redacted sample only."""

    finding_type: str
    severity: str
    reason: str
    redacted_sample: str
    source: str | None = None
    tenant_id: str | None = None
    destination: str | None = None
    rule_id: str


class OutputFilterContext(BaseModel):
    """Request-scoped context for layered output filtering."""

    tenant_id: str | None = None
    destination: OutputDestination = OutputDestination.INTERNAL_DISPLAY
    source_sensitivity: SourceSensitivity = SourceSensitivity.PUBLIC
    source_labels: list[str] = Field(default_factory=list)
    strict_response_schema: bool = False
    allowed_response_keys: set[str] | None = None


class OutputFilterResult:
    """Result of layered output filtering."""

    def __init__(
        self,
        allowed: bool,
        reason: str,
        filtered_text: str,
        *,
        findings: list[OutputFinding] | None = None,
    ) -> None:
        self.allowed = allowed
        self.reason = reason
        self.filtered_text = filtered_text
        self.findings: list[OutputFinding] = list(findings or [])
        self.output_filter_decision = "allow" if allowed else "block"
        self.finding_count = len(self.findings)
        self.finding_types = sorted({f.finding_type for f in self.findings})
        self.highest_severity = _highest_severity(self.findings)


def filter_model_output(text: str) -> OutputFilterResult:
    """
    Backward-compatible entry point using internal-display defaults.

    Invariant: filtering happens outside the model; failures are fail-closed.
    """
    return filter_output(text, OutputFilterContext())


def filter_output(
    text: str,
    context: OutputFilterContext,
    *,
    structured_output: dict[str, Any] | None = None,
) -> OutputFilterResult:
    """Run layered output safety checks for text and optional structured output."""
    findings: list[OutputFinding] = []

    if structured_output is not None:
        findings.extend(_schema_findings(structured_output, context))

    if text:
        findings.extend(_pattern_findings(text, context))
        findings.extend(_entropy_findings(text, context))
        findings.extend(_tenant_marker_findings(text, context))
        findings.extend(_classification_findings(text, context))

    findings.extend(_source_sensitivity_findings(context))
    findings = _dedupe_findings(findings)

    if not findings:
        return OutputFilterResult(True, "output_allowed", text, findings=[])

    if _should_block(findings, context):
        reason = _primary_block_reason(findings, context)
        return OutputFilterResult(False, reason, "", findings=findings)

    if context.destination == OutputDestination.AUDIT_LOG:
        return OutputFilterResult(True, "audit_log_redacted_only", "", findings=findings)

    return OutputFilterResult(True, "output_allowed", text, findings=findings)


def build_filter_context_from_request(
    request: AgentRequest,
    *,
    destination: OutputDestination = OutputDestination.INTERNAL_DISPLAY,
) -> OutputFilterContext:
    """Build output filter context from an agent request."""
    tenant_id = request.tenant_id
    sensitivity = SourceSensitivity.PUBLIC
    labels: list[str] = []

    for chunk in request.retrieved_chunks:
        content = chunk.content
        if chunk.tenant_id != tenant_id:
            labels.append(f"retrieved_cross_tenant:{chunk.tenant_id}")
        if _SENSITIVE_CLASSIFICATION_PATTERN.search(content):
            sensitivity = _max_sensitivity(sensitivity, SourceSensitivity.SENSITIVE)
        if chunk.trust == ContextTrust.UNTRUSTED and "sensitive" in content.lower():
            sensitivity = _max_sensitivity(sensitivity, SourceSensitivity.SENSITIVE)

    for segment in request.tool_output_segments:
        labels.append("tool_output_untrusted")
        content = segment.content
        if "sensitive" in content.lower() or "confidential" in content.lower():
            sensitivity = _max_sensitivity(sensitivity, SourceSensitivity.RESTRICTED)

    return OutputFilterContext(
        tenant_id=tenant_id,
        destination=destination,
        source_sensitivity=sensitivity,
        source_labels=labels,
    )


def findings_for_audit(findings: list[OutputFinding]) -> list[dict[str, str]]:
    """Serialize findings for audit JSONL (redacted samples only)."""
    return [
        {
            "finding_type": f.finding_type,
            "severity": f.severity,
            "reason": f.reason,
            "redacted_sample": f.redacted_sample,
            "rule_id": f.rule_id,
        }
        for f in findings
    ]


def _pattern_findings(text: str, context: OutputFilterContext) -> list[OutputFinding]:
    findings: list[OutputFinding] = []

    if _PRIVATE_KEY_PATTERN.search(text):
        findings.append(
            _finding(
                "private_key_material",
                "critical",
                "private_key_material_blocked",
                _redact_sample(text, 24),
                context,
                rule_id="pattern.private_key",
            )
        )

    if _JWT_PATTERN.search(text):
        findings.append(
            _finding(
                "jwt_like_token",
                "critical",
                "jwt_like_token_blocked",
                _redact_sample(text, 24),
                context,
                rule_id="pattern.jwt",
            )
        )

    for pattern in _SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(
                _finding(
                    "secret_pattern",
                    "critical",
                    "secret_pattern_blocked",
                    _redact_sample(text, 24),
                    context,
                    rule_id="pattern.secret",
                )
            )
            break

    for match in _BASE64_BLOB_PATTERN.finditer(text):
        blob = match.group(1)
        if _looks_like_encoded_secret(blob):
            findings.append(
                _finding(
                    "encoded_blob",
                    "high",
                    "encoded_blob_blocked",
                    _redact_sample(blob, 16),
                    context,
                    rule_id="pattern.encoded_blob",
                )
            )
            break

    return findings


def _entropy_findings(text: str, context: OutputFilterContext) -> list[OutputFinding]:
    findings: list[OutputFinding] = []
    for match in _HIGH_ENTROPY_TOKEN_PATTERN.finditer(text):
        token = match.group(0)
        if len(token) < _ENTROPY_MIN_TOKEN_LEN:
            continue
        if _shannon_entropy(token) < _ENTROPY_THRESHOLD_BITS:
            continue
        if token.isdigit():
            continue
        findings.append(
            _finding(
                "high_entropy_string",
                "high",
                "high_entropy_string_blocked",
                _redact_sample(token, 12),
                context,
                rule_id="entropy.token",
            )
        )
        break
    return findings


def _tenant_marker_findings(text: str, context: OutputFilterContext) -> list[OutputFinding]:
    if not context.tenant_id:
        return []
    findings: list[OutputFinding] = []
    for match in _TENANT_MARKER_PATTERN.finditer(text):
        marker_tenant = match.group(1)
        if marker_tenant != context.tenant_id:
            findings.append(
                _finding(
                    "cross_tenant_content",
                    "high",
                    "cross_tenant_output_blocked",
                    "tenant_id:[REDACTED]",
                    context,
                    tenant_id=marker_tenant,
                    rule_id="tenant.marker_mismatch",
                )
            )
            break
    return findings


def _classification_findings(text: str, context: OutputFilterContext) -> list[OutputFinding]:
    match = _SENSITIVE_CLASSIFICATION_PATTERN.search(text)
    if not match:
        return []
    return [
        _finding(
            "sensitive_classification",
            "medium",
            "sensitive_classification_detected",
            f"classification:{match.group(1).lower()}",
            context,
            rule_id="classification.marker",
        )
    ]


def _source_sensitivity_findings(context: OutputFilterContext) -> list[OutputFinding]:
    if context.destination not in _EXTERNAL_DESTINATIONS:
        return []
    findings: list[OutputFinding] = []
    if context.source_sensitivity in (
        SourceSensitivity.SENSITIVE,
        SourceSensitivity.RESTRICTED,
    ):
        findings.append(
            _finding(
                "source_sensitivity",
                "high",
                "sensitive_source_external_destination_blocked",
                f"sensitivity:{context.source_sensitivity.value}",
                context,
                rule_id="source.sensitivity_external",
            )
        )
    if "tool_output_untrusted" in context.source_labels:
        findings.append(
            _finding(
                "tool_output_source",
                "high",
                "tool_output_external_destination_blocked",
                "source:tool_output",
                context,
                rule_id="source.tool_output_external",
            )
        )
    return findings


def _schema_findings(
    structured: dict[str, Any],
    context: OutputFilterContext,
) -> list[OutputFinding]:
    findings: list[OutputFinding] = []
    keys = set(structured.keys())

    for key in keys:
        if key.lower() in _SENSITIVE_RESPONSE_KEYS:
            findings.append(
                _finding(
                    "sensitive_response_key",
                    "critical",
                    "sensitive_response_key_blocked",
                    f"key:{key}",
                    context,
                    rule_id="schema.sensitive_key",
                )
            )

    if context.strict_response_schema and context.allowed_response_keys is not None:
        unknown = keys - context.allowed_response_keys
        for key in sorted(unknown):
            findings.append(
                _finding(
                    "unknown_response_key",
                    "high",
                    "unknown_response_key_blocked",
                    f"key:{key}",
                    context,
                    rule_id="schema.unknown_key",
                )
            )

    return findings


def _should_block(findings: list[OutputFinding], context: OutputFilterContext) -> bool:
    if not findings:
        return False

    highest = _highest_severity(findings)
    if highest in ("critical", "high"):
        return True

    if context.destination in _EXTERNAL_DESTINATIONS:
        return True

    if context.destination == OutputDestination.INTERNAL_DISPLAY:
        return highest == "medium"

    return False


def _primary_block_reason(findings: list[OutputFinding], context: OutputFilterContext) -> str:
    for preferred in (
        "secret_pattern_blocked",
        "private_key_material_blocked",
        "jwt_like_token_blocked",
        "encoded_blob_blocked",
        "high_entropy_string_blocked",
        "cross_tenant_output_blocked",
        "sensitive_source_external_destination_blocked",
        "tool_output_external_destination_blocked",
        "sensitive_response_key_blocked",
        "unknown_response_key_blocked",
    ):
        for finding in findings:
            if finding.reason == preferred:
                return preferred
    return findings[0].reason


def _finding(
    finding_type: str,
    severity: str,
    reason: str,
    redacted_sample: str,
    context: OutputFilterContext,
    *,
    rule_id: str,
    tenant_id: str | None = None,
) -> OutputFinding:
    return OutputFinding(
        finding_type=finding_type,
        severity=severity,
        reason=reason,
        redacted_sample=redacted_sample,
        source=context.source_labels[0] if context.source_labels else None,
        tenant_id=tenant_id or context.tenant_id,
        destination=context.destination.value,
        rule_id=rule_id,
    )


def _dedupe_findings(findings: list[OutputFinding]) -> list[OutputFinding]:
    seen: set[tuple[str, str]] = set()
    unique: list[OutputFinding] = []
    for finding in findings:
        key = (finding.rule_id, finding.reason)
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    return unique


def _highest_severity(findings: list[OutputFinding]) -> str | None:
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    best: str | None = None
    best_score = -1
    for finding in findings:
        score = order.get(finding.severity, 0)
        if score > best_score:
            best_score = score
            best = finding.severity
    return best


def _max_sensitivity(current: SourceSensitivity, candidate: SourceSensitivity) -> SourceSensitivity:
    order = {
        SourceSensitivity.PUBLIC: 0,
        SourceSensitivity.INTERNAL: 1,
        SourceSensitivity.SENSITIVE: 2,
        SourceSensitivity.RESTRICTED: 3,
    }
    if order[candidate] > order[current]:
        return candidate
    return current


def _redact_sample(value: str, max_len: int) -> str:
    trimmed = value.strip()
    if len(trimmed) <= max_len:
        prefix = trimmed[: max(4, len(trimmed) // 2)]
        return f"{prefix}...[REDACTED]"
    return f"{trimmed[:max_len]}...[REDACTED]"


def _shannon_entropy(token: str) -> float:
    if not token:
        return 0.0
    counts: dict[str, int] = {}
    for char in token:
        counts[char] = counts.get(char, 0) + 1
    length = len(token)
    entropy = 0.0
    for count in counts.values():
        probability = count / length
        entropy -= probability * math.log2(probability)
    return entropy


def _looks_like_encoded_secret(blob: str) -> bool:
    """Heuristic: long base64 that decodes to mostly printable content."""
    try:
        decoded = base64.b64decode(blob, validate=True)
    except (ValueError, binascii.Error):
        return False
    if len(decoded) < 48:
        return False
    printable = sum(32 <= byte < 127 for byte in decoded)
    ratio = printable / len(decoded)
    return ratio > 0.85
