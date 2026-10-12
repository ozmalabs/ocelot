#!/usr/bin/env python3
"""Randomized mixed graph writeback against an independent full-graph oracle."""
from __future__ import annotations

import copy, hashlib, json, os, platform, random, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
SEEDS = tuple(range(74001, 74011))
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_mixed_receipt_oracle_v1.py",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_MIXED_RECEIPT_ORACLE_V1_PREREG_20261001.md",
    "domains/imagination.py", "domains/commitment_gate.py", "domains/shape_tube.py",
    "runners/dsl/src/persist.rs", "runners/dsl/src/graph.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
RAW = ROOT / "evaluation/reports/thoughtexperiment_mixed_receipt_oracle_v1.json"
INFRA_TYPES = {"Imagination", "ImaginedConclusion", "Commitment", "CommitDecision",
    "CommitOption", "ManifoldProjection", "NativeInformationCommitmentReceipt"}

def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def build_trial(seed: int):
    from substrate_rs import NodeID, Substrate
    from domains.imagination import DetachedCollapse
    rng = random.Random(seed)
    sub = Substrate()
    node_count = 64
    nodes = [sub.add_node("Base", {"ordinal": i, "value": rng.randrange(1000)})
             for i in range(node_count)]
    node_model = {n.value: dict(sub.node(n)["attrs"]) for n in nodes}
    edge_model = {}
    while len(edge_model) < 180:
        src, tgt = rng.randrange(node_count), rng.randrange(node_count)
        if src == tgt:
            continue
        edge_type = rng.choice(("link", "aux"))
        key = (src, edge_type, tgt)
        if key in edge_model:
            continue
        attrs = {"weight": rng.randrange(100), "salt": rng.randrange(10000)}
        edge_model[key] = attrs
        sub.add_edge_unchecked(nodes[src], edge_type, nodes[tgt], attrs)
    incident = {i: [] for i in range(node_count)}
    for (src, edge_type, tgt), attrs in edge_model.items():
        row = {"src": src, "type": edge_type, "tgt": tgt, "attrs": dict(attrs)}
        incident[src].append(row)
        incident[tgt].append(row)
    doomed = rng.choice([i for i in range(node_count) if incident[i]])
    available_edges = [key for key in edge_model if doomed not in (key[0], key[2])]
    changed_edge, removed_edge = rng.sample(available_edges, 2)
    changed_node = rng.choice([i for i in range(node_count) if i != doomed])
    new_detached_id = max(node_model) + 1000
    new_attrs = {"origin": "random-mixed", "seed": seed}
    changed_after = rng.randrange(100000, 200000)
    changed_edge_after = {"weight": rng.randrange(100), "committed_seed": seed}

    # Independent expected post-state for the semantic graph.
    expected_nodes = {nid: {"id": nid, "type": "Base", "attrs": dict(attrs)}
                      for nid, attrs in node_model.items()}
    expected_edges = {key: {"src": key[0], "type": key[1], "tgt": key[2], "attrs": dict(attrs)}
                      for key, attrs in edge_model.items()}

    imagination = sub.add_node("Imagination", {"status": "imagining"})
    conclusion_ids = []
    def conclusion(attrs):
        cid = sub.add_node("ImaginedConclusion", attrs)
        conclusion_ids.append(cid)
        return cid

    conclusion({"kind": "node_changed", "detached_id": changed_node,
        "attrs_before": {"value": node_model[changed_node]["value"]},
        "attrs_after": {"value": changed_after}, "status": "pending", "reason": ""})
    conclusion({"kind": "node_added", "detached_id": new_detached_id,
        "node_type": "Derived", "attrs": new_attrs, "status": "pending", "reason": ""})
    conclusion({"kind": "edge_added", "src": changed_node, "edge_type": "derived",
        "tgt": new_detached_id, "attrs": {"seed": seed}, "status": "pending", "reason": ""})
    before_edge_attrs = dict(edge_model[changed_edge])
    conclusion({"kind": "edge_changed", "src": changed_edge[0], "edge_type": changed_edge[1],
        "tgt": changed_edge[2], "attrs_before": before_edge_attrs,
        "attrs_after": changed_edge_after, "status": "pending", "reason": ""})
    conclusion({"kind": "edge_removed", "src": removed_edge[0], "edge_type": removed_edge[1],
        "tgt": removed_edge[2], "attrs_before": dict(edge_model[removed_edge]),
        "status": "pending", "reason": ""})
    conclusion({"kind": "node_removed", "detached_id": doomed, "node_type_before": "Base",
        "attrs_before": dict(node_model[doomed]),
        "incident_edges_before": sorted(incident[doomed],
            key=lambda e: (e["src"], e["type"], e["tgt"])),
        "status": "pending", "reason": ""})

    # Apply the same intended delta to the independent oracle.
    expected_nodes[changed_node]["attrs"]["value"] = changed_after
    expected_nodes[new_detached_id] = {"id": new_detached_id, "type": "Derived", "attrs": new_attrs}
    for key in list(expected_edges):
        if key == removed_edge or doomed in (key[0], key[2]):
            expected_edges.pop(key)
    attrs = expected_edges[changed_edge]["attrs"]
    for key in before_edge_attrs.keys() - changed_edge_after.keys():
        attrs.pop(key, None)
    attrs.update(changed_edge_after)
    expected_edges[(changed_node, "derived", new_detached_id)] = {
        "src": changed_node, "type": "derived", "tgt": new_detached_id,
        "attrs": {"seed": seed}}
    expected_nodes.pop(doomed)

    detached = DetachedCollapse(detached=None, imagination_node=imagination,
        conclusion_nodes=conclusion_ids, focus_nodes=None, hypothesis=None, hyp_map={},
        cut_grounding=False, grounding_cut_count=0, steps_run=0, steps_budget=0,
        converged=True, conclusions={}, derived_only={}, n_conclusions=len(conclusion_ids),
        residual=0.0, confidence=1.0, phase_timings_ms={})
    return sub, detached, expected_nodes, expected_edges, {
        "changed_node": changed_node, "new_detached_id": new_detached_id,
        "new_attrs": new_attrs, "changed_edge": changed_edge,
        "removed_edge": removed_edge, "doomed": doomed,
        "node_changed": changed_after, "edge_changed": changed_edge_after,
    }

