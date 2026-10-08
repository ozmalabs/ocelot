#!/usr/bin/env python3
"""Independent node-count × edge-density × deletion-aperture commit panel."""
from __future__ import annotations

import copy, hashlib, json, os, platform, random, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
NODES = (256, 1000, 5000)
DENSITIES = (0, 2, 8)
APERTURES = (1, 4, 32, 128)
SEEDS = (720101, 720102, 720103, 720104)
HOLE_MODES = ("none", "random4", "trailing4", "mixed8")
WORKERS = 3
PREREG = "docs/research/engine_substrate/THOUGHTEXPERIMENT_TARGETED_COMMIT_FACTORIAL_V1_1_PREREG_20261001.md"
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_targeted_commit_factorial_v1_1.py",
    PREREG,
    "domains/imagination.py", "domains/commitment_gate.py", "domains/shape_tube.py",
    "domains/engine_provenance.py", "runners/dsl/src/persist.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/src/py.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/_native.build.json",
)
RAW = ROOT / "evaluation/reports/thoughtexperiment_targeted_commit_factorial_v1_1.json"


def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def make_case(n_nodes: int, density: int, aperture: int, seed: int, hole_mode: str):
    from substrate_rs import Substrate
    from substrate_rs.ext import add_rule

    rng = random.Random(seed + 31 * n_nodes + 101 * density + 1009 * aperture)
    hole_count = {"none": 0, "random4": 4, "trailing4": 4, "mixed8": 8}[hole_mode]
    total_slots = n_nodes + hole_count
    sub = Substrate()
    all_nodes = [sub.add_node("Base", {"ordinal": i, "value": rng.randrange(1_000_000)})
                 for i in range(total_slots)]
    # Protect fact, peer, hub, and every node in the deletion aperture.
    protected_end = 3 + aperture - 1
    eligible = list(range(protected_end, total_slots))
    if hole_mode == "none":
        holes: list[int] = []
    elif hole_mode == "trailing4":
        holes = eligible[-4:]
    elif hole_mode == "random4":
        holes = rng.sample(eligible, 4)
    else:
        trailing = eligible[-4:]
        random_pool = [ix for ix in eligible if ix not in trailing]
        holes = trailing + rng.sample(random_pool, 4)
    for ix in holes:
        sub.remove_node(all_nodes[ix])
    live = [nid for nid in all_nodes if sub.has_node(nid)]
    assert len(live) == n_nodes
    fact, peer, hub = live[:3]
    spoke_count = aperture - 1
    spokes = live[3:3 + spoke_count]
    # Every non-focal node participates, including spokes. This keeps the
    # controlled background out-degree independent of the deletion aperture.
    context = live[3:]
    sub.add_edge_unchecked(fact, "link", peer, {"seed": seed, "confidence": 0.4})
    sub.add_edge_unchecked(fact, "cascade", hub, {"seed": seed, "reason": "remove-hub"})
    for ix, spoke in enumerate(spokes):
        sub.add_edge_unchecked(hub, "spoke", spoke, {"seed": seed, "ordinal": ix})
    shift = rng.randrange(len(context)) if context else 0
    for ix, src in enumerate(context):
        for offset in range(1, density + 1):
            tgt = context[(ix + offset + shift) % len(context)]
            sub.add_edge_unchecked(src, "context", tgt,
                {"seed": seed, "offset": offset})
    changed_value = 10_000_000 + (seed % 100_000) + n_nodes
    derived_value = {"seed": seed, "nodes": n_nodes, "density": density}
    add_rule(sub, f"targeted_factorial_{n_nodes}_{density}_{aperture}_{seed}",
        [("h", "tests", "f"), ("f", "link", "g"), ("f", "cascade", "z")],
        [["set_attr", "f", "factorial_value", changed_value],
         ["del_edge", "f", "link", "g"],
         ["add_node", "n", "Derived", derived_value],
         ["add_edge", "f", "derived", "n", {"seed": seed, "density": density}],
         ["del_node", "z"]])
    return {"sub": sub, "fact": fact, "peer": peer, "hub": hub, "changed": changed_value,
        "derived_value": derived_value, "seed": seed, "density": density, "aperture": aperture,
        "hole_mode": hole_mode, "holes": sorted(holes), "context_nodes": len(context)}


