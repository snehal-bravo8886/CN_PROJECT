"""Wire protocol and shared severity-to-UDP-port contract.

The destination UDP port identifies the severity to an OpenFlow 1.3 controller.
Only Python's standard library is used.
"""

import json
import re
import uuid
from typing import Any

VERSION = 1
DEFAULT_BASE_PORT = 10000
SEVERITIES = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
PORT_OFFSETS = {name: offset for offset, name in enumerate(SEVERITIES)}
DEFAULT_SEVERITY_PORTS = {name: DEFAULT_BASE_PORT + offset for name, offset in PORT_OFFSETS.items()}
MAX_DATAGRAM_BYTES = 1200  # Avoid ordinary Ethernet IP fragmentation.
MAX_MESSAGE_CHARS = 700
HOST_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
FIELDS = {"version", "host_id", "session_id", "severity", "sequence", "sent_ns", "message"}


class ProtocolError(ValueError):
    """Message failed validation."""


def validate_base_port(base_port: int) -> None:
    if not isinstance(base_port, int) or isinstance(base_port, bool) or not 1024 <= base_port <= 65531:
        raise ValueError("base port must be between 1024 and 65531 (five consecutive UDP ports)")


def severity_port(severity: str, base_port: int = DEFAULT_BASE_PORT) -> int:
    validate_base_port(base_port)
    if severity not in PORT_OFFSETS:
        raise ValueError(f"unsupported severity: {severity}")
    return base_port + PORT_OFFSETS[severity]


def validate_record(record: Any) -> dict:
    if not isinstance(record, dict) or set(record) != FIELDS:
        raise ProtocolError("record must be an object with the exact protocol fields")
    if type(record["version"]) is not int or record["version"] != VERSION:
        raise ProtocolError("unsupported protocol version")
    if not isinstance(record["host_id"], str) or not HOST_PATTERN.fullmatch(record["host_id"]):
        raise ProtocolError("invalid host_id (1-64 letters, numbers, _, -, .)")
    if not isinstance(record["session_id"], str):
        raise ProtocolError("session_id must be a UUID")
    try:
        parsed = uuid.UUID(record["session_id"])
    except (ValueError, AttributeError, TypeError) as exc:
        raise ProtocolError("session_id must be a UUID") from exc
    if str(parsed) != record["session_id"]:
        raise ProtocolError("session_id must be a canonical lowercase UUID")
    if record["severity"] not in SEVERITIES or not isinstance(record["severity"], str):
        raise ProtocolError("unknown severity")
    if type(record["sequence"]) is not int or not 1 <= record["sequence"] <= 2**63 - 1:
        raise ProtocolError("sequence must be a positive integer")
    if type(record["sent_ns"]) is not int or record["sent_ns"] <= 0:
        raise ProtocolError("sent_ns must be a positive Unix timestamp in nanoseconds")
    if not isinstance(record["message"], str) or not 1 <= len(record["message"]) <= MAX_MESSAGE_CHARS:
        raise ProtocolError("message must have 1-700 characters")
    return record


def encode_record(record: dict) -> bytes:
    validate_record(record)
    data = json.dumps(record, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(data) > MAX_DATAGRAM_BYTES:
        raise ProtocolError(f"UDP datagram is too large (max {MAX_DATAGRAM_BYTES} bytes)")
    return data


def decode_record(payload: bytes, *, expected_severity: str | None = None) -> dict:
    if not payload or len(payload) > MAX_DATAGRAM_BYTES:
        raise ProtocolError(f"empty or oversized datagram (max {MAX_DATAGRAM_BYTES} bytes)")
    try:
        record = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid UTF-8 or JSON") from exc
    record = validate_record(record)
    if expected_severity is not None and record["severity"] != expected_severity:
        raise ProtocolError("severity does not match destination UDP port")
    return record
