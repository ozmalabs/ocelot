#!/usr/bin/env python3
"""Source-locked deletion proposal, reground, and gated commit probe."""
from __future__ import annotations

import hashlib, json, os, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_deletion_commit_v1.py",
    "domains/imagination.py", "domains/commitment_gate.py", "domains/shape_tube.py",
    "runners/dsl/src/persist.rs", "runners/dsl/src/graph.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
RAW = ROOT / "evaluation/reports/thoughtexperiment_deletion_commit_v1.json"

def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def fixture():
    from substrate_rs import Substrate
    sub = Substrate()
    fact = sub.add_node("Fact", {"label": "f"})
    peer = sub.add_node("Peer", {})
    doomed = sub.add_node("Stale", {"version": 1, "note": "before"})
    sub.add_edge_unchecked(fact, "link", peer, {"confidence": 0.4, "source": "old"})
    sub.add_edge_unchecked(fact, "cascade", doomed, {"reason": "stale"})
    from substrate_rs.ext import add_rule
    add_rule(sub, "hypothesis_removes_stale_state",
        [("h", "tests", "f"), ("f", "link", "g"), ("f", "cascade", "z")],
        [["set_attr", "f", "mixed_commit_value", 2],
         ["del_edge", "f", "link", "g"],
         ["add_node", "n", "Derived", {"origin": "mixed-rule"}],
         ["add_edge", "f", "derived", "n"],
         ["del_node", "z"]])
    return sub, fact, peer, doomed

def explore(sub, fact):
    from domains.imagination import imagine
    hypothesis = {
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {"proposal": "remove-stale"}}],
        "edges": [{"src": "h", "type": "tests", "tgt": fact.value}],
    }
    result = imagine(sub, focus_nodes=[fact], focus_hops=2, hypothesis=hypothesis,
        steps=4, cut_grounding=False, snapshot_backend="native_reusable_snapshot", record_trace=True)
    return result

