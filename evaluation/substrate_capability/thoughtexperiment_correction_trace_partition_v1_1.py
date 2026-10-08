#!/usr/bin/env python3
"""Paired monolithic/scoped closure on production-materialized correction traces."""
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
sys.path[:0] = [str(ROOT), str(ROOT / "runners" / "dsl" / "python")]
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_correction_trace_partition_v1_1_lock_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_correction_trace_partition_v1_1_20261003.json"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_correction_trace_partition_v1_1.py"
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_correction_trace_partition_v1_1.py",
    "evaluation/substrate_capability/analyze_thoughtexperiment_correction_trace_partition_v1_1.py",
    "domains/seed_registry.py", "domains/discourse_state.py",
    "seeds/communication_intent_arbitration.json",
    "tests/test_phase2_grounding_reference_evidence.py",
    "substrate/boot_core.py", "substrate/world_adapter.py",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/graph.rs", "runners/dsl/src/term.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
)
SIZES = (1, 2, 4, 8)
ORDERS = ("ascending", "descending", "outside_in")
REPLICATES_PER_ORDER = 3
CAP = 100_000
EXPECTED_EVIDENCE = "CommunicationInterpretation -> discourse-scoped DiscourseState -> prior grounded DiscourseEvent -> matching action-target head"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_inputs() -> dict:
    from substrate_rs import _native
    inputs = {p: sha(ROOT / p) for p in SOURCES}
    inputs["native_extension"] = sha(Path(_native.__file__).resolve())
    inputs["native_build_manifest"] = sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json")
    inputs["cargo_lock"] = sha(ROOT / "runners/dsl/Cargo.lock")
    inputs["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return inputs


def frame_order(n: int, policy: str) -> list[int]:
    frames = list(range(2 * n))
    if policy == "ascending":
        return frames
    if policy == "descending":
        return list(reversed(frames))
    out = []
    lo, hi = 0, len(frames) - 1
    while lo <= hi:
        out.append(frames[lo]); lo += 1
        if lo <= hi:
            out.append(frames[hi]); hi -= 1
    return out


def graph_digest(graph: dict) -> str:
    return hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(",", ":"),
                                    default=str).encode()).hexdigest()


def canonical_graph_digest(graph: dict) -> str:
    """Hash graph facts as sets of records; retain duplicate records if any."""
    canonical = dict(graph)
    for key in ("nodes", "edges"):
        if isinstance(canonical.get(key), list):
            canonical[key] = sorted(canonical[key], key=lambda row: json.dumps(
                row, sort_keys=True, separators=(",", ":"), default=str))
    return graph_digest(canonical)


def node_value(node) -> int:
    return int(node.value if hasattr(node, "value") else node)


def valid_scope_membership(row: dict) -> bool:
    scopes = row.get("scope_membership", [])
    if len(scopes) != row.get("frame_count"):
        return False
    roots = [int(scope["scope_root_id"]) for scope in scopes]
    member_ids = [int(member["node_id"]) for scope in scopes for member in scope["members"]]
    return (len(set(roots)) == len(roots)
            and len(set(member_ids)) == len(member_ids)
            and all(scope["scope_root_type"] == "Microtheory"
                    and len(scope["members"]) == 2
                    and {member["node_type"] for member in scope["members"]}
                    == {"DiscourseEvent", "CommunicationInterpretation"}
                    and scope["owned_node_count_including_scope_root"] == 3
                    and int(scope["scope_root_id"]) not in
                    {int(member["node_id"]) for member in scope["members"]}
                    for scope in scopes))