def project(graph: dict, keep: set[int]) -> dict:
    return {"nodes": sorted((n for n in graph["nodes"] if int(n["id"]) in keep),
                             key=lambda n: int(n["id"])),
        "edges": sorted((e for e in graph["edges"]
                         if int(e["src"]) in keep and int(e["tgt"]) in keep),
            key=lambda e: (int(e["src"]), e["type"], int(e["tgt"]))) }


def oracle(base: dict, case: dict, derived_id: int) -> dict:
    fact, peer, hub = case["fact"].value, case["peer"].value, case["hub"].value
    nodes = {int(n["id"]): copy.deepcopy(n) for n in base["nodes"]}
    edges = {(int(e["src"]), e["type"], int(e["tgt"])): copy.deepcopy(e) for e in base["edges"]}
    nodes[fact]["attrs"]["factorial_value"] = case["changed"]
    edges.pop((fact, "link", peer))
    for key in list(edges):
        if hub in (key[0], key[2]):
            edges.pop(key)
    nodes.pop(hub)
    nodes[derived_id] = {"id": derived_id, "type": "Derived", "attrs": case["derived_value"]}
    edges[(fact, "derived", derived_id)] = {"src": fact, "type": "derived", "tgt": derived_id,
        "attrs": {"seed": case["seed"], "density": case["density"]}}
    return {"nodes": sorted(nodes.values(), key=lambda n: int(n["id"])),
        "edges": sorted(edges.values(), key=lambda e:
            (int(e["src"]), e["type"], int(e["tgt"]))) }


def install_tombstone_gate(bucket: dict, branch, original_gate, seed: int):
    def gate_and_tombstone(agent, *args, **kwargs):
        result = original_gate(agent, *args, **kwargs)
        dead = agent.add_node("TemporaryCommitTombstone", {"seed": seed})
        assert agent.remove_node(dead)
        bucket["gate_tombstone_id"] = dead.value
        return result
    return gate_and_tombstone


def run_approved_arm(sub, result, survivors, projections, manifold, mode: str, seed: int):
    import domains.imagination as imagination
    from domains.imagination import commit_imagination
    original_gate = imagination.commit_gate
    bucket: dict = {}
    imagination.commit_gate = install_tombstone_gate(bucket, sub, original_gate, seed)
    start = time.perf_counter_ns()
    try:
        receipt = commit_imagination(sub, result, survivors, approver="factorial-reviewer",
            projections=projections, manifold=manifold,
            _targeted_commit_reads=(mode == "targeted_native"))
    finally:
        elapsed_ms = (time.perf_counter_ns() - start) / 1e6
        imagination.commit_gate = original_gate
    return receipt, elapsed_ms, bucket


