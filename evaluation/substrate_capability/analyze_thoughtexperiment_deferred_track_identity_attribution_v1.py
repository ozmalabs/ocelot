#!/usr/bin/env python3
"""Independent gates for deferred TrackIdentity origin attribution v1."""
from __future__ import annotations

import hashlib, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
if os.environ.get("OCELot_NATIVE_IMPORT_ROOT"):
    sys.path.insert(0, os.environ["OCELot_NATIVE_IMPORT_ROOT"])
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_deferred_track_identity_attribution_v1_lock_20261002.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_deferred_track_identity_attribution_v1_20261002.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources() -> dict:
    from substrate_rs import _native
    locked = json.loads(LOCK.read_text())["sources"]
    binary = Path(_native.__file__).resolve()
    return {"files": {name: sha(ROOT / name) for name in locked["files"]},
            "native_binary": {"path": str(binary), "sha256": sha(binary)}}


def main() -> int:
    lock = json.loads(LOCK.read_text()); capture = json.loads(CAPTURE.read_text())
    workers = capture.get("workers", []); errors = []
    if capture.get("lock_sha256") != sha(LOCK): errors.append("lock hash mismatch")
    if len(workers) != lock["workers"]: errors.append("worker count mismatch")
    if len({worker.get("pid") for worker in workers}) != len(workers): errors.append("worker PIDs are not distinct")
    for worker in workers:
        idx = worker.get("worker_index"); result = worker.get("result", {})
        if not worker.get("source_stable") or worker.get("sources_before") != lock["sources"] or worker.get("sources_after") != lock["sources"]:
            errors.append(f"worker {idx}: source/native fingerprint mismatch")
        if not (result.get("plain") == result.get("traced") == result.get("exact")):
            errors.append(f"worker {idx}: settlement status/progress/pass parity failed")
        for field in ("event_covers_exact_nodes", "event_covers_exact_edges",
                      "aggregate_covers_event_nodes", "aggregate_covers_event_edges",
                      "producer_covers_changed_percepts"):
            if not result.get(field): errors.append(f"worker {idx}: {field} failed")
        if result.get("dropped_events") != 0: errors.append(f"worker {idx}: trace events dropped")
        producer = result.get("producer_events", [])
        if not producer: errors.append(f"worker {idx}: originating deferred rule absent")
        elif any(not event.get("deferred") for event in producer): errors.append(f"worker {idx}: origin event not marked deferred")
        direct = result.get("direct_control_events", [])
        if not direct: errors.append(f"worker {idx}: direct control rule absent")
        elif any(event.get("deferred") for event in direct): errors.append(f"worker {idx}: direct event mislabeled deferred")
        if len(result.get("changed_percept_ids", [])) != 5:
            errors.append(f"worker {idx}: exact oracle did not change all five percept nodes")
    if sources() != lock["sources"]: errors.append("analyzer sees source/native drift")
    summary = {"workers": len(workers), "unique_pids": len({worker.get("pid") for worker in workers}),
               "deferred_origin_events": sum(len(w["result"].get("producer_events", [])) for w in workers),
               "direct_control_events": sum(len(w["result"].get("direct_control_events", [])) for w in workers),
               "all_five_percept_writes_reconciled": all(len(w["result"].get("changed_percept_ids", [])) == 5 and w["result"].get("producer_covers_changed_percepts") for w in workers)}
    result = {"schema": "DeferredTrackIdentityAttributionV1Analysis", "gates_pass": not errors,
              "errors": errors, "summary": summary}
    out = CAPTURE.with_name("thoughtexperiment_deferred_track_identity_attribution_v1_analysis_20261002.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__": raise SystemExit(main())