def execute(n: int, policy: str, arm: str, replicate: int) -> dict:
    from types import SimpleNamespace
    from substrate.boot_core import load_seeds_into
    from substrate.world_adapter import WorldAdapter
    from domains.discourse_state import ensure_discourse_state, record_event

    world = WorldAdapter(seeds=())
    loaded = load_seeds_into(world.s, world.agent, ["communication_intent_arbitration"])
    # The production materializer expects the same graph-facing interface as
    # the live agent. Keep the substrate and registered rules native.
    agent = SimpleNamespace(s=world.s, inner=world.inner, agent=world.agent)
    speaker = world.s.add_node("Interlocutor", {"name": "trace-speaker"})
    state = ensure_discourse_state(agent,
        conversation_id=f"partition-correction-{n}-{policy}-{replicate}",
        addressee=world.agent)
    roots = {}
    current_interpretations = []
    for i in range(n):
        prior_frame, current_frame = 2 * i, 2 * i + 1
        for frame in (prior_frame, current_frame):
            roots[frame] = world.s.add_node("Microtheory", {
                "name": f"trace-{replicate}-frame-{frame}"})
        prior = record_event(agent, state, kind="instruction", speaker=speaker,
                             addressee=world.agent, topic=f"task-{i}",
                             interaction_mode="turn_compatible",
                             payload={"grounding_status": "candidate_grounded"})
        prior_i = world.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1",
            "grounding_status": "candidate_grounded",
            "language_action_target_head": f"action_{i}"})
        world.inner.add_edge_unchecked(prior, "has_interpretation", prior_i, {})
        world.inner.add_edge_unchecked(roots[prior_frame], "has_concept", prior, {})
        world.inner.add_edge_unchecked(roots[prior_frame], "has_concept", prior_i, {})

        current_event = record_event(agent, state, kind="statement", speaker=speaker,
                                     addressee=world.agent, topic=None,
                                     interaction_mode="turn_compatible",
                                     payload={"interaction_relation": "response",
                                              "grounding_status": "unresolved"})
        current_i = world.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1",
            "evidence_schema": "communication_evidence.v1",
            "language_definite_nominal_reference": 1.0,
            "language_discourse_relation": "correction",
            "language_referential_head": f"action_{i}",
            "interaction_relation": "response", "parsed_subject_pos": "noun",
            "grounding_status": "unresolved", "grounding_evidence_path": ""})
        world.inner.add_edge_unchecked(current_event, "has_interpretation", current_i, {})
        world.inner.add_edge_unchecked(world.agent, "holds_interpretation", current_i, {})
        world.inner.add_edge_unchecked(roots[current_frame], "has_concept", current_event, {})
        world.inner.add_edge_unchecked(roots[current_frame], "has_concept", current_i, {})
        current_interpretations.append(current_i)

    order = frame_order(n, policy)
    world.inner.scale_audit_reset()
    world.inner.scale_audit_per_rule_reset()
    world.inner.scale_audit_set_enabled(True)
    world.inner.scale_audit_set_per_rule_enabled(True)
    started = time.perf_counter_ns()
    if arm == "monolithic":
        work = int(world.inner.run_rules(CAP))
        sweeps, calls = 1, 1
        quiescence = []
    else:
        sweeps, calls, work = 0, 0, 0
        while True:
            sweeps += 1
            if sweeps > 100:
                raise RuntimeError("scoped trace failed to reach fixed point within 100 sweeps")
            progress = False
            for frame in order:
                steps = int(world.inner.run_rules_scoped(CAP, False, roots[frame]))
                calls += 1
                work += steps
                progress |= steps > 0
            if not progress:
                break
        quiescence = []
        for frame in order:
            report = dict(world.inner.run_rules_scoped_delta_report(roots[frame], CAP, False))
            calls += 1
            if report.get("progress_steps", 0) or report.get("deferred_effects_pending"):
                raise RuntimeError(f"scope {frame} not quiescent: {report}")
            quiescence.append({"frame": frame,
                               "progress_steps": int(report.get("progress_steps", 0)),
                               "deferred_effects_pending": bool(report.get("deferred_effects_pending"))})
    elapsed = time.perf_counter_ns() - started
    counters = {str(k): int(v) for k, v in dict(world.inner.scale_audit_snapshot()).items()}
    per_rule = []
    names = {int(i): str(name) for i, name, *_ in world.inner.rule_access_sets()}
    for i, metric, count in world.inner.scale_audit_per_rule_snapshot():
        per_rule.append({"rule_name": names.get(int(i), "unknown"),
                         "metric": str(metric), "count": int(count)})
    world.inner.scale_audit_set_per_rule_enabled(False)
    world.inner.scale_audit_set_enabled(False)
    attrs = [dict(world.s.node(node)["attrs"]) for node in current_interpretations]
    graph = world.inner.graph_to_dict()
    scope_membership = []
    for frame, root in sorted(roots.items()):
        members = list(world.inner.neighbours(root, "has_concept"))
        member_rows = [{"node_id": node_value(node),
                        "node_type": str(world.s.node(node)["type"])}
                       for node in members]
        member_rows.sort(key=lambda row: row["node_id"])
        scope_membership.append({"frame_id": frame,
            "scope_root_id": node_value(root),
            "scope_root_type": str(world.s.node(root)["type"]),
            "members": member_rows,
            "owned_node_count_including_scope_root": 1 + len(member_rows)})
    return {
        "n_tasks": n, "scope_order": policy, "arm": arm, "replicate": replicate,
        "loaded_seed_ids": sorted(loaded), "frame_count": len(roots),
        "scope_membership": scope_membership,
        "scope_sweeps": sweeps, "scope_calls": calls,
        "work_steps": work, "elapsed_ns": elapsed, "scale_counters": counters,
        "per_rule_counters": per_rule, "grounding_statuses": [a.get("grounding_status") for a in attrs],
        "evidence_paths": [a.get("grounding_evidence_path") for a in attrs],
        "all_grounded": all(a.get("grounding_status") == "candidate_grounded" for a in attrs),
        "all_expected_evidence": all(a.get("grounding_evidence_path") == EXPECTED_EVIDENCE for a in attrs),
        "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"]),
        "graph_digest": canonical_graph_digest(graph),
        "graph_serialization_digest": graph_digest(graph), "quiescence": quiescence,
    }