def semantic_projection(graph: dict, keep_ids: set[int]) -> dict:
    nodes = [copy.deepcopy(node) for node in graph["nodes"] if int(node["id"]) in keep_ids]
    edges = [copy.deepcopy(edge) for edge in graph["edges"]
             if int(edge["src"]) in keep_ids and int(edge["tgt"]) in keep_ids]
    return {"nodes": sorted(nodes, key=lambda n: int(n["id"])),
            "edges": sorted(edges, key=lambda e:
                (int(e["src"]), e["type"], int(e["tgt"]))) }

def worker() -> dict:
    from domains.imagination import commit_imagination, reground
    from domains.shape_tube import goal_manifold, goal_projection
    projections = {
        "commit": goal_projection("mixed", active=True, action_count=1, intervention_magnitude=1.0),
        "wait": goal_projection("mixed", active=False, action_count=0, intervention_magnitude=0.0),
        "refine": goal_projection("mixed", active=False, action_count=1, intervention_magnitude=0.5),
    }
    manifold = goal_manifold("mixed")
    rows = []
    for seed in SEEDS:
        sub, detached, expected_nodes, expected_edges, spec = build_trial(seed)
        base = sub._inner.graph_to_dict()
        base_ids = {int(node["id"]) for node in base["nodes"] if node["type"] == "Base"}
        regrounded = reground(sub, detached)
        approved = commit_imagination(sub, detached, regrounded["survivors"],
            approver="oracle-reviewer", projections=projections, manifold=manifold)
        added_written = next(row["node"] for row in approved["written"]
                             if row["kind"] == "node_added")
        expected_nodes.pop(spec["new_detached_id"])
        expected_nodes[int(added_written.value)] = {"id": int(added_written.value),
            "type": "Derived", "attrs": spec["new_attrs"]}
        expected_edges.pop((spec["changed_node"], "derived", spec["new_detached_id"]))
        expected_edges[(spec["changed_node"], "derived", int(added_written.value))] = {
            "src": spec["changed_node"], "type": "derived", "tgt": int(added_written.value),
            "attrs": {"seed": seed}}
        expected = {"nodes": sorted(expected_nodes.values(), key=lambda n: n["id"]),
                    "edges": sorted(expected_edges.values(), key=lambda e:
                        (e["src"], e["type"], e["tgt"]))}
        keep_ids = set(expected_nodes)
        observed = semantic_projection(sub._inner.graph_to_dict(), keep_ids | base_ids)
        kinds = {row["kind"] for row in approved["written"]}
        positive_ok = (approved["gate"].get("allowed") is True
            and approved.get("writeback", {}).get("applied") is True
            and {"node_changed", "node_added", "edge_added", "edge_changed",
                 "edge_removed", "node_removed"}.issubset(kinds)
            and observed == expected)

        # Conflict arm: a fresh graph, then alter the edge after reground.
        stale_sub, stale_detached, _, _, stale_spec = build_trial(seed + 100000)
        stale_before = stale_sub._inner.graph_to_dict()
        stale_base_ids = {int(node["id"]) for node in stale_before["nodes"]
                          if node["type"] == "Base"}
        stale_reground = reground(stale_sub, stale_detached)
        ek = stale_spec["changed_edge"]
        stale_sub.add_edge_unchecked(__import__("substrate_rs").NodeID(ek[0]), ek[1],
            __import__("substrate_rs").NodeID(ek[2]), {"weight": 999999, "late_conflict": True})
        conflict_base = stale_sub._inner.graph_to_dict()
        rejected = commit_imagination(stale_sub, stale_detached, stale_reground["survivors"],
            approver="oracle-reviewer", projections=projections, manifold=manifold)
        observed_conflict = semantic_projection(stale_sub._inner.graph_to_dict(), stale_base_ids)
        expected_conflict = semantic_projection(conflict_base, stale_base_ids)
        conflict_ok = (rejected["gate"].get("allowed") is False
            and rejected["gate"].get("reason") == "stale_conclusion_before_image"
            and not rejected["written"] and observed_conflict == expected_conflict)
        rows.append({"seed": seed, "positive_full_graph_oracle": positive_ok,
            "positive_operation_kinds": sorted(kinds), "positive_gate_allowed": approved["gate"].get("allowed"),
            "positive_writeback_applied": approved.get("writeback", {}).get("applied"),
            "conflict_refused": conflict_ok,
            "expected_node_count": len(expected_nodes), "expected_edge_count": len(expected_edges)})
    return {"pid": os.getpid(), "rows": rows}