def worker() -> dict:
    from domains.imagination import commit_imagination, reground
    from domains.shape_tube import goal_manifold, goal_projection
    projections = {
        "commit": goal_projection("deletion", active=True, action_count=1, intervention_magnitude=1.0),
        "wait": goal_projection("deletion", active=False, action_count=0, intervention_magnitude=0.0),
        "refine": goal_projection("deletion", active=False, action_count=1, intervention_magnitude=0.5),
    }
    manifold = goal_manifold("deletion")

    sub, fact, peer, doomed = fixture()
    result = explore(sub, fact)
    kinds = [sub.node(cid)["attrs"].get("kind") for cid in result.conclusion_nodes]
    node_details = result.conclusions.get("nodes_removed_details", [])
    edge_details = result.conclusions.get("edges_removed_details", [])
    precommit = (sub.has_node(doomed) and sub.has_edge(fact, "link", peer)
                 and sub.node(fact)["attrs"].get("mixed_commit_value") is None)
    regrounded = reground(sub, result)
    reground_kinds = {item["kind"] for item in regrounded["detail"] if item["survived"]}

    refused = commit_imagination(sub, result, regrounded["survivors"])
    refused_unchanged = (sub.has_node(doomed) and sub.has_edge(fact, "link", peer)
                         and sub.node(fact)["attrs"].get("mixed_commit_value") is None)
    approved = commit_imagination(sub, result, regrounded["survivors"],
        approver="deletion-reviewer", projections=projections, manifold=manifold)
    derived_edges = [edge for edge in sub._inner.graph_to_dict()["edges"]
                     if edge["type"] == "derived" and edge["src"] == fact.value]
    committed = (not sub.has_node(doomed) and not sub.has_edge(fact, "link", peer)
                 and not sub.has_edge(fact, "cascade", doomed)
                 and sub.node(fact)["attrs"].get("mixed_commit_value") == 2
                 and len(derived_edges) == 1
                 and sub.node(type(fact)(derived_edges[0]["tgt"]))["type"] == "Derived")

    edge_stale_sub, edge_fact, edge_peer, edge_doomed = fixture()
    edge_stale = explore(edge_stale_sub, edge_fact)
    edge_survivors = reground(edge_stale_sub, edge_stale)["survivors"]
    edge_stale_sub._inner.add_edge_unchecked(edge_fact, "link", edge_peer,
        {"confidence": 0.9, "source": "concurrent"})
    edge_stale_result = commit_imagination(edge_stale_sub, edge_stale, edge_survivors,
        approver="deletion-reviewer", projections=projections, manifold=manifold)
    edge_conflict_preserved = (edge_stale_sub.has_node(edge_doomed)
        and edge_stale_sub.edge_attrs(edge_fact, "link", edge_peer) ==
            {"confidence": 0.9, "source": "concurrent"}
        and edge_stale_sub.node(edge_fact)["attrs"].get("mixed_commit_value") is None
        and not any(n["type"] == "Derived" for n in edge_stale_sub._inner.graph_to_dict()["nodes"]))

    node_stale_sub, node_fact, node_peer, node_doomed = fixture()
    node_stale = explore(node_stale_sub, node_fact)
    node_survivors = reground(node_stale_sub, node_stale)["survivors"]
    node_stale_sub.set_attr(node_doomed, "version", 2)
    node_stale_result = commit_imagination(node_stale_sub, node_stale, node_survivors,
        approver="deletion-reviewer", projections=projections, manifold=manifold)
    node_conflict_preserved = (node_stale_sub.has_node(node_doomed)
        and node_stale_sub.has_edge(node_fact, "link", node_peer)
        and node_stale_sub.node(node_doomed)["attrs"]["version"] == 2
        and node_stale_sub.node(node_fact)["attrs"].get("mixed_commit_value") is None
        and not any(n["type"] == "Derived" for n in node_stale_sub._inner.graph_to_dict()["nodes"]))

    fail_sub, fail_fact, fail_peer, fail_doomed = fixture()
    fail_result = explore(fail_sub, fail_fact)
    fail_survivors = reground(fail_sub, fail_result)["survivors"]
    native_type = type(fail_sub._inner)
    original_apply = native_type.apply_experiment_graph_delta
    def corrupt_batch_before_native_publish(native, revision, delta):
        if delta.get("nodes_removed_details"):
            delta["nodes_removed_details"][0]["attrs"] = {"version": 999}
        return original_apply(native, revision, delta)
    native_type.apply_experiment_graph_delta = corrupt_batch_before_native_publish
    try:
        fail_batch = commit_imagination(fail_sub, fail_result, fail_survivors,
            approver="deletion-reviewer", projections=projections, manifold=manifold)
    finally:
        native_type.apply_experiment_graph_delta = original_apply
    fail_batch_atomic = (fail_batch["gate"].get("allowed") is True
        and fail_batch.get("writeback", {}).get("reason") == "graph_batch_conflict"
        and not fail_batch["written"] and fail_sub.has_node(fail_doomed)
        and fail_sub.has_edge(fail_fact, "link", fail_peer)
        and fail_sub.node(fail_fact)["attrs"].get("mixed_commit_value") is None
        and not any(n["type"] == "Derived" for n in fail_sub._inner.graph_to_dict()["nodes"]))

    # Inject a competing writer after commit planning but before native
    # transaction entry; verify the integrated writeback path rejects it.
    race_sub, race_fact, race_peer, race_doomed = fixture()
    race_result = explore(race_sub, race_fact)
    race_survivors = reground(race_sub, race_result)["survivors"]
    native_type = type(race_sub._inner)
    original_apply = native_type.apply_experiment_graph_delta
    def inject_competing_writer(native, revision, delta):
        native.add_node("ConcurrentWriter", {"changed": True})
        return original_apply(native, revision, delta)
    native_type.apply_experiment_graph_delta = inject_competing_writer
    try:
        race_commit = commit_imagination(race_sub, race_result, race_survivors,
            approver="deletion-reviewer", projections=projections, manifold=manifold)
    finally:
        native_type.apply_experiment_graph_delta = original_apply
    race_after = race_sub._inner.graph_to_dict()
    race_rejected = (race_commit.get("writeback", {}).get("reason") == "graph_batch_conflict"
        and race_commit["gate"].get("allowed") is True
        and race_sub.has_node(race_doomed) and race_sub.has_edge(race_fact, "link", race_peer)
        and race_sub.node(race_fact)["attrs"].get("mixed_commit_value") is None
        and any(n["type"] == "ConcurrentWriter" for n in race_after["nodes"])
        and not any(n["type"] == "Derived" for n in race_after["nodes"]))

    failure_sub, failure_fact, failure_peer, failure_doomed = fixture()
    failure_delta = {
        "nodes_added": [], "nodes_changed": [], "nodes_removed": [failure_doomed.value],
        "edges_added": [], "edges_changed": [],
        "edges_removed": [{"src": failure_fact.value, "type": "link", "tgt": failure_peer.value}],
    }
    failure_delta["nodes_removed_details"] = [{"id": failure_doomed.value, "type": "Stale",
                                                "attrs": {"version": 999}}]
    failure_delta["edges_removed"] = [{"src": failure_fact.value, "type": "link",
                                        "tgt": failure_peer.value}]
    failure_delta["edges_removed_details"] = [{"src": failure_fact.value, "type": "link",
        "tgt": failure_peer.value, "attrs": {"confidence": 0.4, "source": "old"}}]
    failure_before = failure_sub._inner.graph_to_dict()
    try:
        failure_sub.apply_experiment_graph_delta(
            failure_sub.experiment_graph_rule_revision(), failure_delta)
        failure_error = None
    except RuntimeError as exc:
        failure_error = str(exc)
    failure_unchanged = failure_before == failure_sub._inner.graph_to_dict()

    return {
        "pid": os.getpid(),
        "before_images_present": bool(node_details and edge_details),
        "node_removed_proposal": "node_removed" in kinds,
        "edge_removed_proposal": "edge_removed" in kinds,
        "cascaded_edge_deduplicated": kinds.count("edge_removed") == 1,
        "live_unchanged_by_imagination": precommit,
        "deletions_regrounded": {"node_removed", "edge_removed"}.issubset(reground_kinds),
        "default_gate_refused": not refused["gate"].get("allowed") and not refused["written"],
        "refusal_kept_primary": refused_unchanged,
        "approved_gate_allowed": approved["gate"].get("allowed")
            and approved.get("writeback", {}).get("applied"),
        "approved_mixed_batch_committed": committed and
            {"node_removed", "edge_removed", "node_changed", "edge_added", "node_added"}
            .issubset({row["kind"] for row in approved["written"]}),
        "stale_edge_rejected": edge_stale_result["gate"].get("reason") == "stale_conclusion_before_image"
            and not edge_stale_result["written"],
        "stale_edge_no_partial_delete": edge_conflict_preserved,
        "stale_node_rejected": node_stale_result["gate"].get("reason") == "stale_conclusion_before_image"
            and not node_stale_result["written"],
        "stale_node_no_partial_delete": node_conflict_preserved,
        "mixed_late_failure_rejected_atomically": fail_batch_atomic,
        "concurrent_revision_rejected": race_rejected,
        "concurrent_write_preserved": race_rejected,
        "late_before_image_failure_rejected": bool(failure_error and "before-image attrs mismatch" in failure_error),
        "late_failure_kept_entire_batch": failure_unchanged,
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
    checks = {key: all(row[key] for row in rows) for key in rows[0] if key != "pid"}
    checks["five_fresh_workers"] = len({row["pid"] for row in rows}) == 5
    capture = {
        "schema": "ThoughtexperimentDeletionCommitCaptureV1",
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