def worker(index: int) -> dict:
    policy = ORDERS[index % len(ORDERS)]
    replicate = index // len(ORDERS)
    rows = []
    for n in SIZES:
        mono = execute(n, policy, "monolithic", replicate)
        scoped = execute(n, policy, "scoped", replicate)
        rows.append({"n_tasks": n, "monolithic": mono, "scoped": scoped,
                     "paired": {"canonical_full_graph_equal": mono["graph_digest"] == scoped["graph_digest"],
                                "serialization_order_equal": mono["graph_serialization_digest"] == scoped["graph_serialization_digest"],
                                "semantic_grounding_equal": mono["grounding_statuses"] == scoped["grounding_statuses"] and mono["evidence_paths"] == scoped["evidence_paths"],
                                "expected_results": mono["all_grounded"] and scoped["all_grounded"] and mono["all_expected_evidence"] and scoped["all_expected_evidence"]}})
    return {"worker_index": index, "pid": os.getpid(), "scope_order": policy,
            "replicate": replicate, "rows": rows}


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        if OUT.exists():
            raise SystemExit(f"refusing to overwrite capture {OUT}")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentCorrectionTracePartitionLockV1_1",
                                    "locked_inputs": locked_inputs()}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True)); return
    locked = locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale lock; generate preregistration using --lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = str(ROOT / "runners/dsl/python") + os.pathsep + str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    started = time.perf_counter_ns()
    runs = [json.loads(subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(i)],
                                      cwd=ROOT, env=env, text=True, capture_output=True,
                                      check=True, timeout=300).stdout)
            for i in range(REPLICATES_PER_ORDER * len(ORDERS))]
    post = locked_inputs()
    cells = [row for run in runs for row in run["rows"]]
    checks = {
        "three_fresh_replicates_per_order": all(sum(r["scope_order"] == order for r in runs) == REPLICATES_PER_ORDER for order in ORDERS),
        "nine_fresh_processes": len({r["pid"] for r in runs}) == 9,
        "source_stable": post == locked,
        "all_expected_seed_ids_loaded": all("communication_intent_arbitration" in row[arm]["loaded_seed_ids"] for row in cells for arm in ("monolithic", "scoped")),
        "all_scoped_fixed_points_quiescent": all(r["scoped"]["scope_sweeps"] >= 1 and len(r["scoped"]["quiescence"]) == r["scoped"]["frame_count"] and all(not q["deferred_effects_pending"] and q["progress_steps"] == 0 for q in r["scoped"]["quiescence"]) for r in cells),
        "measured_scope_membership_is_complete": all(valid_scope_membership(row["scoped"]) for row in cells),
        "positive_semantics_and_exact_evidence": all(r["paired"]["expected_results"] for r in cells),
        "monolithic_scoped_canonical_graph_parity": all(r["paired"]["canonical_full_graph_equal"] for r in cells),
        "all_sweep_orders_semantically_equal": all(r["paired"]["semantic_grounding_equal"] for r in cells),
        "all_expected_cells_present": len(cells) == 36 and sorted({r["n_tasks"] for r in cells}) == list(SIZES),
    }
    summary = {}
    for n in SIZES:
        group = [r for r in cells if r["n_tasks"] == n]
        m = [r["monolithic"]["elapsed_ns"] / 1000 for r in group]
        s = [r["scoped"]["elapsed_ns"] / 1000 for r in group]
        summary[str(n)] = {
            "paired_cases": len(group), "canonical_graph_parity_rate": sum(r["paired"]["canonical_full_graph_equal"] for r in group) / len(group),
            "serialization_order_parity_rate": sum(r["paired"]["serialization_order_equal"] for r in group) / len(group),
            "median_monolithic_us": statistics.median(m), "median_scoped_us": statistics.median(s),
            "median_scoped_to_monolithic_ratio": statistics.median(s) / statistics.median(m),
            "median_monolithic_work_steps": statistics.median(r["monolithic"]["work_steps"] for r in group),
            "median_scoped_work_steps": statistics.median(r["scoped"]["work_steps"] for r in group),
            "median_scoped_calls": statistics.median(r["scoped"]["scope_calls"] for r in group),
            "frame_count": 2 * n,
            "total_nodes_median": statistics.median(r["scoped"]["node_count"] for r in group),
        }
    payload = {
        "schema": "ThoughtexperimentCorrectionTracePartitionV1_1",
        "claim_boundary": "Replays the production discourse event materializer and registered communication rules on repeated authored instruction/correction pairs. Exact full-graph parity tests this fixture across Microtheory sweep orders. The shared graph remains globally readable; ownership annotations are measurement inputs, not learned scopes. This is not natural-task prevalence, physical partitioning, Cow execution, or broad tractability proof.",
        "configuration": {"sizes": SIZES, "scope_orders": ORDERS,
                          "fresh_replicates_per_order": REPLICATES_PER_ORDER,
                          "ownership": "prior instruction+interpretation and current correction+interpretation occupy separate frames; DiscourseState and Agent are unowned/shared"},
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "OZMA_NO_LLM": env["OZMA_NO_LLM"],
                        "OZMA_SEED_PERSIST_DISABLED": env["OZMA_SEED_PERSIST_DISABLED"]},
        "locked_inputs": locked, "post_run_inputs": post,
        "elapsed_wall_ns": time.perf_counter_ns() - started,
        "checks": checks, "summary_by_task_count": summary, "runs": runs,
    }
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite capture {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"capture": OUT.relative_to(ROOT).as_posix(), "checks": checks,
                      "summary_by_task_count": summary}, indent=2))
    if not all(checks.values()):
        raise SystemExit("production-materialized partition trace gates failed")


if __name__ == "__main__":
    main()
