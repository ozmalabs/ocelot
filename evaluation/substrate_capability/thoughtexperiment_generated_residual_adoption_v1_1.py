#!/usr/bin/env python3
"""Rule-generated residual adoption across effects, scales, and apertures."""
from __future__ import annotations

import hashlib, json, os, platform, random, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
FAMILIES = ("attribute", "add", "mixed", "hub_delete")
SIZES = (64, 1000)
SEEDS = (91011, 91012, 91013)
WORKERS = 3
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_generated_residual_adoption_v1_1.py",
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_GENERATED_RESIDUAL_ADOPTION_V1_1_PREREG_20261001.md",
    "domains/imagination.py", "domains/commitment_gate.py", "domains/shape_tube.py",
    "runners/dsl/src/persist.rs", "runners/dsl/src/graph.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
RAW = ROOT / "evaluation/reports/thoughtexperiment_generated_residual_adoption_v1_1.json"


def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def make_case(family: str, size: int, seed: int):
    from substrate_rs import Substrate
    from substrate_rs.ext import add_rule
    rng = random.Random(seed + size * 17 + FAMILIES.index(family) * 100_003)
    sub = Substrate()
    nodes = [sub.add_node("Base", {"ordinal": i, "value": rng.randrange(1000)})
             for i in range(size)]
    fact, peer, target = nodes[:3]
    sub.add_edge_unchecked(fact, "link", peer,
                           {"seed": seed, "weight": rng.randrange(20)})
    hub_degree = 0
    if family == "hub_delete":
        sub.add_edge_unchecked(fact, "cascade", target,
                               {"cause": "stale", "seed": seed})
        for ix, spoke in enumerate(nodes[3:35]):
            sub.add_edge_unchecked(target, "spoke", spoke,
                                   {"seed": seed, "ordinal": ix})
            hub_degree += 1
        match = [("h", "tests", "f"), ("f", "cascade", "z")]
        effects = [["del_node", "z"]]
    else:
        # Context edges are outside the focus aperture and reproducible.
        for ordinal in range(2 * size):
            src, dst = rng.randrange(3, size), rng.randrange(3, size)
            if src != dst:
                sub.add_edge_unchecked(nodes[src], rng.choice(("context", "supports")),
                                       nodes[dst], {"ordinal": ordinal, "seed": seed})
        match = [("h", "tests", "f"), ("f", "link", "g")]
        if family == "attribute":
            effects = [["set_attr", "f", "generated_value", 10_000 + seed]]
        elif family == "add":
            effects = [["add_node", "n", "Derived", {"seed": seed, "value": size}],
                       ["add_edge", "f", "derived", "n", {"seed": seed}]]
        else:
            sub.add_edge_unchecked(fact, "cascade", target,
                                   {"cause": "stale", "seed": seed})
            match.append(("f", "cascade", "z"))
            effects = [["set_attr", "f", "generated_value", 10_000 + seed],
                       ["del_edge", "f", "link", "g"],
                       ["add_node", "n", "Derived", {"seed": seed, "value": size}],
                       ["add_edge", "f", "derived", "n", {"seed": seed}],
                       ["del_node", "z"]]
    add_rule(sub, f"generated_{family}_{size}_{seed}", match, effects)
    return sub, fact, peer, target, hub_degree, seed, family


def semantic_projection(graph: dict, keep_ids: set[int]) -> dict:
    nodes = [n for n in graph["nodes"] if int(n["id"]) in keep_ids]
    edges = [e for e in graph["edges"]
             if int(e["src"]) in keep_ids and int(e["tgt"]) in keep_ids]
    return {"nodes": sorted(nodes, key=lambda n: int(n["id"])),
            "edges": sorted(edges, key=lambda e:
                (int(e["src"]), e["type"], int(e["tgt"]))) }


