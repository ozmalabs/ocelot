#!/usr/bin/env python3
"""Measure costs/statuses of real ProblemShape rung transitions."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_INDUCTION_ECONOMICS_PREREG_20260925.md"
PROBLEM_SHAPE_RULES = {"ps_decode", "ps_recognize", "ps_residual", "ps_mint", "ps_redecode"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value * 1024 if sys.platform.startswith("linux") else value)


def pump(adapter, goal, max_iters: int = 32) -> dict:
    started_wall, started_cpu = time.perf_counter_ns(), time.process_time_ns()
    for _ in range(max_iters):
        adapter.fire_reflexes()
        adapter.inner.run_rules()
        status = adapter.s.node(goal)["attrs"].get("status")
        if status in ("resolved", "walled"):
            return {"status": status, "iterations": _ + 1,
                    "wall_time_ns": time.perf_counter_ns() - started_wall,
                    "cpu_time_ns": time.process_time_ns() - started_cpu}
    raise RuntimeError(f"goal {goal} did not resolve in {max_iters} driver iterations")


def observe_measure(adapter, goal, label: str, native_class) -> dict:
    sub, native = adapter.s, adapter.inner
    before_nodes, before_edges = sub.node_count(), sub.edge_count()
    before_shapes = len(sub.nodes("ProblemShape"))
    before_minted = sum(float(sub.node(n)["attrs"].get("minted", 0.0)) > 0.0
                        for n in sub.nodes("ProblemShape"))
    native_class.scale_audit_reset()
    native_class.scale_audit_per_rule_reset()
    wall0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
    obs = __import__("domains.problem_shape", fromlist=["observe"]).observe(adapter, goal)
    wall_ns, cpu_ns = time.perf_counter_ns() - wall0, time.process_time_ns() - cpu0
    scale = dict(native_class.scale_audit_snapshot())
    rule_rows = native_class.scale_audit_per_rule_snapshot()
    per_rule_names = {row[0]: row[1] for row in native.rule_access_sets()}
    per_rule = [{"rule_index": int(idx), "rule_name": per_rule_names.get(int(idx), "?"),
                 "metric": metric, "count": int(count)}
                for idx, metric, count in rule_rows]
    problem_shape_per_rule = [row for row in per_rule if row["rule_name"] in PROBLEM_SHAPE_RULES]
    after_nodes, after_edges = sub.node_count(), sub.edge_count()
    after_shapes = len(sub.nodes("ProblemShape"))
    after_minted = sum(float(sub.node(n)["attrs"].get("minted", 0.0)) > 0.0
                       for n in sub.nodes("ProblemShape"))
    obs_attrs = sub.node(obs)["attrs"] if obs is not None else {}
    report = native.run_rules_report(100_000, False)
    return {
        "label": label, "goal_id": int(goal.value),
        "observation_id": int(obs.value) if obs is not None else None,
        "goal_status": sub.node(goal)["attrs"].get("status"),
        "observation_status_initial": obs_attrs.get("status"),
        "covered_by_initial": obs_attrs.get("covered_by"),
        "residual_initial": obs_attrs.get("status") == "residual",
        "mint_count_delta": after_minted - before_minted,
        "problem_shape_count_delta": after_shapes - before_shapes,
        "node_delta_including_receipt": after_nodes - before_nodes,
        "edge_delta": after_edges - before_edges,
        "wall_time_ns": wall_ns, "cpu_time_ns": cpu_ns,
        "scale_audit": scale,
        "all_rule_scale_audit": per_rule,
        "problem_shape_rule_scale_audit": problem_shape_per_rule,
        "problem_shape_candidate_pairs": sum(row["count"] for row in problem_shape_per_rule
                                              if row["metric"] == "candidate_pairs"),
        "problem_shape_term_evaluations": sum(row["count"] for row in problem_shape_per_rule
                                              if row["metric"] == "term_evaluations"),
        "problem_shape_term_units": sum(row["count"] for row in problem_shape_per_rule
                                         if row["metric"] == "term_units"),
        "post_observe_settle_report": report,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}"}
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"]
        , cwd=ROOT, env=env, text=True).strip()
    if stale:
        raise SystemExit(f"native build is stale:\n{stale}")

    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from substrate_rs import _native
    from domains import solver_dispatch as sd
    from domains import problem_shape as ps
    from domains import problem_decomposition as pdec
    from worlds import bigville_can_beliefs as bcb

    boot_wall0, boot_cpu0 = time.perf_counter_ns(), time.process_time_ns()
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.register_reflex_response("question_pursue", lambda ag: ag._question_pursue_advance())
    agent.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
    boot_wall_ns, boot_cpu_ns = time.perf_counter_ns() - boot_wall0, time.process_time_ns() - boot_cpu0
    s, native = agent.s, agent.inner
    Native = _native.Substrate
    Native.scale_audit_set_enabled(True)
    Native.scale_audit_set_per_rule_enabled(True)
    records: list[dict] = []
    goal_resolution: list[dict] = []

    def solve_and_observe(goal, label: str) -> None:
        goal_resolution.append({"label": label, **pump(agent, goal)})
        records.append(observe_measure(agent, goal, label, Native))

    # Three ordinary deduction goals: one codebook hit plus repeated use.
    deduction_goals = []
    for i, statement in enumerate(("if X is a fish, X can swim", "if X is a bird, X can fly",
                                   "if X is a dog, X can bark")):
        goal = sd.mint_solve_deduction_goal(agent, statement)
        solve_and_observe(goal, f"deduction_recognition_{i + 1}")
        deduction_goals.append(goal)

    # Three real CAN goals built from Bigville resident records.
    bcb.install_productions(native)
    residents = json.loads((ROOT / "seeds/bigville_cast100.json").read_text())["residents"]
    can_goals = []
    for i in range(3):
        built = bcb.build_resident_can_mt(native, residents[i])
        bcb.apply_scenario_evidence(native, built["concepts"])
        native.set_attr(built["mt_node"], "discrete_mode", "3state")
        native.set_attr(built["mt_node"], "can_tick", 0)
        goal = sd.mint_solve_can_exact_goal(agent, built["mt_node"])
        solve_and_observe(goal, f"can_exact_recognition_{i + 1}")
        can_goals.append(goal)

    # Real decomposition recurrence: derive candidate schemas from solved
    # deduction goals, then observe two distinct attempts of the same shape.
    schema_nodes = [sd._solve_caps(agent)[g]["result"]["node"] for g in deduction_goals]
    cand_shared = pdec.project_deduction_shared_attr(s, schema_nodes)
    cand_complete = pdec.project_deduction_complete(s, schema_nodes)
    decompose_goals = [
        sd.mint_solve_decompose_goal(agent, [cand_shared, cand_complete], bound=1),
        sd.mint_solve_decompose_goal(agent, [cand_complete], bound=0),
        sd.mint_solve_decompose_goal(agent, [cand_shared], bound=5),
    ]
    for i, goal in enumerate(decompose_goals):
        solve_and_observe(goal, f"decompose_recurrence_{i + 1}")

    # A real singleton structural kind should remain residual and must not mint.
    mt = sd._solve_caps(agent)[can_goals[0]]["result"].get("mt")
    if mt is None:
        # The resolver stores the real target on the graph; use the target edge.
        mt_nodes = s.neighbours(can_goals[0], "targets_mt")
        if not mt_nodes:
            raise RuntimeError("resolved CAN Goal has no targets_mt edge")
        mt = mt_nodes[0]
    bridge = sd.mint_solve_reasoning_bridge_goal(agent, "can_to_deduction", mt=mt)
    solve_and_observe(bridge, "novel_singleton_residual")

    for row in records:
        obs_id = row["observation_id"]
        final_attrs = s.node(_native.NodeID(obs_id))["attrs"] if obs_id is not None else {}
        row["observation_status_final"] = final_attrs.get("status")
        row["covered_by_final"] = final_attrs.get("covered_by")

    Native.scale_audit_set_enabled(False)
    Native.scale_audit_set_per_rule_enabled(False)
    expected = {
        "deduction_recognition_1": "recognized", "deduction_recognition_2": "recognized",
        "deduction_recognition_3": "recognized", "can_exact_recognition_1": "recognized",
        "can_exact_recognition_2": "recognized", "can_exact_recognition_3": "recognized",
        "decompose_recurrence_1": "residual", "decompose_recurrence_2": "recognized",
        "decompose_recurrence_3": "recognized", "novel_singleton_residual": "residual",
    }
    # Observation one in the decompose recurrence is initially residual, then
    # re-decodes after observation two mints. Preserve its initial and final
    # states from the trajectory by checking the eventual recognized endpoint.
    checks = {row["label"]: row["observation_status_initial"] == expected[row["label"]]
              for row in records}
    first_decompose = next(r for r in records if r["label"] == "decompose_recurrence_1")
    redecoded = first_decompose["observation_status_final"] == "recognized" and \
        first_decompose["covered_by_final"] == "ps_has_bound=yes"
    mint_total = sum(row["mint_count_delta"] for row in records)
    result = {
        "schema_version": 1,
        "run_id": f"problem-shape-economics-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        "preregistration": {"path": str(PREREG.relative_to(ROOT)), "sha256": sha(PREREG)},
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty_tree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "native_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"),
        "build_record_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "runner_sha256": sha(Path(__file__)),
        "seed_hashes": {p.name: sha(p) for p in [ROOT / "seeds/problem_shape_growth.json",
                                                   ROOT / "seeds/shape_decode_loop.json",
                                                   ROOT / "seeds/bigville_cast100.json"]},
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "logical_cpu_count": os.cpu_count()},
        "setup_cost": {"full_seed_boot_wall_ns": boot_wall_ns,
                       "full_seed_boot_cpu_ns": boot_cpu_ns,
                       "peak_rss_bytes": rss_bytes()},
        "goal_resolution_costs": goal_resolution,
        "records": records,
        "summary": {"observation_count": len(records), "total_mints": mint_total,
                    "residual_observations_final": sum(r["observation_status_final"] == "residual" for r in records),
                    "residual_observations_at_arrival": sum(r["observation_status_initial"] == "residual" for r in records),
                    "problem_shape_candidate_pairs_total": sum(r["problem_shape_candidate_pairs"] for r in records),
                    "problem_shape_term_evaluations_total": sum(r["problem_shape_term_evaluations"] for r in records),
                    "problem_shape_term_units_total": sum(r["problem_shape_term_units"] for r in records),
                    "instrumented_observe_wall_ns_median": int(statistics.median(r["wall_time_ns"] for r in records)),
                    "instrumented_observe_wall_ns_max": max(r["wall_time_ns"] for r in records),
                    "expected_status_checks": checks, "all_expected_statuses_match": all(checks.values()),
                    "first_residual_redecoded_after_mint": redecoded,
                    "mint_total_expected": 1, "mint_total_matches": mint_total == 1},
        "claim_limit": "one fixed-order, small project-authored task sequence; timing describes observe calls only and does not estimate natural residual frequency or held-out induction quality",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))
    return 0 if result["summary"]["all_expected_statuses_match"] and result["summary"]["mint_total_matches"] and redecoded else 2


if __name__ == "__main__":
    raise SystemExit(main())
