#!/usr/bin/env python3
"""Test declared scope-anchor pruning on the materialized correction trace."""
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
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_correction_trace_anchor_v1_lock_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_correction_trace_anchor_v1_20261003.json"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_correction_trace_anchor_v1.py"
PRIOR_TRACE = ROOT / "evaluation/substrate_capability/thoughtexperiment_correction_trace_partition_v1.py"
SOURCES = (
    "evaluation/substrate_capability/thoughtexperiment_correction_trace_anchor_v1.py",
    "evaluation/substrate_capability/analyze_thoughtexperiment_correction_trace_anchor_v1.py",
    "evaluation/substrate_capability/thoughtexperiment_correction_trace_partition_v1.py",
    "domains/seed_registry.py", "domains/discourse_state.py",
    "seeds/communication_intent_arbitration.json",
    "substrate/boot_core.py", "substrate/world_adapter.py",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/graph_rules.rs", "runners/dsl/src/graph.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
)
SIZES = (1, 2, 4, 8)
ORDERS = ("ascending", "descending", "outside_in")
REPLICATES_PER_ORDER = 3
CAP = 100_000
TARGET_RULE = "ground_definite_correction_from_scoped_action_target"
ANCHOR = {
    "match_type": "CommunicationInterpretation",
    "scope_anchor_var": "i",
    "scope_anchor_type": "CommunicationInterpretation",
    "scope_anchor_owner_var": "current_event",
    "scope_anchor_owner_type": "DiscourseEvent",
    "scope_anchor_owner_edge": "has_interpretation",
}
EXPECTED_EVIDENCE = "CommunicationInterpretation -> discourse-scoped DiscourseState -> prior grounded DiscourseEvent -> matching action-target head"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_inputs() -> dict:
    from substrate_rs import _native
    result = {p: sha(ROOT / p) for p in SOURCES}
    result["native_extension"] = sha(Path(_native.__file__).resolve())
    result["native_build_manifest"] = sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json")
    result["cargo_lock"] = sha(ROOT / "runners/dsl/Cargo.lock")
    result["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return result


def canonical_digest(graph: dict) -> str:
    canonical = dict(graph)
    for key in ("nodes", "edges"):
        if isinstance(canonical.get(key), list):
            canonical[key] = sorted(canonical[key], key=lambda item: json.dumps(
                item, sort_keys=True, separators=(",", ":"), default=str))
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":"),
                                    default=str).encode()).hexdigest()


def frame_order(n: int, policy: str) -> list[int]:
    values = list(range(2 * n))
    if policy == "ascending":
        return values
    if policy == "descending":
        return list(reversed(values))
    out = []
    lo, hi = 0, len(values) - 1
    while lo <= hi:
        out.append(values[lo]); lo += 1
        if lo <= hi:
            out.append(values[hi]); hi -= 1
    return out


def load_fixture_seeds(world, arm: str) -> list[str]:
    from substrate.boot_core import load_seeds_into
    import substrate.boot_core as boot_core_module
    original = boot_core_module.manifest_for
    metadata_seen = {"value": False}

    def manifest_for(seed_id: str):
        manifest = original(seed_id)
        if arm == "anchor" and seed_id == "communication_intent_arbitration":
            for rule in manifest.get("rules", []):
                if rule.get("name") == TARGET_RULE:
                    rule.update(ANCHOR)
                    metadata_seen["value"] = True
        return manifest

    boot_core_module.manifest_for = manifest_for
    try:
        loaded = load_seeds_into(world.s, world.agent, ["communication_intent_arbitration"])
    finally:
        boot_core_module.manifest_for = original
    if arm == "anchor" and not metadata_seen["value"]:
        raise RuntimeError("declared-anchor metadata was not injected into the loaded rule")
    return sorted(loaded)


