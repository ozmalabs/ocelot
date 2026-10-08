#!/usr/bin/env python3
"""Independent gates for per-rule write attribution v1."""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
if os.environ.get("OCELot_NATIVE_IMPORT_ROOT"):
    sys.path.insert(0, os.environ["OCELot_NATIVE_IMPORT_ROOT"])
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_rule_write_attribution_v1_lock_20261002.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_rule_write_attribution_v1_20261002.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_sources() -> dict:
    from substrate_rs import _native
    paths = json.loads(LOCK.read_text())["sources"]["files"]
    return {
        "files": {name: sha(ROOT / name) for name in paths},
        "native_binary": {"path": str(Path(_native.__file__).resolve()),
                          "sha256": sha(Path(_native.__file__).resolve())},
    }


def median_pair(rows: list[dict], kind: str, arm: str) -> float:
    values = [worker["timings"][kind]["pairs"][i][arm]
              for worker in rows for i in range(len(worker["timings"][kind]["pairs"]))]
    return statistics.median(values) / 1e6


def main() -> int:
    lock = json.loads(LOCK.read_text())
    data = json.loads(CAPTURE.read_text())
    workers = data.get("workers", [])
    errors: list[str] = []
    if data.get("lock_sha256") != sha(LOCK):
        errors.append("lock hash mismatch")
    if data.get("schema") != "ThoughtexperimentRuleWriteAttributionV1Results":
        errors.append("capture schema mismatch")
    if len(workers) != lock["workers"]:
        errors.append("worker count mismatch")
    pids = [worker.get("pid") for worker in workers]
    if len(set(pids)) != len(pids):
        errors.append("workers did not use distinct processes")
    for worker in workers:
        index = worker.get("worker_index")
        if not worker.get("source_stable"):
            errors.append(f"worker {index}: source drift")
        if worker.get("sources_before") != lock["sources"] or worker.get("sources_after") != lock["sources"]:
            errors.append(f"worker {index}: source fingerprint differs from lock")
        fixtures = {fixture["kind"]: fixture for fixture in worker.get("fixtures", [])}
        if set(fixtures) != set(lock["fixtures"]):
            errors.append(f"worker {index}: fixture set mismatch")
        for kind, fixture in fixtures.items():
            if fixture["plain"] != fixture["traced"] or fixture["plain"] != fixture["exact"]:
                errors.append(f"worker {index}/{kind}: settlement status/progress/pass parity failed")
            for field in ("event_covers_exact_nodes", "event_covers_exact_edges",
                          "aggregate_covers_event_nodes", "aggregate_covers_event_edges"):
                if not fixture.get(field):
                    errors.append(f"worker {index}/{kind}: {field} failed")
            if fixture.get("dropped_events") != 0:
                errors.append(f"worker {index}/{kind}: event overflow")
            if not fixture.get("event_count"):
                errors.append(f"worker {index}/{kind}: no events")
            timing_rows = worker.get("timings", {}).get(kind, {}).get("pairs", [])
            if len(timing_rows) != lock["timing_pairs_per_fixture_worker"]:
                errors.append(f"worker {index}/{kind}: timing pair count mismatch")
            elif any(set(pair) != {"plain", "attributed"} or min(pair.values()) <= 0 for pair in timing_rows):
                errors.append(f"worker {index}/{kind}: malformed timing pair")
        overlap = fixtures.get("overlap_noop", {})
        if not {"writer_first", "writer_second"}.issubset(set(overlap.get("event_names", []))):
            errors.append(f"worker {index}: overlapping writer names absent")
        if overlap.get("no_progress_event_count", 0) < 1:
            errors.append(f"worker {index}: no-op attempt not observed")
    if current_sources() != lock["sources"]:
        errors.append("analyzer sees current source/native drift")
    summary = {"workers": len(workers), "unique_pids": len(set(pids)),
               "fixtures_per_worker": lock["fixtures"],
               "median_wall_ms": {}, "attributed_to_plain_ratio": {}}
    for kind in lock["fixtures"]:
        plain = median_pair(workers, kind, "plain")
        attributed = median_pair(workers, kind, "attributed")
        summary["median_wall_ms"][kind] = {"plain": plain, "attributed": attributed}
        summary["attributed_to_plain_ratio"][kind] = attributed / plain if plain else None
    result = {"schema": "ThoughtexperimentRuleWriteAttributionV1Analysis",
              "gates_pass": not errors, "errors": errors, "summary": summary}
    out = CAPTURE.with_name("thoughtexperiment_rule_write_attribution_v1_analysis_20261002.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
