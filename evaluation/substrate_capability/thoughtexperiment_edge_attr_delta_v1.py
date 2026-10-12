#!/usr/bin/env python3
"""Source-locked edge-attribute diff/adoption and conflict probe."""
from __future__ import annotations

import copy, hashlib, json, os, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_edge_attr_delta_v1.py",
    "runners/dsl/src/persist.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/src/graph.rs", "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "domains/imagination.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
RAW = ROOT / "evaluation/reports/thoughtexperiment_edge_attr_delta_v1.json"

def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def worker():
    from substrate_rs import Substrate
    sub = Substrate()
    before = {
        "nodes": [
            {"id": 0, "type": "Item", "attrs": {}},
            {"id": 1, "type": "Item", "attrs": {}},
            {"id": 2, "type": "Item", "attrs": {}},
        ],
        "edges": [
            {"src": 0, "type": "keeps", "tgt": 1,
             "attrs": {"stable": "yes", "change": "old", "remove": 9}},
            {"src": 1, "type": "drops", "tgt": 2, "attrs": {"gone": True}},
        ],
    }
    after = {
        "nodes": copy.deepcopy(before["nodes"]),
        "edges": [
            {"src": 0, "type": "keeps", "tgt": 1,
             "attrs": {"stable": "yes", "change": "new", "added": 42}},
            {"src": 0, "type": "adds", "tgt": 2,
             "attrs": {"born": "with-edge", "weight": 3.5}},
        ],
    }
    sub.graph_from_dict(before)
    revision = tuple(sub.experiment_graph_rule_revision())
    diff = sub._inner.graph_diff(before, after)
    before_image = copy.deepcopy(diff)
    if not diff.get("edges_changed"):
        raise AssertionError("edge attribute edit did not produce edges_changed")
    sub.begin_experiment_delta_journal()
    sub.checkpoint_experiment_delta_journal()
    sub.apply_experiment_graph_delta(revision, diff)
    journal = sub.finish_experiment_delta_journal()
    adopted = sub.graph_to_dict()
    exact = adopted["nodes"] == after["nodes"] and sorted(adopted["edges"], key=lambda e: (e["src"],e["type"],e["tgt"])) == sorted(after["edges"], key=lambda e: (e["src"],e["type"],e["tgt"]))
    journal_exact = journal["conclusions"] == diff and journal["derived_only"] == diff

    rejected = Substrate()
    rejected.graph_from_dict(before)
    bad_revision = tuple(rejected.experiment_graph_rule_revision())
    malformed = copy.deepcopy(diff)
    malformed["edges_changed"][0]["attrs_before"]["change"] = "wrong-before-image"
    unchanged_before = rejected.graph_to_dict()
    error = None
    try:
        rejected.apply_experiment_graph_delta(bad_revision, malformed)
    except RuntimeError as exc:
        error = str(exc)
    unchanged_after = rejected.graph_to_dict()
    return {
        "pid": os.getpid(), "edge_diff_counts": {k: len(diff[k]) for k in
            ("edges_added", "edges_removed", "edges_changed")},
        "exact_adoption": exact,
        "journal_edge_attr_round_trip": journal_exact,
        "journal": journal,
        "malformed_rejected": bool(error and "before-image" in error),
        "unchanged_on_rejection": unchanged_before == unchanged_after,
        "error": error,
        "diff": before_image,
    }

def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--worker":
        print(json.dumps(worker(), sort_keys=True, separators=(",", ":")))
        return 0
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    rows = []
    for _ in range(5):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
            cwd=ROOT, text=True, capture_output=True)
        if proc.returncode:
            raise SystemExit(proc.stderr[-4000:])
        rows.append(json.loads(proc.stdout))
    import substrate_rs as srs
    binary = Path(srs._native.__file__).resolve()
    capture = {
        "schema": "ThoughtexperimentEdgeAttrDeltaCaptureV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(), "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "source_sha256": {path: sha_file(ROOT / path) for path in SOURCES},
        "binary": {"path": str(binary), "sha256": sha_file(binary)},
        "workers": rows,
        "checks": {
            "five_fresh_workers": len(rows) == 5 and len({r["pid"] for r in rows}) == 5,
            "exact_adoption": all(r["exact_adoption"] for r in rows),
            "journal_edge_attr_round_trip": all(r["journal_edge_attr_round_trip"] for r in rows),
            "malformed_rejected": all(r["malformed_rejected"] for r in rows),
            "unchanged_on_rejection": all(r["unchanged_on_rejection"] for r in rows),
            "all_edge_delta_kinds": all(r["edge_diff_counts"] == {"edges_added": 1, "edges_removed": 1, "edges_changed": 1} for r in rows),
        },
    }
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps(capture["checks"], indent=2, sort_keys=True))
    if not all(capture["checks"].values()):
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
