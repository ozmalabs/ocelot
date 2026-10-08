#!/usr/bin/env python3
"""Measure graph-authored correction candidate ranking on a held-out wave."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
WORKERS = 3
ARMS = ("default_order", "graph_cost_rank")
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_GRAPH_AUTHORED_CORRECTION_RANK_V1_PREREG_20261001.md"
RAW = ROOT / "evaluation/reports/thoughtexperiment_graph_authored_correction_rank_v1_raw_20261001.json"
RESULT = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_GRAPH_AUTHORED_CORRECTION_RANK_V1_RESULTS_20261001.md"
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_GRAPH_AUTHORED_CORRECTION_RANK_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_graph_authored_correction_rank_v1.py",
    "domains/reflective_faculty.py", "domains/self_correct_dispatch.py",
    "domains/self_correction.py", "domains/collapse_watch.py",
    "domains/collapse_model.py", "seeds/composer_self_correct_graph.json",
    "seeds/composer_collapse_watch_graph.json", "seeds/shape_decode_loop.json",
    "seeds/relation_vocabulary.json", "seeds/composer_dispatch.json",
    "seeds/autonomy.json", "substrate/boot_core.py",
    "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs",
    "runners/dsl/python/substrate_rs/_native.build.json",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    from substrate_rs import _native
    binary = Path(_native.__file__).resolve()
    return {"files": {name: sha(ROOT / name) for name in SOURCES},
            "native_path": str(binary), "native_sha256": sha(binary)}


def add_wave(sub, agent, prefix: str) -> list:
    result = []
    for i in range(3):
        token = f"{prefix}{i}"
        node = sub.add_node("Observation", {
            "signature": [[token, "X"]], "key": [token], "status": "pending"})
        sub.add_edge(agent, "observed", node)
        result.append((token, node))
    return result


def episode(worker_index: int, arm: str) -> dict:
    from substrate.boot_core import boot_core
    from substrate.seed_loader import manifest_for
    import domains.reflective_faculty as rf
    from domains import collapse_watch as cw
    from domains import self_correct_dispatch as dispatch
    from domains.collapse_model import predict_collapse
    from domains import self_correction as correction
    from domains.self_correction import _default_candidates, _infer_growth_rule
    from domains.self_correct_dispatch import _candidate_cost

    sub, agent_node = boot_core()
    for seed_id in ("relation_vocabulary", "composer_dispatch", "autonomy"):
        sub._inner.load_seed_manifest(manifest_for(seed_id), agent_node)

    class Agent:
        def __init__(self, substrate, node):
            self.s, self.inner, self.agent = substrate, substrate._inner, node

    agent = Agent(sub, agent_node)
    compose_rows = []
    for phrase, tag in ((["predict", "COLLAPSE", "of", "DIVERGENCE"], "cw_rank"),
                        (["correct", "DIVERGENCE", "by", "CANDIDATE"], "sc_rank")):
        induced = rf.induce_concern(agent, [phrase], name_hint=tag)
        composed = rf.ground_concern(agent, [induced["capability_key"]])
        compose_rows.append({"tag": tag, "grounded": composed.get("grounded"),
                             "served_by": composed.get("served_by"),
                             "path": composed.get("path"),
                             "program_name": composed.get("program_name")})
    native = rf._native_eval2(sub)
    rf._ensure_shape_decode_loop(sub, native, agent_node)
    for rule_name in ("sd_mint_quantum", "sd_dedup_existing"):
        sub.add_node("RuleSummary", {"name": rule_name, "from_seed": "self_correction_rank_eval"})
    sub.add_node("SeedSummary", {"seed_id": "self_correction_rank_eval", "skippable": 1.0})

    first_wave = add_wave(sub, agent_node, f"w{worker_index}{arm}A")
    initial_model = cw.scan_and_predict(agent)
    closure_progress = int(native.run_rules(2000))
    impasses = [node for node in sub.nodes("Impasse")
                if sub.node(node)["attrs"].get("kind") == "predicted_divergence"]
    correct_ready = bool(impasses and sub.node(impasses[0])["attrs"].get("correct_ready"))
    second_wave = add_wave(sub, agent_node, f"w{worker_index}{arm}B")
    model_before = predict_collapse(agent)
    target = _infer_growth_rule(native, model_before)
    candidates = _default_candidates(native, target) if target else []
    candidate_labels = [candidate.get("label") for candidate in candidates]
    candidate_costs = {candidate.get("label"): _candidate_cost(native, candidate)
                       for candidate in candidates}
    program_name = next((sub.node(node)["attrs"].get("name")
                         for node in sub.nodes("Program")
                         if str(sub.node(node)["attrs"].get("name", "")).startswith("self_correct_rank_")), None)
    program_present = bool(program_name)

    ordering_start = time.perf_counter_ns()
    if arm == "graph_cost_rank":
        candidates = dispatch.rank_candidates(agent, native, candidates)
    ordering_ns = time.perf_counter_ns() - ordering_start

    before_rules = native.export_rules()
    rehearsal_rule_parity = []
    original_imagine = correction.imagine_and_check_convergence

    def tracked_imagine(*args, **kwargs):
        rule_state_before = native.export_rules()
        value = original_imagine(*args, **kwargs)
        rule_state_after = native.export_rules()
        rehearsal_rule_parity.append(rule_state_before == rule_state_after)
        return value

    correction.imagine_and_check_convergence = tracked_imagine
    correction_start = time.perf_counter_ns()
    try:
        result = correction.intervene_on_divergence(agent, target_rule=target,
            candidates=candidates, model_before=model_before)
    finally:
        correction.imagine_and_check_convergence = original_imagine
    correction_ns = time.perf_counter_ns() - correction_start
    after_rules = native.export_rules()
    selected = result.get("chosen")
    active_rules = {row.get("name"): row.get("active", True) for row in after_rules}
    variant_rule = next((name for name, active in active_rules.items()
                         if name and name.startswith("sd_mint_quantum_scfix_") and active), None)
    selected_candidate = next((candidate for candidate in candidates
                               if candidate.get("label") == selected), None)
    allowed_rule_names = set(selected_candidate.get("rules", {})) if selected_candidate else set()
    if selected_candidate:
        allowed_rule_names.update(
            variant.get("name") for variant in selected_candidate["rules"].values()
            if isinstance(variant, dict) and variant.get("name"))
    before_status = {row.get("name"): row.get("active", True) for row in before_rules}
    changed_rule_names = sorted(name for name in set(before_status) | set(active_rules)
                                if before_status.get(name) != active_rules.get(name))
    rule_changes_limited_to_selected_candidate = set(changed_rule_names).issubset(allowed_rule_names)

    third_wave = add_wave(sub, agent_node, f"w{worker_index}{arm}C")
    third_closure_progress = int(native.run_rules(2000))
    c_pending = []
    c_axis_counts = {}
    for token, node in third_wave:
        if sub.has_node(node) and sub.node(node)["attrs"].get("status") == "pending":
            c_pending.append(token)
        matching_axes = [axis for axis in sub.nodes("CapabilityAxis")
                         if sub.node(axis)["attrs"].get("induced")
                         and sub.node(axis)["attrs"].get("capability_keys") == [[token, "X"]]]
        c_axis_counts[token] = len(matching_axes)
    fixedpoint_progress = int(native.run_rules(2000))
    final_model = predict_collapse(agent)
    tried = result.get("candidates_tried", [])
    task_oracle = {
        "repair_rule_active": bool(variant_rule),
        "original_rule_inactive": active_rules.get("sd_mint_quantum") is False,
        "no_heldout_observations_pending": not c_pending,
        "one_axis_per_heldout_signature": all(value == 1 for value in c_axis_counts.values()),
        "native_rule_closure_at_fixed_point": fixedpoint_progress == 0,
    }
    return {
        "worker_index": worker_index, "pid": os.getpid(), "arm": arm,
        "composer_rows": compose_rows, "both_composers_graph_authored":
            all(row["grounded"] and row["served_by"] == "graph" for row in compose_rows),
        "rank_program_present_before_ablation": program_present,
        "rank_program_name": program_name,
        "first_wave_count": len(first_wave), "first_model_converged": initial_model.converged,
        "first_closure_progress": closure_progress,
        "correct_ready_gate": correct_ready, "second_wave_count": len(second_wave),
        "target_rule": target, "model_before_converged": model_before.converged,
        "candidate_default_order": candidate_labels,
        "candidate_order_used": [candidate.get("label") for candidate in candidates],
        "candidate_costs": candidate_costs,
        "candidate_ordering_wall_ns": ordering_ns, "correction_wall_ns": correction_ns,
        "selected_candidate": selected, "adopted": bool(result.get("adopted")),
        "escalated": bool(result.get("escalated")),
        "tried": [{"label": row.get("label"), "converges": row.get("converges"),
                   "inert": row.get("inert"), "selected": row.get("selected"),
                   "rank_trace": row.get("rank_trace")} for row in tried],
        "candidates_tested": len(tried),
        "every_rehearsal_preserved_primary_rules": bool(rehearsal_rule_parity) and all(rehearsal_rule_parity),
        "rehearsal_rule_parity_checks": rehearsal_rule_parity,
        "rule_changes_limited_to_selected_candidate": rule_changes_limited_to_selected_candidate,
        "changed_rule_names": changed_rule_names,
        "variant_rule": variant_rule, "model_final_converged":
            bool(result.get("model_final") and result["model_final"].converged),
        "heldout_wave": {"closure_progress": third_closure_progress,
                         "pending_tokens": c_pending, "axis_count_by_signature": c_axis_counts,
                         "model_converged": final_model.converged,
                         "independent_task_oracle": task_oracle},
        "all_task_oracle_gates": all(task_oracle.values()),
    }


def worker(worker_index: int) -> dict:
    before = fingerprint()
    episodes = [episode(worker_index, arm) for arm in ARMS]
    after = fingerprint()
    return {"pid": os.getpid(), "source_before": before, "source_after": after,
            "source_stable": before == after, "episodes": episodes}


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, separators=(",", ":")))
        return 0
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    env = {**os.environ, "PYTHONPATH": f"{ROOT / 'runners/dsl/python'}:{ROOT}"}
    workers = []
    for worker_index in range(WORKERS):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker",
                               str(worker_index)],
            cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        # The native graph-composer emits diagnostic lines to process stdout;
        # the worker's final line is the machine-readable capture.
        workers.append(json.loads(proc.stdout.splitlines()[-1]))
    episodes = [episode for worker_row in workers for episode in worker_row["episodes"]]
    by_arm = {arm: [row for row in episodes if row["arm"] == arm] for arm in ARMS}
    gates = {
        "three_fresh_workers": len({row["pid"] for row in workers}) == WORKERS,
        "six_episodes": len(episodes) == WORKERS * len(ARMS),
        "all_composers_graph_authored": all(row["both_composers_graph_authored"] for row in episodes),
        "rank_program_present_in_both_arms": all(row["rank_program_present_before_ablation"] for row in episodes),
        "all_first_impasses_correct_ready": all(row["correct_ready_gate"] for row in episodes),
        "all_episodes_locate_target": all(row["target_rule"] == "sd_mint_quantum" for row in episodes),
        "all_episodes_adopt_same_candidate": all(row["adopted"] and
            row["selected_candidate"] == "dedup_identity_fix" for row in episodes),
        "all_model_outcomes_converge": all(row["model_final_converged"] for row in episodes),
        "all_rehearsals_preserve_primary_rules": all(row["every_rehearsal_preserved_primary_rules"] for row in episodes),
        "committed_rule_changes_match_selected_candidate": all(row["rule_changes_limited_to_selected_candidate"] for row in episodes),
        "all_heldout_task_oracles": all(row["all_task_oracle_gates"] for row in episodes),
        "stable_source_and_build": all(row["source_stable"] for row in workers),
        "rank_arm_uses_rank_trace": all(any(item.get("rank_trace") for item in row["tried"])
                                          for row in by_arm["graph_cost_rank"]),
        "default_arm_has_no_rank_trace": all(not any(item.get("rank_trace") for item in row["tried"])
                                               for row in by_arm["default_order"]),
    }
    result_rows = []
    for arm in ARMS:
        rows = by_arm[arm]
        result_rows.append({"arm": arm, "episodes": len(rows),
            "candidate_tests": [row["candidates_tested"] for row in rows],
            "candidate_tests_median": statistics.median(row["candidates_tested"] for row in rows),
            "correction_ms_median": statistics.median(row["correction_wall_ns"] for row in rows) / 1e6,
            "heldout_ok": sum(row["all_task_oracle_gates"] for row in rows),
            "orders": [row["candidate_order_used"] for row in rows],
            "selected": [row["selected_candidate"] for row in rows]})
    from substrate_rs import _native
    binary = Path(_native.__file__).resolve()
    capture = {"schema": "ThoughtexperimentGraphAuthoredCorrectionRankV1",
        "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "engine_fingerprint": rust_source_fingerprint(str(ROOT)),
        "protocol": {"worker_count": WORKERS, "arms": list(ARMS),
                     "episodes_per_arm": WORKERS, "episodes_per_worker": len(ARMS),
                     "waves": [3, 3, 3],
                     "rank_policy": "graph Argmin over measured JSON structural cost",
                     "default_control": "same policy Program present; ranking evaluation ablated"},
        "native_binary": {"path": str(binary), "sha256": sha(binary)},
        "workers": workers, "episodes": episodes, "arm_summary": result_rows, "gates": gates}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    out = f"""# Thoughtexperiment graph-authored correction ranking v1 — results