def apply_oracle(base: dict, family: str, fact: int, peer: int, target: int,
                 derived_id: int | None, seed: int, size: int) -> dict:
    nodes = {int(n["id"]): json.loads(json.dumps(n)) for n in base["nodes"]}
    edges = {(int(e["src"]), e["type"], int(e["tgt"])):
             json.loads(json.dumps(e)) for e in base["edges"]}
    if family == "attribute":
        nodes[fact]["attrs"]["generated_value"] = 10_000 + seed
    elif family == "add":
        nodes[derived_id] = {"id": derived_id, "type": "Derived",
                             "attrs": {"seed": seed, "value": size}}
        edges[(fact, "derived", derived_id)] = {"src": fact, "type": "derived",
            "tgt": derived_id, "attrs": {"seed": seed}}
    elif family == "mixed":
        nodes[fact]["attrs"]["generated_value"] = 10_000 + seed
        edges.pop((fact, "link", peer))
        for key in list(edges):
            if target in key[:1] or target == key[2]:
                edges.pop(key)
        nodes.pop(target)
        nodes[derived_id] = {"id": derived_id, "type": "Derived",
                             "attrs": {"seed": seed, "value": size}}
        edges[(fact, "derived", derived_id)] = {"src": fact, "type": "derived",
            "tgt": derived_id, "attrs": {"seed": seed}}
    elif family == "hub_delete":
        for key in list(edges):
            if target in (key[0], key[2]):
                edges.pop(key)
        nodes.pop(target)
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
    for family in FAMILIES:
        for size in SIZES:
            for seed in SEEDS:
                sub, fact, peer, target, hub_degree, seed, family = make_case(family, size, seed)
                base = sub._inner.graph_to_dict()
                base_ids = {int(n["id"]) for n in base["nodes"]}
                hypothesis = {"nodes": [{"key": "h", "type": "Hypothesis",
                    "attrs": {"seed": seed, "proposal": family}}],
                    "edges": [{"src": "h", "type": "tests", "tgt": fact.value}]}
                t0 = time.perf_counter_ns()
                result = imagine(sub, focus_nodes=[fact], focus_hops=2, hypothesis=hypothesis,
                    steps=8, cut_grounding=False, snapshot_backend="native_reusable_snapshot",
                    record_trace=True, _measure_phases=True)
                imagine_ms = (time.perf_counter_ns() - t0) / 1e6
                baseline = semantic_projection(base, base_ids)
                isolated = semantic_projection(sub._inner.graph_to_dict(), base_ids) == baseline
                kinds = {sub.node(cid)["attrs"].get("kind") for cid in result.conclusion_nodes}
                t0 = time.perf_counter_ns()
                regrounded = reground(sub, result)
                reground_ms = (time.perf_counter_ns() - t0) / 1e6
                t0 = time.perf_counter_ns()
                refused = commit_imagination(sub, result, regrounded["survivors"])
                refusal_ms = (time.perf_counter_ns() - t0) / 1e6
                refusal_isolated = semantic_projection(sub._inner.graph_to_dict(), base_ids) == baseline
                t0 = time.perf_counter_ns()
                approved = commit_imagination(sub, result, regrounded["survivors"],
                    approver="generated-oracle-reviewer", projections=projections, manifold=manifold)
                commit_ms = (time.perf_counter_ns() - t0) / 1e6
                added = next((row["node"] for row in approved["written"]
                              if row["kind"] == "node_added"), None)
                expected = apply_oracle(base, family, fact.value, peer.value, target.value,
                    added.value if added else None, seed, size)
                observed = semantic_projection(sub._inner.graph_to_dict(),
                                                {int(n["id"]) for n in expected["nodes"]})
                written = {row["kind"] for row in approved["written"]}
                expected_conclusions = {
                    "attribute": {"node_changed"},
                    "add": {"node_added", "edge_added"},
                    "mixed": {"node_changed", "node_added", "edge_added", "edge_removed", "node_removed"},
                    # Node deletion is the rule conclusion; incident edges are
                    # cascade writeback effects recorded separately in receipt.
                    "hub_delete": {"node_removed"},
                }[family]
                expected_written = {"hub_delete": {"node_removed", "edge_removed"}}.get(
                    family, expected_conclusions)
                rows.append({"family": family, "size": size, "seed": seed,
                    "hub_degree": hub_degree, "base_edges": len(base["edges"]),
                    "phase_ms": {"imagine_total": imagine_ms,
                        **result.phase_timings_ms, "reground": reground_ms,
                        "default_refusal": refusal_ms, "approved_commit": commit_ms},
                    "rehearsal_isolated": isolated,
                    "expected_conclusion_kinds_present": expected_conclusions.issubset(kinds),
                    "default_gate_refused": refused["gate"].get("allowed") is False and not refused["written"],
                    "refusal_preserved_graph": refusal_isolated,
                    "approved_writeback": approved.get("writeback", {}).get("applied") is True,
                    "expected_write_kinds_present": expected_written.issubset(written),
                    "full_graph_oracle_parity": observed == expected})
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
    for _ in range(WORKERS):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
            cwd=ROOT, text=True, capture_output=True)
        if proc.returncode:
            raise SystemExit(proc.stderr[-5000:])
        workers.append(json.loads(proc.stdout))
    rows = [row for w in workers for row in w["rows"]]
    from substrate_rs import _native
    binary = Path(_native.__file__).resolve()
    cells = {(r["family"], r["size"]) for r in rows}
    phases = sorted({key for row in rows for key in row["phase_ms"]})
    medians = {f"{family}/{size}": {phase: statistics.median(
        row["phase_ms"].get(phase, 0.0) for row in rows
        if row["family"] == family and row["size"] == size) for phase in phases}
        for family, size in sorted(cells)}
    checks = {"three_fresh_workers": len({w["pid"] for w in workers}) == WORKERS,
        "72_trials": len(rows) == 72, "eight_family_size_cells": len(cells) == 8,
        "all_rehearsals_isolated": all(r["rehearsal_isolated"] for r in rows),
        "all_default_gates_refused": all(r["default_gate_refused"] for r in rows),
        "all_refusals_preserved_graph": all(r["refusal_preserved_graph"] for r in rows),
        "all_approved_writebacks": all(r["approved_writeback"] for r in rows),
        "all_expected_conclusion_kinds": all(r["expected_conclusion_kinds_present"] for r in rows),
        "all_expected_write_kinds": all(r["expected_write_kinds_present"] for r in rows),
        "all_full_graph_oracles": all(r["full_graph_oracle_parity"] for r in rows)}
    capture = {"schema": "ThoughtexperimentGeneratedResidualAdoptionV1_1",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "source_sha256": {name: sha_file(ROOT / name) for name in SOURCES},
        "binary": {"path": str(binary), "sha256": sha_file(binary)},
        "worker_count": len(workers), "workers": workers, "trials": rows,
        "phase_medians_ms": medians, "checks": checks}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "phase_medians_ms": medians}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
