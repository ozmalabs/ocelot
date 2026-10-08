#!/usr/bin/env python3
"""Source-locked assumption-preserving Thoughtexperiment commit probe."""
from __future__ import annotations

import hashlib, json, os, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_epistemic_commit_v1.py",
    "domains/imagination.py", "domains/commitment_gate.py", "domains/shape_tube.py",
    "runners/dsl/src/py.rs", "runners/dsl/src/persist.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
RAW = ROOT / "evaluation/reports/thoughtexperiment_epistemic_commit_v1.json"

def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def fixture():
    from substrate_rs import Substrate
    sub = Substrate()
    sub.add_node("Rule", {
        "id": "hypothesis_updates_edge_attrs",
        "match": [["h", "tests", "f"], ["f", "state", "z"]],
        "effect": [["add_edge", "f", "state", "z", {"mode": "imagined", "added": 8}]],
    })
    fact = sub.add_node("Fact", {"label": "f"})
    target = sub.add_node("State", {})
    sub.add_edge_unchecked(fact, "state", target, {"mode": "old", "keep": True})
    return sub, fact, target

def imagine_once(sub, fact):
    from domains.imagination import imagine
    hypothesis = {
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {"proposal": "edge-update"}}],
        "edges": [{"src": "h", "type": "tests", "tgt": fact.value,
                   "attrs": {"source": "assumed"}}],
    }
    result = imagine(sub, focus_nodes=[fact], focus_hops=2, hypothesis=hypothesis,
                     steps=4, cut_grounding=False,
                     snapshot_backend="native_reusable_snapshot", record_trace=True)
    return result, hypothesis

def worker() -> dict:
    from domains.imagination import commit_imagination, reground
    from domains.shape_tube import goal_manifold, goal_projection
    projections = {
        "commit": goal_projection("thoughtexperiment", active=True, action_count=1, intervention_magnitude=1.0),
        "wait": goal_projection("thoughtexperiment", active=False, action_count=0, intervention_magnitude=0.0),
        "refine": goal_projection("thoughtexperiment", active=False, action_count=1, intervention_magnitude=0.5),
    }
    manifold = goal_manifold("thoughtexperiment")

    sub, fact, target = fixture()
    before = sub.edge_attrs(fact, "state", target)
    result, hypothesis = imagine_once(sub, fact)
    trace = sub.node(result.imagination_node)["attrs"]
    kinds = [sub.node(cid)["attrs"].get("kind") for cid in result.conclusion_nodes]
    edge_rows = [sub.node(cid)["attrs"] for cid in result.conclusion_nodes
                 if sub.node(cid)["attrs"].get("kind") == "edge_changed"]
    assumption_ids = [sub.node(cid)["attrs"].get("detached_id") for cid in result.conclusion_nodes
                      if sub.node(cid)["attrs"].get("kind") == "assumption_added"]
    post_explore = sub.edge_attrs(fact, "state", target)
    raw_has_assumption = any(n.get("type") == "Hypothesis" for n in result.conclusions["nodes_added"])
    raw_has_assumption_edge = any(e.get("type") == "tests" for e in result.conclusions["edges_added"])
    regrounded = reground(sub, result)

    # Force a primary-side race after regrounding; commit must reject before
    # publishing the detached update and preserve the concurrent value.
    sub._inner.add_edge_unchecked(fact, "state", target, {"mode": "concurrent", "keep": True})
    stale = commit_imagination(sub, result, regrounded["survivors"], approver="experiment-reviewer",
        projections=projections, manifold=manifold)
    after_stale = sub.edge_attrs(fact, "state", target)

    # Restore the branch before-image and exercise fail-closed then approved
    # commit. Assumption records are retained in the trace but never written.
    sub._inner.add_edge_unchecked(fact, "state", target, before)
    refused = commit_imagination(sub, result, regrounded["survivors"])
    after_refusal = sub.edge_attrs(fact, "state", target)
    approved = commit_imagination(sub, result, regrounded["survivors"],
        approver="experiment-reviewer", projections=projections, manifold=manifold)
    after_approved = sub.edge_attrs(fact, "state", target)
    live_graph_after = sub.graph_to_dict()
    edge_record_status = next((sub.node(cid)["attrs"].get("status") for cid in result.conclusion_nodes
        if sub.node(cid)["attrs"].get("kind") == "edge_changed"), None)

    return {
        "pid": os.getpid(), "hypothesis_persisted": trace.get("hypothesis") == hypothesis,
        "assumption_records_present": bool(assumption_ids) and "assumption_added" in kinds and "assumption_edge_added" in kinds,
        "raw_receipt_contains_assumption": raw_has_assumption and raw_has_assumption_edge,
        "edge_change_record_present": len(edge_rows) == 1,
        "edge_change_before_after": bool(edge_rows and edge_rows[0].get("attrs_before")
            and edge_rows[0].get("attrs_after")),
        "live_unchanged_by_imagination": post_explore == before,
        "edge_change_survived_reground": any(item["kind"] == "edge_changed" and item["survived"]
            for item in regrounded["detail"]),
        "stale_commit_rejected": stale["gate"].get("reason") == "stale_edge_before_image" and not stale["written"],
        "concurrent_value_preserved": after_stale == {"mode": "concurrent", "keep": True},
        "default_commit_refused": not refused["gate"].get("allowed") and not refused["written"],
        "refusal_did_not_write_edge": after_refusal == before,
        "approved_commit_allowed": approved["gate"].get("allowed") and
            any(item["kind"] == "edge_changed" for item in approved["written"]),
        "approved_edge_attrs": after_approved,
        "assumptions_not_committed": not list(sub.nodes("Hypothesis")) and
            not any(edge.get("type") == "tests" for edge in live_graph_after["edges"]),
        "changed_edge_record_committed": edge_record_status == "committed",
        "conclusion_kinds": kinds,
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
    checks = {key: all(row[key] for row in rows) for key in rows[0] if key != "pid" and key != "approved_edge_attrs" and key != "conclusion_kinds"}
    checks["five_fresh_workers"] = len({row["pid"] for row in rows}) == 5
    checks["approved_edge_attrs_exact"] = all(row["approved_edge_attrs"] == {"mode": "imagined", "added": 8} for row in rows)
    capture = {
        "schema": "ThoughtexperimentEpistemicCommitCaptureV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(), "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "source_sha256": {path: sha_file(ROOT / path) for path in SOURCES},
        "binary": {"path": str(binary), "sha256": sha_file(binary)},
        "checks": checks, "workers": rows,
    }
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps(checks, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