def worker(worker_index: int) -> dict:
    from domains.imagination import imagine, reground, commit_imagination
    import domains.imagination as imagination
    from domains.shape_tube import goal_manifold, goal_projection
    from substrate_rs import Substrate
    projections = {
        "commit": goal_projection("factorial", active=True, action_count=1, intervention_magnitude=1.0),
        "wait": goal_projection("factorial", active=False, action_count=0, intervention_magnitude=0.0),
        "refine": goal_projection("factorial", active=False, action_count=1, intervention_magnitude=0.5),
    }
    manifold = goal_manifold("factorial")
    rows, conflicts = [], []
    cell_number = 0
    for n_nodes in NODES:
        for density in DENSITIES:
            for aperture in APERTURES:
                for seed in SEEDS:
                    hole_mode = HOLE_MODES[(seed + cell_number) % len(HOLE_MODES)]
                    case = make_case(n_nodes, density, aperture, seed, hole_mode)
                    sub = case["sub"]
                    base = sub._inner.graph_to_dict()
                    base_ids = {int(n["id"]) for n in base["nodes"]}
                    hyp = {"nodes": [{"key": "h", "type": "Hypothesis", "attrs": {"seed": seed}}],
                           "edges": [{"src": "h", "type": "tests", "tgt": case["fact"].value}]}
                    result = imagine(sub, focus_nodes=[case["fact"]], focus_hops=2, hypothesis=hyp,
                        steps=8, cut_grounding=False, snapshot_backend="native_reusable_snapshot",
                        record_trace=True)
                    rehearsal_ok = project(sub._inner.graph_to_dict(), base_ids) == project(base, base_ids)
                    regrounded = reground(sub, result)
                    refused = commit_imagination(sub, result, regrounded["survivors"])
                    refusal_ok = refused["gate"].get("allowed") is False and not refused["written"]
                    refusal_ok = refusal_ok and project(sub._inner.graph_to_dict(), base_ids) == project(base, base_ids)

                    modes = ("legacy_full_graph", "targeted_native")
                    order = modes if (worker_index + seed + n_nodes + density + aperture) % 2 == 0 else tuple(reversed(modes))
                    arm_results = {}
                    for mode in order:
                        branch = sub.fork_full_copy_experiment()
                        receipt, elapsed_ms, tombstone = run_approved_arm(
                            branch, result, regrounded["survivors"], projections, manifold, mode, seed)
                        added = next((r["node"] for r in receipt["written"] if r["kind"] == "node_added"), None)
                        expected = oracle(base, case, added.value if added else -1)
                        observed = project(branch._inner.graph_to_dict(), {int(n["id"]) for n in expected["nodes"]})
                        kinds = {r["kind"] for r in receipt["written"]}
                        arm_results[mode] = {"commit_ms": elapsed_ms,
                            "writeback": receipt.get("writeback", {}).get("applied") is True,
                            "write_kinds": {"node_changed", "node_added", "edge_added", "edge_removed", "node_removed"}.issubset(kinds),
                            "oracle": observed == expected, "added_id": added.value if added else None,
                            "gate_tombstone_id": tombstone.get("gate_tombstone_id")}
                    rows.append({"nodes": n_nodes, "background_out_degree": density,
                        "aperture_degree": aperture, "seed": seed, "hole_mode": hole_mode,
                        "hole_count": len(case["holes"]), "context_nodes": case["context_nodes"],
                        "actual_live_nodes": len(base["nodes"]), "actual_base_edges": len(base["edges"]),
                        "rehearsal_isolated": rehearsal_ok, "default_refused_and_isolated": refusal_ok,
                        "arms": arm_results, "same_added_id": arm_results[modes[0]]["added_id"] ==
                            arm_results[modes[1]]["added_id"]})

                # One explicit revision-conflict case for every node × density × aperture cell.
                conflict_seed = SEEDS[(worker_index + cell_number) % len(SEEDS)]
                conflict_mode = HOLE_MODES[(conflict_seed + cell_number) % len(HOLE_MODES)]
                cc = make_case(n_nodes, density, aperture, conflict_seed, conflict_mode)
                csub = cc["sub"]
                chyp = {"nodes": [{"key": "h", "type": "Hypothesis", "attrs": {"seed": conflict_seed}}],
                        "edges": [{"src": "h", "type": "tests", "tgt": cc["fact"].value}]}
                cres = imagine(csub, focus_nodes=[cc["fact"]], focus_hops=2, hypothesis=chyp,
                    steps=8, cut_grounding=False, snapshot_backend="native_reusable_snapshot", record_trace=True)
                csurvivors = reground(csub, cres)["survivors"]
                cb = csub.fork_full_copy_experiment()
                native_type = type(cb._inner)
                original_apply = native_type.apply_experiment_graph_delta
                def competing_writer(native, revision, delta):
                    native.add_node("ConcurrentWriter", {"cell": cell_number, "seed": conflict_seed})
                    return original_apply(native, revision, delta)
                native_type.apply_experiment_graph_delta = competing_writer
                try:
                    creceipt = commit_imagination(cb, cres, csurvivors, approver="conflict-reviewer",
                        projections=projections, manifold=manifold, _targeted_commit_reads=True)
                finally:
                    native_type.apply_experiment_graph_delta = original_apply
                cgraph = cb._inner.graph_to_dict()
                conflict_ok = (creceipt.get("writeback", {}).get("reason") == "graph_batch_conflict"
                    and not creceipt["written"] and cb.has_node(cc["hub"]) and cb.has_edge(cc["fact"], "link", cc["peer"])
                    and cb.node(cc["fact"])["attrs"].get("factorial_value") is None
                    and not any(n["type"] == "Derived" for n in cgraph["nodes"])
                    and any(n["type"] == "ConcurrentWriter" for n in cgraph["nodes"]))
                conflicts.append({"nodes": n_nodes, "background_out_degree": density,
                    "aperture_degree": aperture, "seed": conflict_seed, "hole_mode": conflict_mode,
                    "revision_conflict_atomic_and_preserved": conflict_ok})
                cell_number += 1
    return {"pid": os.getpid(), "worker_index": worker_index, "rows": rows, "conflicts": conflicts}


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, separators=(",", ":")))
        return 0
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    workers = []
    for index in range(WORKERS):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(index)],
            cwd=ROOT, text=True, capture_output=True)
        if proc.returncode:
            raise SystemExit(proc.stderr[-5000:])
        workers.append(json.loads(proc.stdout))
    rows = [r for w in workers for r in w["rows"]]
    conflicts = [r for w in workers for r in w["conflicts"]]
    expected_cells = {(n, d, a) for n in NODES for d in DENSITIES for a in APERTURES}
    grouped = {}
    for n, d, a in sorted(expected_cells):
        cell = [r for r in rows if (r["nodes"], r["background_out_degree"], r["aperture_degree"]) == (n, d, a)]
        key = f"N{n}/out{d}/ap{a}"
        legacy = [r["arms"]["legacy_full_graph"]["commit_ms"] for r in cell]
        targeted = [r["arms"]["targeted_native"]["commit_ms"] for r in cell]
        wins = sum(b < a for a, b in zip(legacy, targeted))
        grouped[key] = {"trials": len(cell), "actual_nodes_median": statistics.median(r["actual_live_nodes"] for r in cell),
            "actual_edges_median": statistics.median(r["actual_base_edges"] for r in cell),
            "legacy_commit_median_ms": statistics.median(legacy),
            "targeted_commit_median_ms": statistics.median(targeted),
            "paired_ratio_median": statistics.median(a / b for a, b in zip(legacy, targeted) if b > 0),
            "targeted_pair_wins": wins}
    checks = {"three_fresh_workers": len({w["pid"] for w in workers}) == WORKERS,
        "36_factorial_cells": len({(r["nodes"], r["background_out_degree"], r["aperture_degree"]) for r in rows}) == 36,
        "432_clean_pairs": len(rows) == 432 and all(len(r["arms"]) == 2 for r in rows),
        "108_conflict_cases": len(conflicts) == 108,
        "all_rehearsals_isolated": all(r["rehearsal_isolated"] for r in rows),
        "all_default_refusals_isolated": all(r["default_refused_and_isolated"] for r in rows),
        "all_writebacks_applied": all(a["writeback"] for r in rows for a in r["arms"].values()),
        "all_write_kinds": all(a["write_kinds"] for r in rows for a in r["arms"].values()),
        "all_full_graph_oracles": all(a["oracle"] for r in rows for a in r["arms"].values()),
        "all_same_added_ids": all(r["same_added_id"] for r in rows),
        "all_revision_conflicts_atomic": all(r["revision_conflict_atomic_and_preserved"] for r in conflicts),
        "all_tombstone_layouts_covered": {r["hole_mode"] for r in rows} == set(HOLE_MODES)}
    from substrate_rs import _native
    binary = Path(_native.__file__).resolve()
    capture = {"schema": "ThoughtexperimentTargetedCommitFactorialV1_1",
        "host": {"platform": platform.platform(), "machine": platform.machine(), "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "source_sha256": {name: sha_file(ROOT / name) for name in SOURCES},
        "binary": {"path": str(binary), "sha256": sha_file(binary)},
        "workers": workers, "trials": rows, "conflicts": conflicts,
        "cell_summary": grouped, "checks": checks}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "cell_summary": grouped}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