def execute(n: int, policy: str, arm: str, replicate: int) -> dict:
    from types import SimpleNamespace
    from substrate.world_adapter import WorldAdapter
    from domains.discourse_state import ensure_discourse_state, record_event

    world = WorldAdapter(seeds=())
    loaded = load_fixture_seeds(world, arm)
    facade = SimpleNamespace(s=world.s, inner=world.inner, agent=world.agent)
    speaker = world.s.add_node("Interlocutor", {"name": "trace-speaker"})
    state = ensure_discourse_state(facade,
        conversation_id=f"anchor-correction-{n}-{policy}-{replicate}",
        addressee=world.agent)
    roots, interpretations = {}, []
    for i in range(n):
        pf, cf = 2 * i, 2 * i + 1
        roots[pf] = world.s.add_node("Microtheory", {"name": f"frame-{pf}"})
        roots[cf] = world.s.add_node("Microtheory", {"name": f"frame-{cf}"})
        prior = record_event(facade, state, kind="instruction", speaker=speaker,
            addressee=world.agent, topic=f"task-{i}", interaction_mode="turn_compatible",
            payload={"grounding_status": "candidate_grounded"})
        prior_i = world.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1", "grounding_status": "candidate_grounded",
            "language_action_target_head": f"action_{i}"})
        world.inner.add_edge_unchecked(prior, "has_interpretation", prior_i, {})
        world.inner.add_edge_unchecked(roots[pf], "has_concept", prior, {})
        world.inner.add_edge_unchecked(roots[pf], "has_concept", prior_i, {})
        current = record_event(facade, state, kind="statement", speaker=speaker,
            addressee=world.agent, topic=None, interaction_mode="turn_compatible",
            payload={"interaction_relation": "response", "grounding_status": "unresolved"})
        current_i = world.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1", "evidence_schema": "communication_evidence.v1",
            "language_definite_nominal_reference": 1.0, "language_discourse_relation": "correction",
            "language_referential_head": f"action_{i}", "interaction_relation": "response",
            "parsed_subject_pos": "noun", "grounding_status": "unresolved",
            "grounding_evidence_path": ""})
        world.inner.add_edge_unchecked(current, "has_interpretation", current_i, {})
        world.inner.add_edge_unchecked(world.agent, "holds_interpretation", current_i, {})
        world.inner.add_edge_unchecked(roots[cf], "has_concept", current, {})
        world.inner.add_edge_unchecked(roots[cf], "has_concept", current_i, {})
        interpretations.append(current_i)

    order = frame_order(n, policy)
    inner = world.inner
    inner.scale_audit_reset(); inner.scale_audit_per_rule_reset()
    inner.scale_audit_set_enabled(True); inner.scale_audit_set_per_rule_enabled(True)
    start = time.perf_counter_ns()
    if arm == "monolithic":
        closure_work = int(inner.run_rules(CAP))
        sweeps, calls = 1, 1
    else:
        closure_work, sweeps, calls = 0, 0, 0
        while True:
            sweeps += 1
            if sweeps > 100:
                raise RuntimeError("scoped anchor closure exceeded 100 sweeps")
            progress = False
            for frame in order:
                amount = int(inner.run_rules_scoped(CAP, False, roots[frame]))
                closure_work += amount; calls += 1; progress |= amount > 0
            if not progress:
                break
        for frame in order:
            q = dict(inner.run_rules_scoped_delta_report(roots[frame], CAP, False))
            calls += 1
            if q.get("progress_steps", 0) or q.get("deferred_effects_pending"):
                raise RuntimeError(f"scope {frame} not quiescent: {q}")
    elapsed = time.perf_counter_ns() - start
    counters = {str(k): int(v) for k, v in dict(inner.scale_audit_snapshot()).items()}
    rule_names = {int(i): str(name) for i, name, *_ in inner.rule_access_sets()}
    per_rule = []
    for index, metric, count in inner.scale_audit_per_rule_snapshot():
        per_rule.append({"rule_name": rule_names.get(int(index), "unknown"),
                         "metric": str(metric), "count": int(count)})
    inner.scale_audit_set_per_rule_enabled(False); inner.scale_audit_set_enabled(False)
    attrs = [dict(world.s.node(node)["attrs"]) for node in interpretations]
    graph = inner.graph_to_dict()
    target_rule_path = {x["metric"]: x["count"] for x in per_rule if x["rule_name"] == TARGET_RULE}
    return {
        "n_tasks": n, "scope_order": policy, "arm": arm, "replicate": replicate,
        "loaded_seed_ids": loaded, "frame_count": len(roots),
        "scope_sweeps": sweeps, "scope_calls": calls,
        "closure_work_steps": closure_work, "elapsed_ns": elapsed,
        "scale_counters": counters, "per_rule_counters": per_rule,
        "target_rule_counters": target_rule_path,
        "grounding_statuses": [a.get("grounding_status") for a in attrs],
        "evidence_paths": [a.get("grounding_evidence_path") for a in attrs],
        "all_grounded": len(attrs) == n and all(a.get("grounding_status") == "candidate_grounded" for a in attrs),
        "all_expected_evidence": all(a.get("grounding_evidence_path") == EXPECTED_EVIDENCE for a in attrs),
        "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"]),
        "canonical_graph_digest": canonical_digest(graph),
        "graph_serialization_digest": hashlib.sha256(json.dumps(graph, sort_keys=True,
            separators=(",", ":"), default=str).encode()).hexdigest(),
    }