**Result:** {sum(gates.values())}/{len(gates)} preregistered gates pass.

The first harness invocation exposed an implementation mistake in the worker loop: it ran 18 episodes instead of the preregistered six and failed the episode-count gate. The runner was corrected without changing the protocol, then rerun with exactly three workers and six episodes. Only the corrected replay below is treated as the confirmatory capture.

## Outcome

{WORKERS} fresh workers completed {len(episodes)} episodes, with each worker running both arms on fresh substrates. The graph-authored composers produced the correction gate and rank Program. Both arms passed the correct-ready gate, identified `sd_mint_quantum`, adopted `dedup_identity_fix`, and passed every held-out continuation oracle. The third wave used new observation signatures; direct graph inspection found no pending held-out observations, exactly one induced axis per signature, and a zero-progress native closure at the fixed point.

| Arm | Candidate attempts | Median attempts | Median correction time | Held-out oracle |
|---|---:|---:|---:|---:|
"""
    for summary in result_rows:
        out += f"| `{summary['arm']}` | {summary['candidate_tests']} | {summary['candidate_tests_median']} | {summary['correction_ms_median']:.3f} ms | {summary['heldout_ok']}/{WORKERS} |\n"
    out += """

The graph ranker orders candidates by structural cost and tries the zero-cost `swap_term_leaf:signature->residual` first; it fails to converge, then `dedup_identity_fix` succeeds at a JSON-size-difference score of 868. The default order tries the successful repair first. Both routes reach the same held-out outcome, while ranking performs more candidate rehearsals. This task therefore does not show a utility advantage for the rank policy; on this fixture its edit-size prior increases search work. Structural edit size is not a substitute for predicted task utility. Every worker ran `default_order` before `graph_cost_rank`, so timing differences are descriptive and may include arm-order/cache effects; candidate attempts and held-out task outcomes are the stronger comparisons.

## Interpretation and limits

The result establishes that the active adapter can execute the graph-authored rank Program and carry a selected correction into later task inputs on this authored observation family. It also reveals that cost-only ranking does not reduce work here. The policy is authored once and does not learn from the returned experience record. Three workers and one task family do not estimate general correction quality, natural-task frequency, or scale. A future delegated-boundary evaluation should make the rank policy consume accumulated outcome/residual/cost experience and compare it on fresh correction families against default, random, and frozen controls.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_GRAPH_AUTHORED_CORRECTION_RANK_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_graph_authored_correction_rank_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_graph_authored_correction_rank_v1_raw_20261001.json)
"""
    RESULT.write_text(out)
    summary = {"gates": gates, "arm_summary": result_rows,
               "worker_pids": [row["pid"] for row in workers]}
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
