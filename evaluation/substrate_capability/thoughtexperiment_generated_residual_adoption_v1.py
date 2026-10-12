#!/usr/bin/env python3
"""Rule-generated thoughtexperiment residuals vs independent full-graph oracle."""
from __future__ import annotations

import hashlib, json, os, platform, random, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
SEEDS = tuple(range(88001, 88011))
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_generated_residual_adoption_v1.py",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_GENERATED_RESIDUAL_ADOPTION_V1_PREREG_20261001.md",
    "domains/imagination.py", "domains/commitment_gate.py", "domains/shape_tube.py",
    "runners/dsl/src/persist.rs", "runners/dsl/src/graph.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
RAW = ROOT / "evaluation/reports/thoughtexperiment_generated_residual_adoption_v1.json"

def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def make_case(seed: int):
    from substrate_rs import Substrate
    from substrate_rs.ext import add_rule
    rng = random.Random(seed)
    sub = Substrate()
    nodes = [sub.add_node("Base", {"ordinal": i, "value": rng.randrange(1000)})
             for i in range(48)]
    fact, peer, doomed = nodes[:3]
    sub.add_edge_unchecked(fact, "link", peer, {"seed": seed, "weight": rng.randrange(20)})
    sub.add_edge_unchecked(fact, "cascade", doomed, {"cause": "stale", "seed": seed})
    for ordinal in range(100):
        src, tgt = rng.randrange(3, 48), rng.randrange(3, 48)
        if src != tgt:
            sub.add_edge_unchecked(nodes[src], rng.choice(("context", "supports")),
                                   nodes[tgt], {"ordinal": ordinal, "seed": seed})
    changed = rng.randrange(10000, 20000)
    derived_value = rng.randrange(1000, 2000)
    add_rule(sub, f"generated_mixed_rule_{seed}",
        [("h", "tests", "f"), ("f", "link", "g"), ("f", "cascade", "z")],
        [["set_attr", "f", "generated_value", changed],
         ["del_edge", "f", "link", "g"],
         ["add_node", "n", "Derived", {"seed": seed, "value": derived_value}],
         ["add_edge", "f", "derived", "n", {"seed": seed, "confidence": 0.75}],
         ["del_node", "z"]])
    return sub, fact, peer, doomed, changed, derived_value

def semantic_projection(graph: dict, keep_ids: set[int]) -> dict:
    nodes = [node for node in graph["nodes"] if int(node["id"]) in keep_ids]
    edges = [edge for edge in graph["edges"]
             if int(edge["src"]) in keep_ids and int(edge["tgt"]) in keep_ids]
    return {"nodes": sorted(nodes, key=lambda n: int(n["id"])),
            "edges": sorted(edges, key=lambda e:
                (int(e["src"]), e["type"], int(e["tgt"]))) }

def apply_oracle(base: dict, *, fact: int, peer: int, doomed: int,
                 changed: int, derived_id: int, derived_value: int, seed: int) -> dict:
    nodes = {int(row["id"]): json.loads(json.dumps(row)) for row in base["nodes"]}
    edges = {(int(row["src"]), row["type"], int(row["tgt"])):
             json.loads(json.dumps(row)) for row in base["edges"]}
    nodes[fact]["attrs"]["generated_value"] = changed
    edges.pop((fact, "link", peer))
    for key in list(edges):
        if doomed in (key[0], key[2]):
            edges.pop(key)
    nodes.pop(doomed)
    nodes[derived_id] = {"id": derived_id, "type": "Derived",
                         "attrs": {"seed": seed, "value": derived_value}}
    key = (fact, "derived", derived_id)
    edges[key] = {"src": fact, "type": "derived", "tgt": derived_id,
                  "attrs": {"seed": seed, "confidence": 0.75}}
    return {"nodes": sorted(nodes.values(), key=lambda n: int(n["id"])),
            "edges": sorted(edges.values(), key=lambda e:
                (int(e["src"]), e["type"], int(e["tgt"]))) }