def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--worker":
        print(json.dumps(worker(), sort_keys=True, separators=(",", ":")))
        return 0
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    workers = []
    for _ in range(5):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
            cwd=ROOT, text=True, capture_output=True)
        if proc.returncode:
            raise SystemExit(proc.stderr[-5000:])
        workers.append(json.loads(proc.stdout))
    rows = [row for worker_row in workers for row in worker_row["rows"]]
    import substrate_rs as srs
    binary = Path(srs._native.__file__).resolve()
    capture = {"schema": "ThoughtexperimentMixedReceiptOracleV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "source_sha256": {name: sha_file(ROOT / name) for name in SOURCES},
        "binary": {"path": str(binary), "sha256": sha_file(binary)},
        "worker_count": len(workers), "workers": workers, "trials": rows,
        "checks": {"five_fresh_workers": len({w["pid"] for w in workers}) == 5,
            "fifty_trials": len(rows) == 50,
            "all_positive_full_graph_oracles_pass": all(r["positive_full_graph_oracle"] for r in rows),
            "all_conflict_arms_refused_without_writes": all(r["conflict_refused"] for r in rows),
            "all_mixed_operation_kinds_covered": all(len(r["positive_operation_kinds"]) == 6 for r in rows)}}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps(capture["checks"], indent=2, sort_keys=True))
    return 0 if all(capture["checks"].values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
