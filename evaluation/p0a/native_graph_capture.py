"""Evaluator-owned reconstruction of a finite sealed native graph closure.

This module has no worker client, broker, or projection capability.  It verifies
exact closure bytes, starts fresh isolated native interpreters, and produces the
already-attested export consumed by :func:`evaluation_mode` before a worker is
allowed to start.
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import ProtocolError, canonical_bytes, object_hash, parse_canonical, sha256
from .provenance import make_native_graph_export_attestation

_REQUIRED_FILES = (
    "substrate_rs/__init__.py",
    "substrate_rs/_native.abi3.so",
    "native_graph_proposal_seed.json",
    "native_sealed_graph_action_fact.json",
    "native_graph_entrypoint.py",
)
_PROPOSAL_FIELDS = frozenset({"schema", "proposal_id", "kind", "args", "input_refs", "source",
                              "causal_parent_receipt_hash", "requested_budget", "graph_logical_time",
                              "proposal_digest"})


@dataclass(frozen=True)
class NativeGraphClosureV1:
    """An explicit, regular-file-only native execution closure."""
    root: Path
    files: dict[str, str]

    @classmethod
    def from_root(cls, root: Path) -> "NativeGraphClosureV1":
        root = Path(root).resolve(strict=True)
        files: dict[str, str] = {}
        for name in _REQUIRED_FILES:
            path = root / name
            if not path.is_file() or path.is_symlink():
                raise ProtocolError("native_closure_unavailable")
            files[name] = sha256(path.read_bytes())
        return cls(root, files)

    @property
    def manifest(self) -> dict[str, Any]:
        records = [{"path": name, "digest": self.files[name]} for name in _REQUIRED_FILES]
        body = {"schema": "NativeGraphClosureV1", "files": records}
        body["closure_digest"] = object_hash(body, "closure_digest")
        return body

    @property
    def closure_digest(self) -> str:
        return self.manifest["closure_digest"]

    def validate(self) -> None:
        if set(self.files) != set(_REQUIRED_FILES):
            raise ProtocolError("native_closure_unavailable")
        for name in _REQUIRED_FILES:
            path = self.root / name
            try:
                resolved = path.resolve(strict=True)
            except OSError as exc:
                raise ProtocolError("native_closure_unavailable") from exc
            if resolved != path or not path.is_file() or path.is_symlink() or sha256(path.read_bytes()) != self.files[name]:
                raise ProtocolError("native_closure_unavailable")


@dataclass(frozen=True)
class NativeGraphCapture:
    native_graph_export: bytes
    native_graph_export_attestation: dict[str, Any]
    closure_manifest: dict[str, Any]


# This string is deliberately self-contained so each pass has a new Python
# process, module table, ``substrate_rs.Substrate`` and native runtime state.
_RECONSTRUCT = r'''
import json, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve(strict=True)
sys.path.insert(0, str(root))
import substrate_rs
seed_bytes = (root / "native_graph_proposal_seed.json").read_bytes()
facts_bytes = (root / "native_sealed_graph_action_fact.json").read_bytes()
seed = json.loads(seed_bytes)
facts = json.loads(facts_bytes)
s = substrate_rs.Substrate()
root_node = s.add_node(facts["root_type"], facts["root_attrs"])
fact = s.add_node("SealedGraphActionFactV1", facts["proposal"])
s.add_edge_unchecked(root_node, facts["edge_type"], fact)
s.load_seed_manifest(seed)
steps = s.tick(16)
if steps >= 16:
    raise RuntimeError("native fixed point exhausted")
nodes = s.nodes("GraphActionProposalV1")
if len(nodes) != 1:
    raise RuntimeError("invalid native proposal count")
proposal = dict(s.node(nodes[0])["attrs"])
print(json.dumps({"proposal": proposal, "steps": steps,
                  "package": str(Path(substrate_rs.__file__).resolve()),
                  "native": str(Path(substrate_rs._native.__file__).resolve())},
                 sort_keys=True, separators=(",", ":")))
'''


def _proposal(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _PROPOSAL_FIELDS:
        raise ProtocolError("invalid_native_capture")
    if value.get("schema") != "GraphActionProposalV1" or not isinstance(value.get("proposal_id"), str):
        raise ProtocolError("invalid_native_capture")
    if value.get("proposal_digest") != object_hash(value, "proposal_digest"):
        raise ProtocolError("invalid_native_capture")
    if not isinstance(value.get("args"), dict) or not isinstance(value.get("input_refs"), list):
        raise ProtocolError("invalid_native_capture")
    source, budget = value.get("source"), value.get("requested_budget")
    if (not isinstance(source, dict) or set(source) != {"origin_rule_digest", "source_node_type", "source_content_digest", "graph_snapshot_digest"} or
            not isinstance(budget, dict) or set(budget) != {"wall_ms", "cpu_ms", "memory_bytes", "writes", "network_bytes"} or
            any(type(item) is not int or item < 0 for item in budget.values()) or
            value.get("kind") != "GraphCounterAdvanceV1" or value["args"].get("steps") not in range(101) or
            value.get("causal_parent_receipt_hash") is not None or type(value.get("graph_logical_time")) is not int or value["graph_logical_time"] < 0):
        raise ProtocolError("invalid_native_capture")
    return value


def _reconstruct(closure: NativeGraphClosureV1) -> dict[str, Any]:
    command = [sys.executable, "-I", "-c", _RECONSTRUCT, str(closure.root)]
    try:
        completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   check=False, close_fds=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProtocolError("native_closure_unavailable") from exc
    if completed.returncode:
        raise ProtocolError("invalid_native_capture")
    try:
        result = json.loads(completed.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid_native_capture") from exc
    package = str((closure.root / "substrate_rs/__init__.py").resolve())
    native = str((closure.root / "substrate_rs/_native.abi3.so").resolve())
    if not isinstance(result, dict) or result.get("package") != package or result.get("native") != native:
        raise ProtocolError("native_closure_unavailable")
    proposal = _proposal(result.get("proposal"))
    if result.get("steps") != 1:
        raise ProtocolError("invalid_native_capture")
    return proposal


def capture_native_graph(*, closure: NativeGraphClosureV1, run_id: str, agent_build_digest: str,
                         control_plane_digest: str, input_snapshot_digest: str, now_ms: int,
                         expires_at_unix_ms: int, signer, key_id: str,
                         capture_sequence: int = 0) -> NativeGraphCapture:
    """Run two fresh evaluator-native captures and sign only evaluator bytes."""
    closure.validate()
    facts_digest = closure.files["native_sealed_graph_action_fact.json"]
    if input_snapshot_digest != facts_digest or agent_build_digest != closure.closure_digest:
        raise ProtocolError("native_closure_unavailable")
    first, second = _reconstruct(closure), _reconstruct(closure)
    if canonical_bytes(first) != canonical_bytes(second):
        raise ProtocolError("native_capture_disagreement")
    evidence = [{"proposal_id": first["proposal_id"], "proposal_digest": first["proposal_digest"],
                 "proposal": first, "source": first["source"],
                 "causal_parent_receipt_hash": first["causal_parent_receipt_hash"],
                 "graph_logical_time": first["graph_logical_time"]}]
    export = {"schema": "NativeGraphEvidenceExportV1", "run_id": run_id,
              "input_snapshot_digest": input_snapshot_digest, "issued_at_unix_ms": now_ms,
              "expires_at_unix_ms": expires_at_unix_ms, "evidence": evidence}
    export["export_digest"] = object_hash(export, "export_digest")
    export_bytes = canonical_bytes(export)
    attestation = make_native_graph_export_attestation(
        export_bytes, run_id=run_id, agent_build_digest=agent_build_digest,
        control_plane_digest=control_plane_digest, input_snapshot_digest=input_snapshot_digest,
        capture_sequence=capture_sequence, captured_at_unix_ms=now_ms, signer=signer, key_id=key_id)
    return NativeGraphCapture(export_bytes, attestation, closure.manifest)
