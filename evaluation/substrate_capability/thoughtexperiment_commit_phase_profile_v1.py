#!/usr/bin/env python3
"""Profile rule-generated commit phases against an independent graph oracle."""
from __future__ import annotations

import hashlib, importlib.util, json, os, platform, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
BASE_RUNNER = "evaluation/substrate_capability/thoughtexperiment_generated_residual_adoption_v1_1.py"
PREREG = "docs/research/engine_substrate/THOUGHTEXPERIMENT_COMMIT_PHASE_PROFILE_V1_PREREG_20261001.md"
SOURCES = ("evaluation/substrate_capability/thoughtexperiment_commit_phase_profile_v1.py", BASE_RUNNER,
    PREREG, "docs/research/engine_substrate/THOUGHTEXPERIMENT_TARGETED_COMMIT_READS_V1_PREREG_20261001.md",
    "domains/imagination.py", "domains/commitment_gate.py",
    "domains/information_commitment.py", "domains/shape_tube.py",
    "runners/dsl/src/persist.rs", "runners/dsl/src/graph.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json")
RAW = ROOT / "evaluation/reports/thoughtexperiment_commit_phase_profile_v1.json"
WORKERS = 3


def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("generated_residual_v1_1", ROOT / BASE_RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def timed_wrapper(bucket: dict, key: str, original):
    def wrapped(*args, **kwargs):
        start = time.perf_counter_ns()
        try:
            return original(*args, **kwargs)
        finally:
            row = bucket.setdefault(key, {"count": 0, "total_ms": 0.0})
            row["count"] += 1
            row["total_ms"] += (time.perf_counter_ns() - start) / 1e6
    return wrapped


def instrument(bucket: dict, branch, seed: int):
    import domains.imagination as imagination
    import domains.commitment_gate as gate
    import domains.information_commitment as info
    from substrate_rs import Substrate
    native_type = type(Substrate()._inner)
    patches = []

    def patch(obj, attr, key):
        original = getattr(obj, attr)
        setattr(obj, attr, timed_wrapper(bucket, key, original))
        patches.append((obj, attr, original))

    original_gate = imagination.commit_gate
    def timed_gate(agent, *args, **kwargs):
        started = time.perf_counter_ns()
        try:
            result = original_gate(agent, *args, **kwargs)
        finally:
            row = bucket.setdefault("commit_gate", {"count": 0, "total_ms": 0.0})
            row["count"] += 1
            row["total_ms"] += (time.perf_counter_ns() - started) / 1e6
        # Exercise a trailing tombstone after the gate has minted its audit
        # record, immediately before commit allocates its output IDs.
        tombstone = branch.add_node("TemporaryHighId", {"seed": seed})
        assert branch.remove_node(tombstone)
        bucket["tombstone_id"] = tombstone.value
        bucket["tombstone_policy"] = branch._inner.next_live_node_id() == tombstone.value
        return result
    imagination.commit_gate = timed_gate
    patches.append((imagination, "commit_gate", original_gate))
    patch(imagination, "_judge_conclusion", "judge_conclusion")
    patch(gate, "_mint_commitment_record", "commitment_record_mint")
    patch(info, "assess", "information_assess")
    patch(native_type, "graph_to_dict", "live_graph_snapshot")
    patch(native_type, "apply_experiment_graph_delta", "staged_delta_apply")
    patch(native_type, "set_attr", "native_set_attr")
    return patches


def restore(patches):
    for obj, attr, original in reversed(patches):
        setattr(obj, attr, original)


def worker() -> dict:
    from domains.imagination import imagine, reground, commit_imagination
    import domains.imagination as imagination_module
    from domains.shape_tube import goal_manifold, goal_projection
    base_module = load_base()
    projections = {
        "commit": goal_projection("generated", active=True, action_count=1, intervention_magnitude=1.0),
        "wait": goal_projection("generated", active=False, action_count=0, intervention_magnitude=0.0),
        "refine": goal_projection("generated", active=False, action_count=1, intervention_magnitude=0.5),
    }
    manifold = goal_manifold("generated")
    rows = []
    for family in base_module.FAMILIES:
        for size in base_module.SIZES:
            for seed in base_module.SEEDS:
                sub, fact, peer, target, hub_degree, seed, family = base_module.make_case(family, size, seed)
                base_graph = sub._inner.graph_to_dict()
                base_ids = {int(n["id"]) for n in base_graph["nodes"]}
                hyp = {"nodes": [{"key": "h", "type": "Hypothesis", "attrs": {"seed": seed}}],
                       "edges": [{"src": "h", "type": "tests", "tgt": fact.value}]}
                result = imagine(sub, focus_nodes=[fact], focus_hops=2, hypothesis=hyp,
                    steps=8, cut_grounding=False, snapshot_backend="native_reusable_snapshot",
                    record_trace=True, _measure_phases=True)
                after_imagine = sub._inner.graph_to_dict()
                isolated = base_module.semantic_projection(after_imagine, base_ids) == \
                           base_module.semantic_projection(base_graph, base_ids)
                reground_start = time.perf_counter_ns()
                regrounded = reground(sub, result)
                reground_ms = (time.perf_counter_ns() - reground_start) / 1e6
                # Check fail-closed behavior before timing the approved path.
                refused = commit_imagination(sub, result, regrounded["survivors"])
                refusal_ok = refused["gate"].get("allowed") is False and not refused["written"]
                refusal_graph = base_module.semantic_projection(sub._inner.graph_to_dict(), base_ids)
                refusal_isolated = refusal_graph == base_module.semantic_projection(base_graph, base_ids)
                kinds = {"attribute": {"node_changed"}, "add": {"node_added", "edge_added"},
                    "mixed": {"node_changed", "node_added", "edge_added", "edge_removed", "node_removed"},
                    "hub_delete": {"node_removed", "edge_removed"}}[family]
                conclusion_expected = {"node_removed"} if family == "hub_delete" else kinds
                arms = {}
                modes = ("legacy_full_graph", "targeted_native")
                mode_order = modes if (seed + size + base_module.FAMILIES.index(family)) % 2 == 0 else tuple(reversed(modes))
                for mode in mode_order:
                    branch = sub.fork_full_copy_experiment()
                    bucket: dict = {}
                    patches = instrument(bucket, branch, seed)
                    start = time.perf_counter_ns()
                    try:
                        approved = commit_imagination(branch, result, regrounded["survivors"],
                            approver="profile-reviewer", projections=projections, manifold=manifold,
                            _targeted_commit_reads=(mode == "targeted_native"))
                    finally:
                        commit_total_ms = (time.perf_counter_ns() - start) / 1e6
                        restore(patches)
                    added = next((r["node"] for r in approved["written"] if r["kind"] == "node_added"), None)
                    expected = base_module.apply_oracle(base_graph, family, fact.value, peer.value,
                        target.value, added.value if added else None, seed, size)
                    observed = base_module.semantic_projection(branch._inner.graph_to_dict(),
                        {int(n["id"]) for n in expected["nodes"]})
                    written = {r["kind"] for r in approved["written"]}
                    expected_added_id = bucket.get("tombstone_id")
                    allocation_ok = added is None or added.value == expected_added_id
                    # Nested instrumented phase totals overlap; this remainder
                    # is explicitly not an additive partition.
                    nested_keys = ("commit_gate", "information_assess", "commitment_record_mint",
                        "judge_conclusion", "live_graph_snapshot", "staged_delta_apply", "native_set_attr")
                    covered_sum = sum(bucket.get(k, {}).get("total_ms", 0.0) for k in nested_keys)
                    bucket["unattributed_nonpartition_remainder_ms"] = commit_total_ms - covered_sum
                    arms[mode] = {"commit_total_ms": commit_total_ms, "instrumented": bucket,
                        "approved_writeback": approved.get("writeback", {}).get("applied") is True,
                        "expected_write_kinds": kinds.issubset(written),
                        "allocated_next_live_id": allocation_ok,
                        "tombstone_policy": bucket.get("tombstone_policy") is True,
                        "full_graph_oracle": observed == expected}
                # Separate uninstrumented paired timing. The tiny gate wrapper
                # only creates the trailing tombstone needed by this fixture.
                uninstrumented = {}
                original_gate = imagination_module.commit_gate
                def gate_with_trailing_tombstone(agent, *args, **kwargs):
                    gate_result = original_gate(agent, *args, **kwargs)
                    temp = agent.add_node("TemporaryHighId", {"seed": seed})
                    assert agent.remove_node(temp)
                    uninstrumented["tombstone_id"] = temp.value
                    uninstrumented["tombstone_policy"] = agent._inner.next_live_node_id() == temp.value
                    return gate_result
                imagination_module.commit_gate = gate_with_trailing_tombstone
                try:
                    for mode in mode_order:
                        branch = sub.fork_full_copy_experiment()
                        start = time.perf_counter_ns()
                        approved = commit_imagination(branch, result, regrounded["survivors"],
                            approver="profile-reviewer", projections=projections, manifold=manifold,
                            _targeted_commit_reads=(mode == "targeted_native"))
                        elapsed_ms = (time.perf_counter_ns() - start) / 1e6
                        added = next((r["node"] for r in approved["written"] if r["kind"] == "node_added"), None)
                        expected = base_module.apply_oracle(base_graph, family, fact.value, peer.value,
                            target.value, added.value if added else None, seed, size)
                        observed = base_module.semantic_projection(branch._inner.graph_to_dict(),
                            {int(n["id"]) for n in expected["nodes"]})
                        uninstrumented[mode] = {"commit_total_ms": elapsed_ms,
                            "full_graph_oracle": observed == expected,
                            "writeback": approved.get("writeback", {}).get("applied") is True,
                            "allocated_next_live_id": added is None or
                                added.value == uninstrumented["tombstone_id"]}
                finally:
                    imagination_module.commit_gate = original_gate
                rows.append({"family": family, "size": size, "seed": seed,
                    "hub_degree": hub_degree, "imagine_phases_ms": result.phase_timings_ms,
                    "reground_ms": reground_ms, "arms": arms, "uninstrumented": uninstrumented,
                    "rehearsal_isolated": isolated, "default_refused": refusal_ok,
                    "refusal_preserved_graph": refusal_isolated,
                    "expected_conclusion_kinds": conclusion_expected.issubset(
                        {sub.node(cid)["attrs"].get("kind") for cid in result.conclusion_nodes}),
                    "both_arms_match_oracle": all(a["full_graph_oracle"] for a in arms.values()),
                    "both_uninstrumented_match_oracle": all(uninstrumented[m]["full_graph_oracle"]
                        for m in ("legacy_full_graph", "targeted_native")),
                    "both_uninstrumented_writeback": all(uninstrumented[m]["writeback"]
                        for m in ("legacy_full_graph", "targeted_native")),
                    "both_uninstrumented_allocate_tombstone": all(uninstrumented[m]["allocated_next_live_id"]
                        for m in ("legacy_full_graph", "targeted_native")),
                    "both_arms_preserve_id_allocation": all(a["allocated_next_live_id"] and
                                                              a["tombstone_policy"] for a in arms.values())})
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
    phases = sorted({k for r in rows for arm in r["arms"].values()
                     for k, value in arm["instrumented"].items()
                     if isinstance(value, dict) and k != "unattributed_nonpartition_remainder_ms"})
    medians = {}
    for family in ("attribute", "add", "mixed", "hub_delete"):
        for size in (64, 1000):
            cell = [r for r in rows if r["family"] == family and r["size"] == size]
            key = f"{family}/{size}"
            medians[key] = {}
            medians[key]["uninstrumented_paired"] = {mode: statistics.median(
                r["uninstrumented"][mode]["commit_total_ms"] for r in cell)
                for mode in ("legacy_full_graph", "targeted_native")}
            for mode in ("legacy_full_graph", "targeted_native"):
                medians[key][mode] = {"commit_total_ms": statistics.median(r["arms"][mode]["commit_total_ms"] for r in cell),
                "reground_ms": statistics.median(r["reground_ms"] for r in cell),
                **{phase: {"count_median": statistics.median(r["arms"][mode]["instrumented"].get(phase, {}).get("count", 0)
                             for r in cell), "total_ms_median": statistics.median(
                             r["arms"][mode]["instrumented"].get(phase, {}).get("total_ms", 0.0) for r in cell)}
                   for phase in phases}}
    checks = {"three_fresh_workers": len({w["pid"] for w in workers}) == 3,
        "72_trials": len(rows) == 72,
        "all_rehearsals_isolated": all(r["rehearsal_isolated"] for r in rows),
        "all_default_refused": all(r["default_refused"] for r in rows),
        "all_refusals_isolated": all(r["refusal_preserved_graph"] for r in rows),
        "all_arms_approved_writeback": all(a["approved_writeback"] for r in rows for a in r["arms"].values()),
        "all_expected_conclusion_kinds": all(r["expected_conclusion_kinds"] for r in rows),
        "all_expected_write_kinds": all(a["expected_write_kinds"] for r in rows for a in r["arms"].values()),
        "all_full_graph_oracles": all(r["both_arms_match_oracle"] for r in rows),
        "all_uninstrumented_oracles": all(r["both_uninstrumented_match_oracle"] for r in rows),
        "all_uninstrumented_writebacks": all(r["both_uninstrumented_writeback"] for r in rows),
        "all_uninstrumented_tombstone_ids": all(r["both_uninstrumented_allocate_tombstone"] for r in rows),
        "all_tombstone_ids_preserved": all(r["both_arms_preserve_id_allocation"] for r in rows)}
    from substrate_rs import _native
    binary = Path(_native.__file__).resolve()
    capture = {"schema": "ThoughtexperimentCommitPhaseProfileV1",
        "host": {"platform": platform.platform(), "machine": platform.machine(), "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "source_sha256": {name: sha_file(ROOT / name) for name in SOURCES},
        "binary": {"path": str(binary), "sha256": sha_file(binary)},
        "workers": workers, "trials": rows, "phase_medians_ms": medians, "checks": checks}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "phase_medians_ms": medians}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
