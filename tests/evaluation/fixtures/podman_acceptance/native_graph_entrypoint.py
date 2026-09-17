from __future__ import annotations

import json
import mmap
import os
import socket
import struct
import sys
from pathlib import Path

from evaluation.p0a.canonical import object_hash


def _error(callback):
    try:
        callback()
    except Exception as exc:
        return type(exc).__name__
    return "ok"


def _contract():
    return json.loads(Path("/agent/probe_contract.json").read_text(encoding="utf-8"))


def _hostile_report(contract):
    snapshot = os.listdir("/proc/self/fd")
    result = {"fds": sorted(int(fd) for fd in snapshot if os.path.exists(f"/proc/self/fd/{fd}")),
              "mmap": {}, "paths": [], "network": []}
    for fd in (0, 1, 2):
        result["mmap"][str(fd)] = _error(lambda fd=fd: mmap.mmap(fd, 1, access=mmap.ACCESS_READ))
    for literal in contract["sentinels"]:
        path = Path(literal)
        result["paths"].append({"path": literal,
            "listdir": _error(lambda: os.listdir(path.parent)), "stat": _error(lambda: os.stat(path)),
            "write": _error(lambda: os.close(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)))})
    for family, address in ((socket.AF_INET, ("127.0.0.1", contract["loopback_port"])),
                            (socket.AF_INET, ("192.0.2.1", 9))):
        def connect(family=family, address=address):
            s = socket.socket(family, socket.SOCK_STREAM); s.settimeout(0.25)
            try: s.connect(address)
            finally: s.close()
        result["network"].append({"target": repr(address), "result": _error(connect)})
    for literal in contract["podman_sockets"]:
        def unix_connect(literal=literal):
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.settimeout(0.25)
            try: s.connect(literal)
            finally: s.close()
        result["network"].append({"target": literal, "result": _error(unix_connect),
                                  "stat": _error(lambda literal=literal: os.stat(literal)),
                                  "open": _error(lambda literal=literal: os.close(os.open(literal, os.O_RDONLY)))})
    return result


def _native_proposal():
    import substrate_rs
    seed = json.loads(Path("/agent/native_graph_proposal_seed.json").read_text(encoding="utf-8"))
    facts = json.loads(Path("/agent/native_sealed_graph_action_fact.json").read_text(encoding="utf-8"))
    substrate = substrate_rs.Substrate()
    root = substrate.add_node(facts["root_type"], facts["root_attrs"])
    fact = substrate.add_node("SealedGraphActionFactV1", facts["proposal"])
    substrate.add_edge_unchecked(root, facts["edge_type"], fact)
    substrate.load_seed_manifest(seed)
    if substrate.tick(16) >= 16:
        raise RuntimeError("native fixed point exhausted")
    nodes = substrate.nodes("GraphActionProposalV1")
    if len(nodes) != 1:
        raise RuntimeError("native proposal count")
    return dict(substrate.node(nodes[0])["attrs"])


def _export_substitution(client):
    frame = {"schema": "EvaluationAgentProtocolV1", "type": "submit_native_graph_proposal", "run_id": client.run_id,
             "session_nonce": client.nonce, "correlation_id": "1", "proposal": _native_proposal(),
             "native_graph_export": {"schema": "NativeGraphEvidenceExportV1"}}
    body = json.dumps(frame, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(struct.pack(">I", len(body)) + body); sys.stdout.buffer.flush()


def run(client):
    contract = _contract()
    if contract["mode"] == "export_frame_substitution":
        _export_substitution(client)
        return
    report = _hostile_report(contract)
    proposal = _native_proposal()
    if contract["mode"] == "candidate_substitution":
        proposal["args"] = {"steps": 2}; proposal["proposal_digest"] = object_hash(proposal, "proposal_digest")
    replies = [client.submit_native_graph_proposal(dict(proposal))
               for _ in range(2 if contract["mode"] == "candidate_replay" else 1)]
    report["submitted_proposal_digests"] = [proposal["proposal_digest"] for _ in replies]
    report["proposal_phases"] = [reply.get("reply", {}).get("phase") for reply in replies]
    print("P0_HOSTILE_REPORT=" + json.dumps(report, sort_keys=True, separators=(",", ":")), file=sys.stderr, flush=True)
