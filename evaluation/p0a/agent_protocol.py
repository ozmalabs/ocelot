"""Bounded canonical stdio protocol between the evaluator and fresh worker."""
from __future__ import annotations

import os
import struct
from typing import Any, BinaryIO

from .canonical import ProtocolError, canonical_bytes, parse_canonical

MAX_FRAME_BYTES = 64 * 1024
SCHEMA = "EvaluationAgentProtocolV1"
_FORBIDDEN = frozenset({"path", "paths", "fd", "fds", "grant", "grant_bytes", "callback", "request", "action_request", "result_file"})


def _validate_common(frame: dict[str, Any], *, run_id: str | None = None, nonce: str | None = None) -> None:
    if frame.get("schema") != SCHEMA or not isinstance(frame.get("type"), str):
        raise ProtocolError("agent protocol schema")
    if not isinstance(frame.get("run_id"), str) or not isinstance(frame.get("session_nonce"), str):
        raise ProtocolError("agent protocol binding")
    if run_id is not None and frame["run_id"] != run_id:
        raise ProtocolError("agent protocol run binding")
    if nonce is not None and frame["session_nonce"] != nonce:
        raise ProtocolError("agent protocol session binding")
    if _FORBIDDEN.intersection(frame):
        raise ProtocolError("agent protocol authority field")


def validate_frame(frame: dict[str, Any], *, run_id: str | None = None, nonce: str | None = None) -> dict[str, Any]:
    _validate_common(frame, run_id=run_id, nonce=nonce)
    kind = frame["type"]
    allowed: set[str]
    if kind == "hello":
        allowed = {"schema", "type", "run_id", "session_nonce"}
    elif kind == "submit_native_graph_proposal":
        # The worker may submit a bounded graph candidate, never an opaque ID
        # that the evaluator silently turns into a proposal.  It still has no
        # action, grant, callback, path, or descriptor authority.
        allowed = {"schema", "type", "run_id", "session_nonce", "correlation_id", "proposal"}
        if not isinstance(frame.get("correlation_id"), str) or not isinstance(frame.get("proposal"), dict):
            raise ProtocolError("invalid native graph proposal frame")
    elif kind == "reply":
        allowed = {"schema", "type", "run_id", "session_nonce", "correlation_id", "reply", "outcome"}
        if not isinstance(frame.get("correlation_id"), str) or not isinstance(frame.get("reply"), dict) or not isinstance(frame.get("outcome"), dict):
            raise ProtocolError("invalid agent reply")
    elif kind in {"terminal", "heartbeat"}:
        allowed = {"schema", "type", "run_id", "session_nonce"}
    else:
        raise ProtocolError("agent protocol message type")
    if set(frame) != allowed:
        raise ProtocolError("agent protocol fields")
    return frame


def encode_frame(frame: dict[str, Any]) -> bytes:
    validate_frame(frame)
    payload = canonical_bytes(frame)
    if len(payload) > MAX_FRAME_BYTES:
        raise ProtocolError("agent protocol frame too large")
    return struct.pack(">I", len(payload)) + payload


def decode_frame(stream: BinaryIO) -> dict[str, Any]:
    prefix = stream.read(4)
    if not prefix:
        raise EOFError("agent protocol EOF")
    if len(prefix) != 4:
        raise ProtocolError("truncated agent protocol frame")
    (size,) = struct.unpack(">I", prefix)
    if not 0 < size <= MAX_FRAME_BYTES:
        raise ProtocolError("agent protocol frame size")
    payload = stream.read(size)
    if len(payload) != size:
        raise ProtocolError("truncated agent protocol frame")
    return validate_frame(parse_canonical(payload))


def write_frame(stream: BinaryIO, frame: dict[str, Any]) -> None:
    stream.write(encode_frame(frame))
    stream.flush()


def session_nonce() -> str:
    return os.urandom(32).hex()