def worker() -> dict:
    from domains.imagination import imagine, reground, commit_imagination
    from domains.shape_tube import goal_manifold, goal_projection
    projections = {
        "commit": goal_projection("generated", active=True, action_count=1, intervention_magnitude=1.0),
        "wait": goal_projection("generated", active=False, action_count=0, intervention_magnitude=0.0),
        "refine": goal_projection("generated", active=False, action_count=1, intervention_magnitude=0.5),
    }
    manifold = goal_manifold("generated")
    rows = []
    for seed in SEEDS:
        sub, fact, peer, doomed, changed, derived_value = make_case(seed)
        base = sub._inner.graph_to_dict()
        base_ids = {int(node["id"]) for node in base["nodes"]}
        hypothesis = {"nodes": [{"key": "h", "type": "Hypothesis",
            "attrs": {"seed": seed, "proposal": "generated-mixed-residual"}}],
            "edges": [{"src": "h", "type": "tests", "tgt": fact.value}]}
        result = imagine(sub, focus_nodes=[fact], focus_hops=2, hypothesis=hypothesis,
            steps=8, cut_grounding=False, snapshot_backend="native_reusable_snapshot",
            record_trace=True)
        base_projection = semantic_projection(base, base_ids)
        trace_isolated = semantic_projection(sub._inner.graph_to_dict(), base_ids) == base_projection
        kinds = [sub.node(cid)["attrs"].get("kind") for cid in result.conclusion_nodes]
        regrounded = reground(sub, result)
        refused = commit_imagination(sub, result, regrounded["survivors"])
        refusal_preserved = semantic_projection(sub._inner.graph_to_dict(), base_ids) == base_projection
        approved = commit_imagination(sub, result, regrounded["survivors"],
            approver="generated-oracle-reviewer", projections=projections, manifold=manifold)
        added = next((row["node"] for row in approved["written"]
                      if row["kind"] == "node_added"), None)
        expected = apply_oracle(base, fact=fact.value, peer=peer.value, doomed=doomed.value,
            changed=changed, derived_id=added.value if added else -1,
            derived_value=derived_value, seed=seed)
        keep_ids = {int(node["id"]) for node in expected["nodes"]}
        observed = semantic_projection(sub._inner.graph_to_dict(), keep_ids | base_ids)
        expected_kinds = {"node_changed", "node_added", "edge_added", "edge_removed", "node_removed"}
        written_kinds = {row["kind"] for row in approved["written"]}
        rows.append({"seed": seed, "trace_isolated": trace_isolated,
            "generated_kinds_present": expected_kinds.issubset(set(kinds)),
            "default_gate_refused": refused["gate"].get("allowed") is False and not refused["written"],
            "refusal_preserved_semantic_graph": refusal_preserved,
            "approved_gate_allowed": approved["gate"].get("allowed") is True,
            "approved_writeback_applied": approved.get("writeback", {}).get("applied") is True,
            "all_expected_kinds_written": expected_kinds.issubset(written_kinds),
            "full_graph_oracle_parity": observed == expected,
            "conclusion_count": len(result.conclusion_nodes),
            "receipt_counts": {key: len(result.conclusions.get(key, [])) for key in
                ("nodes_added", "nodes_changed", "nodes_removed", "edges_added", "edges_changed", "edges_removed")}})
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
    capture = {"schema": "ThoughtexperimentGeneratedResidualAdoptionV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "source_sha256": {name: sha_file(ROOT / name) for name in SOURCES},
        "binary": {"path": str(binary), "sha256": sha_file(binary)},
        "worker_count": len(workers), "workers": workers, "trials": rows,
        "checks": {"five_fresh_workers": len({w["pid"] for w in workers}) == 5,
            "fifty_generated_trials": len(rows) == 50,
            "all_rehearsals_isolated": all(r["trace_isolated"] for r in rows),
            "all_default_gates_refused": all(r["default_gate_refused"] for r in rows),
            "all_refusals_preserved_graph": all(r["refusal_preserved_semantic_graph"] for r in rows),
            "all_approved_writebacks_applied": all(r["approved_writeback_applied"] for r in rows),
            "all_full_graph_oracles_match": all(r["full_graph_oracle_parity"] for r in rows),
            "generated_effect_kinds_present": all(r["generated_kinds_present"] for r in rows)}}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps(capture["checks"], indent=2, sort_keys=True))
    return 0 if all(capture["checks"].values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
