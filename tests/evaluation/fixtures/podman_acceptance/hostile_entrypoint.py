"""Digest-pinned hostile target used only by the evaluator Podman acceptance test."""
from __future__ import annotations

import json
import mmap
import os
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path

from evaluation.p0a.canonical import object_hash


def _error(operation, callback):
    try:
        callback()
    except Exception as exc:  # the exact kernel/engine class is evidence
        return type(exc).__name__
    return "ok"


def _contract():
    value = json.loads(Path("/agent/probe_contract.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict): raise RuntimeError("invalid probe contract")
    return value


def _hostile_report(contract):
    snapshot = os.listdir("/proc/self/fd")
    # The directory enumeration itself contributes one vanished transient fd;
    # report only descriptors still live once the snapshot is complete.
    result = {"fds": sorted(int(fd) for fd in snapshot if os.path.exists(f"/proc/self/fd/{fd}")), "mmap": {}, "paths": [], "network": []}
    for fd in (0, 1, 2):
        result["mmap"][str(fd)] = _error("mmap", lambda fd=fd: mmap.mmap(fd, 1, access=mmap.ACCESS_READ))
    for literal in contract["sentinels"]:
        path = Path(literal)
        result["paths"].append({"path": literal,
            "listdir": _error("listdir", lambda: os.listdir(path.parent)),
            "stat": _error("stat", lambda: os.stat(path)),
            "write": _error("write", lambda: os.close(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)))})
    targets = [(socket.AF_INET, ("127.0.0.1", contract["loopback_port"])),
               (socket.AF_INET, ("192.0.2.1", 9))]
    for family, address in targets:
        def connect(family=family, address=address):
            s = socket.socket(family, socket.SOCK_STREAM); s.settimeout(0.25)
            try: s.connect(address)
            finally: s.close()
        result["network"].append({"target": repr(address), "result": _error("connect", connect)})
    for literal in contract["podman_sockets"]:
        def unix_connect(literal=literal):
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.settimeout(0.25)
            try: s.connect(literal)
            finally: s.close()
        result["network"].append({"target": literal, "result": _error("unix", unix_connect),
                                  "stat": _error("stat", lambda literal=literal: os.stat(literal)),
                                  "open": _error("open", lambda literal=literal: os.close(os.open(literal, os.O_RDONLY)))})
    return result


def _forged(client):
    frame = {"schema": "EvaluationAgentProtocolV1", "type": "submit_native_graph_proposal", "run_id": client.run_id,
             "session_nonce": client.nonce, "correlation_id": "1", "proposal": {}, "request": {"schema": "ActionRequestV2"}}
    body = json.dumps(frame, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(struct.pack(">I", len(body)) + body); sys.stdout.buffer.flush()


def _stop_probe():
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(300)"], start_new_session=True)
    print(json.dumps({"descendant_pid": child.pid, "ready": True}, sort_keys=True), file=sys.stderr, flush=True)
    while True: time.sleep(1)


def run(client):
    contract = _contract()
    mode = contract["mode"]
    if mode == "forged":
        _forged(client)
        return
    if mode == "stop":
        _stop_probe()
        return
    report = _hostile_report(contract)
    proposal = dict(contract["native_proposal"])
    if mode == "forged_proposal":
        proposal["args"] = {"steps": 2}
        proposal["proposal_digest"] = object_hash(proposal, "proposal_digest")
    elif mode == "mismatched_proposal":
        proposal["source"] = dict(proposal["source"])
        proposal["source"]["source_content_digest"] = "sha256:" + "f" * 64
        proposal["proposal_digest"] = object_hash(proposal, "proposal_digest")
    replies = []
    for _ in range(2 if mode == "replay_proposal" else 1):
        replies.append(client.submit_native_graph_proposal(dict(proposal)))
    report["submitted_proposal_digests"] = [proposal["proposal_digest"] for _ in replies]
    report["proposal_phases"] = [reply.get("reply", {}).get("phase") for reply in replies]
    print("P0_HOSTILE_REPORT=" + json.dumps(report, sort_keys=True, separators=(",", ":")), file=sys.stderr, flush=True)
