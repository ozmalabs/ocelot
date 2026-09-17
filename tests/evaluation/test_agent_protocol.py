from __future__ import annotations

import io
import struct

import pytest

from evaluation.p0a.agent_protocol import MAX_FRAME_BYTES, SCHEMA, decode_frame, encode_frame, validate_frame
from evaluation.p0a.canonical import ProtocolError


def frame(kind="hello", **extra):
    return {"schema": SCHEMA, "type": kind, "run_id": "run", "session_nonce": "nonce", **extra}


def test_canonical_bounded_handshake_and_native_graph_candidate_only():
    hello = frame()
    assert decode_frame(io.BytesIO(encode_frame(hello))) == hello
    proposal = frame("submit_native_graph_proposal", correlation_id="1", proposal={"schema": "GraphActionProposalV1"})
    assert validate_frame(proposal, run_id="run", nonce="nonce") == proposal
    with pytest.raises(ProtocolError, match="message type"):
        encode_frame(frame("submit_graph_proposal", correlation_id="1", proposal_id="opaque-id"))


@pytest.mark.parametrize("extra", [
    {"path": "/host/secret"}, {"fd": 4}, {"grant": "authority"},
    {"callback": "module:call"}, {"request": {"schema": "ActionRequestV2"}},
])
def test_protocol_rejects_authority_smuggling(extra):
    proposal = frame("submit_native_graph_proposal", correlation_id="1", proposal={"schema": "GraphActionProposalV1"}, **extra)
    with pytest.raises(ProtocolError, match="authority field"):
        encode_frame(proposal)


def test_protocol_rejects_oversize_and_truncated_frames():
    with pytest.raises(ProtocolError, match="frame size"):
        decode_frame(io.BytesIO(struct.pack(">I", MAX_FRAME_BYTES + 1)))
    with pytest.raises(ProtocolError, match="truncated"):
        decode_frame(io.BytesIO(struct.pack(">I", 5) + b"{}"))
