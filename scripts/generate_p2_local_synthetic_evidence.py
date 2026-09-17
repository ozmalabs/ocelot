#!/usr/bin/env python3
"""Regenerate local-only P2 320-study evidence through the native worker.

This is a reproducible development control, not a release evaluator. It uses a
fixed local seed/key and synthetic receipt commitments; its output must never be
presented as externally trusted P2-B1 release evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluation.p0a.canonical import canonical_bytes, object_hash, sha256
from evaluation.p2.study import STUDY_SIZE, materialize_held_out_study, score_held_out

DEFAULT_WORKER = ROOT / "runners" / "dsl" / "target" / "debug" / "p2_native_worker"
DEFAULT_OUTPUT = ROOT / "evaluation" / "p2" / "LOCAL_SYNTHETIC_320_EVIDENCE.json"
PATH = "P2BoundedFutureManifoldV1"


def worker_proposal(worker: Path, envelope: dict) -> dict:
    digest = sha256(canonical_bytes(envelope))
    request = canonical_bytes({"schema": "P2NativeWorkerRequestV1", "envelope": envelope,
                               "verified_input_digest": digest})
    result = subprocess.run([str(worker)], input=request, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            check=False, close_fds=True, timeout=3)
    if result.returncode:
        raise RuntimeError("local native worker rejected synthetic envelope")
    try:
        proposal = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("local native worker did not produce a proposal") from exc
    selection = proposal.get("selection")
    if not isinstance(selection, dict) or selection.get("selection_path") != PATH:
        raise RuntimeError("local native worker bypassed bounded future-manifold selection")
    selected, tie_set = selection.get("selected_action_id"), selection.get("native_tie_set")
    if selected is not None and (not isinstance(tie_set, list) or selected not in tie_set):
        raise RuntimeError("local native selection derivation missing")
    return proposal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=Path, default=DEFAULT_WORKER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    worker = args.worker.resolve(strict=True)
    if worker.is_symlink() or not worker.is_file():
        raise RuntimeError("local native worker unavailable")
    key = Ed25519PrivateKey.from_private_bytes(b"\x53" * 32)
    manifest, envelopes, truth = materialize_held_out_study(
        secret_seed=b"\x42" * 32, signing_key=key,
        run_id="local-synthetic-320-corrected-path-v1")
    proposals = {envelope["episode_id"]: worker_proposal(worker, envelope) for envelope in envelopes}
    receipts = {episode_id: object_hash({"schema": "P2LocalSyntheticReceiptV1", "episode_id": episode_id,
                                         "proposal_digest": proposal["proposal_digest"]})
                for episode_id, proposal in proposals.items()}
    scoring = score_held_out(manifest=manifest, truth=truth, proposals=proposals,
                             receipt_hashes=receipts, signer=key)
    route_counts = Counter(proposal["selection"]["selection_path"] for proposal in proposals.values())
    result = {
        "schema": "P2LocalSynthetic320EvidenceV1",
        "evidence_status": "local_synthetic_not_externally_trusted_release_evidence",
        "study_kind": "deterministic development control; no release lock, Podman custody, or receipt authority",
        "worker_binary_sha256": "sha256:" + hashlib.sha256(worker.read_bytes()).hexdigest(),
        "selection_path": PATH,
        "selection_path_counts": dict(sorted(route_counts.items())),
        "episode_count": STUDY_SIZE,
        "study_manifest": manifest,
        "synthetic_receipt_scheme": "P2LocalSyntheticReceiptV1 commitments; not signed release receipts",
        "scoring_evidence": scoring,
    }
    result["evidence_hash"] = object_hash(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(result))
    args.output.chmod(0o444)


if __name__ == "__main__":
    main()
