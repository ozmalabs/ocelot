#!/usr/bin/env python3
"""Fresh-process candidate: eventized ProblemShape transitions plus key support index."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
from substrate_problem_shape_induction_economics import pump, rss_bytes, sha  # noqa: E402
from substrate_problem_shape_population_scale import STATEMENTS, SIZES, MIXES  # noqa: E402

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_PREREG_20260925.md"
AMENDMENTS = []
LOCK = ROOT / "evaluation/substrate_capability/problem_shape_all_transitions_lock_20260925.json"
BASELINE = ROOT / "evaluation/reports/substrate_problem_shape_population_scale_20260925.json"
PS_RULES = {"ps_decode", "ps_recognize", "ps_residual", "ps_mint", "ps_redecode"}


def attr(node: str, key: str) -> dict:
    return {"type": "Attr", "node": {"type": "Var", "name": node}, "key": key}


def term(value: dict) -> dict:
    return {"__term__": value}


def indexed_rules(native, seed: dict, *, deactivate_existing: bool = True) -> dict:
    rules = {r["name"]: copy.deepcopy(r) for r in seed["rules"] if r.get("name") in PS_RULES}
    if deactivate_existing:
        access = native.rule_access_sets()
        ids = {row[1]: int(row[0]) for row in access if row[1] in PS_RULES and row[2]}
        if set(ids) != PS_RULES:
            raise RuntimeError(f"loaded ProblemShape rule names differ from seed: {ids}")
        for rule_id in ids.values():
            if not native.remove_rule(rule_id):
                raise RuntimeError(f"could not tombstone rule slot {rule_id}")
    elif native is not None:
        raise ValueError("native must be None when preserving seed rule slots")

    rules["ps_decode"]["match"] = [["ag", "problem_shape_pending_decode", "obs"]]
    rules["ps_decode"]["effects"].insert(0, ["del_edge", "ag", "problem_shape_pending_decode", "obs"])
    rules["ps_decode"]["effects"].append(["add_edge", "ag", "problem_shape_decoded", "obs", {}])

    rules["ps_recognize"]["match"] = [["ag", "problem_shape_decoded", "obs"]]
    rules["ps_recognize"]["effects"].append(["del_edge", "ag", "problem_shape_decoded", "obs"])

    residual = rules["ps_residual"]
    residual["match"] = [["ag", "problem_shape_decoded", "obs"]]
    residual["effects"].append(["del_edge", "ag", "problem_shape_decoded", "obs"])
    residual["effects"].append(["add_edge", "ag", "problem_shape_residual_candidate", "obs", {}])

    mint = rules["ps_mint"]
    mint["match"] = [["ag", "problem_shape_residual_candidate", "obs"],
                      ["obs", "indexed_problem_shape", "ix"]]
    where = mint["where"]["items"]
    support_guard = where[2]
    support_guard["a"] = attr("ix", "support_count")
    add_shape = next(e for e in mint["effects"] if e[0] == "add_node" and e[2] == "ProblemShape")
    add_shape[3]["support"] = term(attr("ix", "support_count"))
    mint["effects"].append(["del_edge", "ag", "problem_shape_residual_candidate", "obs"])

    redecode = rules["ps_redecode"]
    redecode["effects"] = [
        ["del_edge", "ag", "problem_shape_pending_decode", "obs"],
        ["del_edge", "ag", "problem_shape_decoded", "obs"],
        ["del_edge", "ag", "problem_shape_residual_candidate", "obs"],
        *redecode["effects"],
        ["add_edge", "ag", "problem_shape_pending_decode", "obs", {}],
    ]
    return rules


def observe_indexed(adapter, goal, label: str, native_class, index_by_key: dict[str, object]) -> dict:
    from domains import problem_shape as ps

    sub, native = adapter.s, adapter.inner
    before_nodes, before_edges = sub.node_count(), sub.edge_count()
    before_mints = sum(float(sub.node(n)["attrs"].get("minted", 0.0)) > 0.0
                       for n in sub.nodes("ProblemShape"))
    native_class.scale_audit_reset()
    native_class.scale_audit_per_rule_reset()

    observation_wall0, observation_cpu0 = time.perf_counter_ns(), time.process_time_ns()
    create0 = time.perf_counter_ns()
    obs = ps.observe(adapter, goal, run=False)
    create_ns = time.perf_counter_ns() - create0
    if obs is None:
        raise RuntimeError("ProblemShape observer refused an experimental observation")
    obs_attrs = sub.node(obs)["attrs"]
    key = str(obs_attrs["key"])

    index0 = time.perf_counter_ns()
    ix = index_by_key.get(key)
    if ix is None:
        ix = sub.add_node("ProblemShapeKeyIndex", {"key": key, "support_count": 0})
        index_by_key[key] = ix
    count = int(sub.node(ix)["attrs"]["support_count"]) + 1
    sub.set_attr(ix, "support_count", count)
    sub.add_edge(obs, "indexed_problem_shape", ix)
    sub.add_edge(ix, "indexed_problem_shape_observation", obs)
    sub.add_edge(adapter.agent, "problem_shape_pending_decode", obs)
    index_ns = time.perf_counter_ns() - index0

    closure0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
    legacy_progress = native.run_rules()
    closure_ns, cpu_ns = time.perf_counter_ns() - closure0, time.process_time_ns() - cpu0
    # Match the receipt side effect of problem_shape.observe(run=True).
    sub.add_node("NativeProblemShapeReceipt", {
        "schema": "native_problem_shape_receipt_v1", "cluster": "problem_shape.observation_decode",
        "provenance": "native_rule_readback:problem_shape", "native_rule": "problem_shape_growth_native_decode",
        "native_steps": ["observe_goal", "run_rules", "readback"],
        "outcome_source": "native_rule_readback", "python_outcome_selection": False,
    })
    treatment_observation_wall_ns = time.perf_counter_ns() - observation_wall0
    treatment_observation_cpu_ns = time.process_time_ns() - observation_cpu0
    # As in the baseline harness, instrumentation readback is outside the timed call.
    scale = dict(native_class.scale_audit_snapshot())
    rule_names = {int(row[0]): row[1] for row in native.rule_access_sets()}
    per_rule = [{"rule_index": int(i), "rule_name": rule_names.get(int(i), "?"),
                 "metric": metric, "count": int(c)}
                for i, metric, c in native_class.scale_audit_per_rule_snapshot()]
    ps_rule_metrics = [r for r in per_rule if r["rule_name"] in PS_RULES]
    settle_report = native.run_rules_report(100_000, False)
    attrs_after = sub.node(obs)["attrs"]
    status_after_closure = attrs_after.get("status")
    after_nodes, after_edges = sub.node_count(), sub.edge_count()
    after_mints = sum(float(sub.node(n)["attrs"].get("minted", 0.0)) > 0.0
                      for n in sub.nodes("ProblemShape"))
    return {
        "label": label, "goal_id": goal.value, "observation_id": obs.value, "key": key,
        "observation_status_initial": status_after_closure,
        "observation_status_at_observation_settle": attrs_after.get("status"),
        "covered_by_final": attrs_after.get("covered_by"),
        "mint_count_delta": after_mints - before_mints,
        "node_delta_including_index_and_receipt": after_nodes - before_nodes,
        "edge_delta_including_index_and_event_edges": after_edges - before_edges,
        "host_observation_creation_ns": create_ns,
        "treatment_observation_wall_ns": treatment_observation_wall_ns,
        "treatment_observation_cpu_ns": treatment_observation_cpu_ns,
        "host_index_maintenance_ns": index_ns,
        "native_closure_wall_ns": closure_ns, "native_closure_cpu_ns": cpu_ns,
        "native_legacy_progress": legacy_progress,
        "scale_audit": scale, "all_rule_scale_audit": per_rule, "problem_shape_rule_scale_audit": ps_rule_metrics,
        "problem_shape_candidate_pairs": sum(r["count"] for r in ps_rule_metrics if r["metric"] == "candidate_pairs"),
        "problem_shape_term_evaluations": sum(r["count"] for r in ps_rule_metrics if r["metric"] == "term_evaluations"),
        "ps_mint_candidate_pairs": sum(r["count"] for r in ps_rule_metrics
                                        if r["rule_name"] == "ps_mint" and r["metric"] == "candidate_pairs"),
        "ps_mint_term_evaluations": sum(r["count"] for r in ps_rule_metrics
                                         if r["rule_name"] == "ps_mint" and r["metric"] == "term_evaluations"),
        "post_receipt_settle_report": settle_report,
        "support_count_after_index": count,
    }


def worker(size: int, mix: str, preserve_rule_order: bool = False, seed_dir: str | None = None) -> dict:
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from substrate_rs import _native
    from domains import solver_dispatch as sd
    from domains import problem_decomposition as pdec
    from worlds import bigville_can_beliefs as bcb

    boot0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
    agent = WorldAdapter(seeds=())
    if preserve_rule_order and not seed_dir:
        raise ValueError("preserve_rule_order requires a transformed seed_dir")
    load_report = load_all_seeds(agent, seed_dir=seed_dir)
    seed_rule_rows = sorted((row for row in agent.inner.rule_access_sets() if row[2]), key=lambda row: int(row[0]))
    seed_rule_names = [str(row[1]) for row in seed_rule_rows]
    seed_rule_order_sha256 = hashlib.sha256(json.dumps(seed_rule_names, separators=(",", ":")).encode()).hexdigest()
    seed_ps_positions = {str(row[1]): int(row[0]) for row in seed_rule_rows if row[1] in PS_RULES}
    agent.register_reflex_response("question_pursue", lambda ag: ag._question_pursue_advance())
    agent.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
    boot_wall, boot_cpu = time.perf_counter_ns() - boot0, time.process_time_ns() - cpu0
    s, native, Native = agent.s, agent.inner, _native.Substrate
    # The isolated experiment extends Γ with its two private index/event relations.
    # Keep production timing identical in both eventized variants. In the
    # order-preserving arm the replacement rule bodies were loaded at the
    # original seed positions; the ordinary experimental arm tombstones and
    # appends those rules below.
    native.add_production({"provenance": "recurrence_index_experiment:observation_index",
        "src": {"type": "ProblemShapeObservation", "var": "obs"},
        "edge_type": "indexed_problem_shape",
        "tgt": {"type": "ProblemShapeKeyIndex", "var": "ix"}})
    native.add_production({"provenance": "recurrence_index_experiment:index_observation",
        "src": {"type": "ProblemShapeKeyIndex", "var": "ix"},
        "edge_type": "indexed_problem_shape_observation",
        "tgt": {"type": "ProblemShapeObservation", "var": "obs"}})
    native.add_production({"provenance": "all_transitions_experiment:pending_decode",
        "src": {"type": "Agent", "var": "ag"},
        "edge_type": "problem_shape_pending_decode",
        "tgt": {"type": "ProblemShapeObservation", "var": "obs"}})
    native.add_production({"provenance": "all_transitions_experiment:decoded",
        "src": {"type": "Agent", "var": "ag"},
        "edge_type": "problem_shape_decoded",
        "tgt": {"type": "ProblemShapeObservation", "var": "obs"}})
    native.add_production({"provenance": "all_transitions_experiment:residual_candidate",
        "src": {"type": "Agent", "var": "ag"},
        "edge_type": "problem_shape_residual_candidate",
        "tgt": {"type": "ProblemShapeObservation", "var": "obs"}})

    seed_path = (Path(seed_dir) / "problem_shape_growth.json" if seed_dir
                 else ROOT / "seeds/problem_shape_growth.json")
    seed = json.loads(seed_path.read_text())
    if not preserve_rule_order:
        variants = indexed_rules(native, seed)
        for name in ("ps_decode", "ps_recognize", "ps_residual", "ps_mint", "ps_redecode"):
            native.add_rule(variants[name])
    index_by_key = {}

    scaffolding = []
    resolutions = []
    for statement in STATEMENTS[:3]:
        goal = sd.mint_solve_deduction_goal(agent, statement)
        resolved = pump(agent, goal)
        resolutions.append({"label": "schema_scaffold", **resolved})
        scaffolding.append(goal)

    pre_observe_rows = sorted((row for row in native.rule_access_sets() if row[2]), key=lambda row: int(row[0]))
    pre_observe_names = [str(row[1]) for row in pre_observe_rows]
    pre_observe_rule_order_sha256 = hashlib.sha256(json.dumps(pre_observe_names, separators=(",", ":")).encode()).hexdigest()
    pre_observe_ps_positions = {str(row[1]): int(row[0]) for row in pre_observe_rows if row[1] in PS_RULES}
    Native.scale_audit_set_enabled(True)
    Native.scale_audit_set_per_rule_enabled(True)
    records = []
    if mix == "recognition":
        bcb.install_productions(native)
        residents = json.loads((ROOT / "seeds/bigville_cast100.json").read_text())["residents"]
        for i in range(size):
            if i % 2 == 0:
                goal = sd.mint_solve_deduction_goal(agent, STATEMENTS[(i // 2) % len(STATEMENTS)])
                label = f"deduction_{i+1}"
            else:
                built = bcb.build_resident_can_mt(native, residents[i])
                bcb.apply_scenario_evidence(native, built["concepts"])
                native.set_attr(built["mt_node"], "discrete_mode", "3state")
                native.set_attr(built["mt_node"], "can_tick", 0)
                goal = sd.mint_solve_can_exact_goal(agent, built["mt_node"])
                label = f"can_exact_{i+1}"
            resolutions.append({"label": label, **pump(agent, goal)})
            records.append(observe_indexed(agent, goal, label, Native, index_by_key))
    elif mix == "recurrent_residual":
        schemas = [sd._solve_caps(agent)[g]["result"]["node"] for g in scaffolding]
        shared = pdec.project_deduction_shared_attr(s, schemas)
        complete = pdec.project_deduction_complete(s, schemas)
        for i in range(size):
            if i == 0:
                candidates, bound = [shared, complete], 1
            elif i == 1:
                candidates, bound = [complete], 0
            else:
                candidates, bound = [shared], 5 + i
            goal = sd.mint_solve_decompose_goal(agent, candidates, bound=bound)
            label = f"decompose_{i+1}"
            resolutions.append({"label": label, **pump(agent, goal)})
            records.append(observe_indexed(agent, goal, label, Native, index_by_key))
    else:
        raise ValueError(mix)

    # Refresh application-visible final state after the complete sequence, as the
    # locked baseline does; later minting can re-decode earlier observations.
    for row in records:
        final_attrs = s.node(_native.NodeID(int(row["observation_id"]))) ["attrs"]
        row["observation_status_final"] = final_attrs.get("status")
        row["covered_by_final"] = final_attrs.get("covered_by")

    # Independent host-side grouping oracle for the experimental support rows.
    expected_support = {}
    for node in s.nodes("ProblemShapeObservation"):
        key = str(s.node(node)["attrs"]["key"])
        expected_support[key] = expected_support.get(key, 0) + 1
    actual_support = {str(s.node(ix)["attrs"]["key"]): int(s.node(ix)["attrs"]["support_count"])
                      for ix in s.nodes("ProblemShapeKeyIndex")}
    every_observation_indexed_once = all(len(s.neighbours(o, "indexed_problem_shape")) == 1
                                         for o in s.nodes("ProblemShapeObservation"))
    support_exact = actual_support == expected_support
    mint_count = sum(r["mint_count_delta"] for r in records)
    expected_status = (["recognized"] * size if mix == "recognition" else
                       (["residual"] + ["recognized"] * (size - 1)))
    expected_final = ["recognized"] * size
    initial_ok = [r["observation_status_initial"] for r in records] == expected_status
    final_ok = [r["observation_status_final"] for r in records] == expected_final
    expected_mints = 0 if mix == "recognition" else 1
    minted_shapes = [s.node(n)["attrs"] for n in s.nodes("ProblemShape")
                     if float(s.node(n)["attrs"].get("minted", 0.0)) > 0.0]
    expected_minted_support = 0 if mix == "recognition" else 2
    minted_shape_support_exact = (not minted_shapes if mix == "recognition" else
                                  len(minted_shapes) == 1 and int(minted_shapes[0].get("support", -1)) == expected_minted_support
                                  and minted_shapes[0].get("name") == "ps_has_bound=yes")
    codebook_epoch_exact = int(s.node(agent.agent)["attrs"].get("problem_codebook_epoch", 0)) == expected_mints
    all_fixed = all(r["post_receipt_settle_report"]["status"] == "fixed_point" for r in records)
    active_rule_rows = sorted((row for row in native.rule_access_sets() if row[2]), key=lambda row: int(row[0]))
    active_rule_order = [str(row[1]) for row in active_rule_rows]
    active_rule_order_sha256 = hashlib.sha256(json.dumps(active_rule_order, separators=(",", ":")).encode()).hexdigest()
    active_rule_positions = {str(row[1]): int(row[0]) for row in active_rule_rows
                             if row[1] in {"ps_decode", "ps_recognize", "ps_residual", "ps_mint", "ps_redecode"}}
    Native.scale_audit_set_enabled(False)
    Native.scale_audit_set_per_rule_enabled(False)
    return {
        "preserve_rule_order": preserve_rule_order,
        "seed_rule_order_sha256": seed_rule_order_sha256,
        "seed_rule_names": seed_rule_names,
        "seed_problem_shape_rule_positions": seed_ps_positions,
        "pre_observation_rule_names": pre_observe_names,
        "pre_observation_rule_order_sha256": pre_observe_rule_order_sha256,
        "pre_observation_problem_shape_rule_positions": pre_observe_ps_positions,
        "seed_load_order": load_report.get("order", []),
        "seed_load_failed_ids": [str(row) for row in load_report.get("failed", [])],
        "seed_load_failure_count": len(load_report.get("failed", [])),
        "active_problem_shape_rule_positions": active_rule_positions,
        "active_rule_order_sha256": active_rule_order_sha256,
        "worker_id": f"indexed-N{size}-{mix}", "process_id": os.getpid(),
        "population_size": size, "task_mix": mix, "variant": "all_transition_events_plus_key_support_counter",
        "full_seed_boot_wall_ns": boot_wall, "full_seed_boot_cpu_ns": boot_cpu,
        "process_peak_rss_bytes": rss_bytes(), "goal_resolution_costs": resolutions,
        "records": records, "actual_support_by_key": actual_support,
        "expected_support_by_key": expected_support,
        "minted_shape_snapshot": minted_shapes,
        "expected_minted_support_at_first_recurrence": expected_minted_support,
        "support_exact": support_exact, "every_observation_indexed_once": every_observation_indexed_once,
        "problem_shape_candidate_pairs_total": sum(r["problem_shape_candidate_pairs"] for r in records),
        "problem_shape_term_evaluations_total": sum(r["problem_shape_term_evaluations"] for r in records),
        "ps_mint_candidate_pairs_total": sum(r["ps_mint_candidate_pairs"] for r in records),
        "ps_mint_term_evaluations_total": sum(r["ps_mint_term_evaluations"] for r in records),
        "host_index_maintenance_ns_total": sum(r["host_index_maintenance_ns"] for r in records),
        "all_checks_pass": initial_ok and final_ok and mint_count == expected_mints and all_fixed and
                           support_exact and every_observation_indexed_once and
                           minted_shape_support_exact and codebook_epoch_exact,
        "checks": {"expected_initial_statuses": initial_ok, "expected_final_statuses": final_ok,
                   "expected_mint_count": mint_count == expected_mints, "all_fixed_point": all_fixed,
                   "support_count_exact": support_exact, "one_index_per_observation": every_observation_indexed_once,
                   "minted_shape_and_support_exact": minted_shape_support_exact,
                   "codebook_epoch_exact": codebook_epoch_exact},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--worker-size", type=int, choices=SIZES, help=argparse.SUPPRESS)
    ap.add_argument("--worker-mix", choices=MIXES, help=argparse.SUPPRESS)
    ap.add_argument("--worker-preserve-rule-order", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--worker-seed-dir", type=Path, help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.worker_size is not None:
        if not args.worker_mix:
            ap.error("worker mode requires --worker-mix")
        result = worker(args.worker_size, args.worker_mix, args.worker_preserve_rule_order,
                        str(args.worker_seed_dir) if args.worker_seed_dir else None)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["all_checks_pass"] else 2
    if args.output is None:
        ap.error("--output is required")
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}"}
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],
        cwd=ROOT, env=env, text=True).strip()
    if stale:
        raise SystemExit(f"native build stale:\n{stale}")
    lock = json.loads(LOCK.read_text())
    for key, value in {
        "preregistration_sha256": sha(PREREG), "runner_sha256": sha(Path(__file__)),
        "amendment_hashes": [sha(p) for p in AMENDMENTS],
        "native_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"),
        "baseline_raw_sha256": sha(BASELINE),
        "seed_hashes": {p.name: sha(p) for p in [ROOT / "seeds/problem_shape_growth.json",
                                                   ROOT / "seeds/shape_decode_loop.json",
                                                   ROOT / "seeds/bigville_cast100.json"]},
    }.items():
        if lock.get(key) != value:
            raise SystemExit(f"lock mismatch at {key}")

    records = []
    for n in SIZES:
        for mix in MIXES:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                                   "--worker-size", str(n), "--worker-mix", mix],
                                  cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
            if proc.returncode:
                raise RuntimeError(f"indexed worker failed {n}/{mix}:\n{proc.stdout}\n{proc.stderr}")
            worker_record = json.loads(proc.stdout)
            base = next(r for r in json.loads(BASELINE.read_text())["records"]
                        if r["population_size"] == n and r["task_mix"] == mix
                        and r["codebook_mode"] == "dynamic")
            worker_record["baseline"] = {
                "raw_report_sha256": lock["baseline_raw_sha256"],
                "problem_shape_candidate_pairs_total": base["problem_shape_candidate_pairs_total"],
                "problem_shape_term_evaluations_total": base["problem_shape_term_evaluations_total"],
                "ps_mint_candidate_pairs_total": sum(z["count"] for q in base["records"]
                    for z in q["problem_shape_rule_scale_audit"]
                    if z["rule_name"] == "ps_mint" and z["metric"] == "candidate_pairs"),
                "ps_mint_term_evaluations_total": sum(z["count"] for q in base["records"]
                    for z in q["problem_shape_rule_scale_audit"]
                    if z["rule_name"] == "ps_mint" and z["metric"] == "term_evaluations"),
                "total_observe_wall_ns": sum(q["wall_time_ns"] for q in base["records"]),
            }
            worker_record["delta_vs_locked_baseline"] = {
                "problem_shape_candidate_pairs": (worker_record["problem_shape_candidate_pairs_total"]
                    - base["problem_shape_candidate_pairs_total"]),
                "problem_shape_term_evaluations": (worker_record["problem_shape_term_evaluations_total"]
                    - base["problem_shape_term_evaluations_total"]),
                "ps_mint_candidate_pairs": (worker_record["ps_mint_candidate_pairs_total"]
                    - worker_record["baseline"]["ps_mint_candidate_pairs_total"]),
                "ps_mint_term_evaluations": (worker_record["ps_mint_term_evaluations_total"]
                    - worker_record["baseline"]["ps_mint_term_evaluations_total"]),
            }
            records.append(worker_record)
            print(json.dumps({"completed": worker_record["worker_id"], "checks": worker_record["checks"]}), flush=True)
    result = {
        "schema_version": 1, "run_id": f"problem-shape-all-transitions-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        "preregistration": {"path": str(PREREG.relative_to(ROOT)), "sha256": sha(PREREG)},
        "amendments": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p)} for p in AMENDMENTS],
        "lock": {"path": str(LOCK.relative_to(ROOT)), "sha256": sha(LOCK)},
        "runner_sha256": sha(Path(__file__)), "native_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"),
        "baseline_raw_path": str(BASELINE.relative_to(ROOT)), "baseline_raw_sha256": lock["baseline_raw_sha256"],
        "unique_worker_pids": len({r["process_id"] for r in records}) == len(records),
        "records": records, "all_checks_pass": all(r["all_checks_pass"] for r in records)
                              and len({r["process_id"] for r in records}) == len(records),
        "claim_limit": "candidate mechanism prototype; ps_redecode intentionally remains globally driven for codebook invalidation",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": result["all_checks_pass"], "workers": len(records)}, sort_keys=True))
    return 0 if result["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