def worker(index: int) -> dict:
    policy = ORDERS[index % len(ORDERS)]
    replicate = index // len(ORDERS)
    rows = []
    for n in SIZES:
        arms = {arm: execute(n, policy, arm, replicate)
                for arm in ("monolithic", "fallback", "anchor")}
        rows.append({"n_tasks": n, "arms": arms,
                     "paired": {
                         "fallback_matches_monolithic": arms["fallback"]["canonical_graph_digest"] == arms["monolithic"]["canonical_graph_digest"],
                         "anchor_matches_monolithic": arms["anchor"]["canonical_graph_digest"] == arms["monolithic"]["canonical_graph_digest"],
                         "anchor_matches_fallback": arms["anchor"]["canonical_graph_digest"] == arms["fallback"]["canonical_graph_digest"],
                         "semantics_all_arms": all(arms[a]["all_grounded"] and arms[a]["all_expected_evidence"] for a in arms),
                     }})
    return {"worker_index": index, "pid": os.getpid(), "scope_order": policy,
            "replicate": replicate, "rows": rows}


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        if OUT.exists():
            raise SystemExit(f"refusing to overwrite {OUT}")
        LOCK.write_text(json.dumps({"schema": "ThoughtexperimentCorrectionTraceAnchorLockV1",
                                    "locked_inputs": locked_inputs()}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True)); return
    locked = locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source lock")
    env = dict(os.environ); env.setdefault("OZMA_NO_LLM", "1"); env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = str(ROOT / "runners/dsl/python") + os.pathsep + str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    started = time.perf_counter_ns(); runs = []
    for i in range(REPLICATES_PER_ORDER * len(ORDERS)):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(i)],
            cwd=ROOT, env=env, text=True, capture_output=True, timeout=300)
        if proc.returncode:
            raise SystemExit(f"worker {i} failed ({proc.returncode}): {proc.stderr[-4000:]}")
        runs.append(json.loads(proc.stdout))
    post = locked_inputs(); cells = [row for run in runs for row in run["rows"]]
    checks = {
        "nine_fresh_processes": len({r["pid"] for r in runs}) == 9,
        "three_replicates_per_order": all(sum(r["scope_order"] == o for r in runs) == 3 for o in ORDERS),
        "source_stable": post == locked,
        "complete_panel": len(cells) == 36 and sorted({x["n_tasks"] for x in cells}) == list(SIZES),
        "all_correct_semantics": all(c["paired"]["semantics_all_arms"] for c in cells),
        "fallback_full_graph_parity": all(c["paired"]["fallback_matches_monolithic"] for c in cells),
        "anchor_full_graph_parity": all(c["paired"]["anchor_matches_monolithic"] for c in cells),
        "fallback_path_no_declared_anchor": all(
            a["arms"]["fallback"]["scale_counters"].get("scoped_declared_anchor_rule_matches", 0) == 0
            for a in cells),
        "anchor_path_exercised_on_target_rule": all(
            sum(a["arms"]["anchor"]["target_rule_counters"].get(k, 0)
                for k in ("scoped_declared_anchor", "scoped_path_declared_anchor")) > 0
            for a in cells),
    }
    summary = {}
    for n in SIZES:
        group = [c for c in cells if c["n_tasks"] == n]
        info = {"paired_cases": len(group)}
        for arm in ("monolithic", "fallback", "anchor"):
            elapsed = [c["arms"][arm]["elapsed_ns"] / 1000 for c in group]
            info[f"{arm}_median_us"] = statistics.median(elapsed)
        for metric in ("cand_enum", "term_evals_total", "rule_enumerations"):
            f = statistics.median(c["arms"]["fallback"]["scale_counters"].get(metric, 0) for c in group)
            a = statistics.median(c["arms"]["anchor"]["scale_counters"].get(metric, 0) for c in group)
            info[metric] = {"fallback_median": f, "anchor_median": a,
                            "anchor_over_fallback": a / f if f else None}
        info["anchor_target_rule_path_counts"] = {
            str(k): statistics.median(c["arms"]["anchor"]["target_rule_counters"].get(k, 0) for c in group)
            for k in sorted({k for c in group for k in c["arms"]["anchor"]["target_rule_counters"]})}
        summary[str(n)] = info
    payload = {
        "schema": "ThoughtexperimentCorrectionTraceAnchorV1",
        "claim_boundary": "Tests an opt-in declared CommunicationInterpretation/DiscourseEvent co-ownership anchor on one production-materialized correction trace. Exact canonical graph facts are compared against same-source generic fallback and monolithic closure. Shared graph visibility remains global; ownership labels are authored, so this is not physical partitioning, scope discovery, or natural-task prevalence.",
        "configuration": {"sizes": SIZES, "scope_orders": ORDERS,
            "replicates_per_order": REPLICATES_PER_ORDER,
            "anchor_rule": TARGET_RULE, "anchor_metadata": ANCHOR,
            "ownership": "current DiscourseEvent owns current CommunicationInterpretation through has_interpretation; predecessor event and target remain in another frame"},
        "environment": {"python": sys.version, "platform": platform.platform(),
            "OZMA_NO_LLM": env["OZMA_NO_LLM"], "OZMA_SEED_PERSIST_DISABLED": env["OZMA_SEED_PERSIST_DISABLED"]},
        "locked_inputs": locked, "post_run_inputs": post,
        "elapsed_wall_ns": time.perf_counter_ns() - started,
        "checks": checks, "summary_by_task_count": summary, "runs": runs,
    }
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"capture": OUT.relative_to(ROOT).as_posix(), "checks": checks,
        "summary_by_task_count": summary}, indent=2))
    if not all(checks.values()):
        raise SystemExit("anchor pruning gates failed")


if __name__ == "__main__":
    main()
