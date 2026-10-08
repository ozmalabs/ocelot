#!/usr/bin/env python3
"""Test shared-graph, frame-scoped native settlement with live boundary reads.

Each concept belongs to one frame Microtheory. The existing run_rules_scoped
path settles one frame's rule bindings against the shared graph; repeated
round-robin calls propagate cross-frame influence until a whole round is quiet.
Only CAN update rules are installed: this experiment measures state inference,
not Hebbian mint/reweight behavior.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import random
import statistics
import time
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_FILE = ROOT / "seeds/can_native_reimplementation.json"
OUT = Path(os.environ.get(
    "SUBSTRATE_CAN_BOUNDARY_OUT",
    ROOT / "evaluation/reports/substrate_can_boundary_frames_20260924.json",
))
SIZES = tuple(int(x) for x in os.environ.get("SUBSTRATE_CAN_BOUNDARY_SIZES", "16,32").split(","))
TOPOLOGIES = tuple(os.environ.get(
    "SUBSTRATE_CAN_BOUNDARY_TOPOLOGIES", "blocks4,path,banded2,complete"
).split(","))
MODES = tuple(os.environ.get("SUBSTRATE_CAN_BOUNDARY_MODES", "2state,3state").split(","))
REPLICATES = int(os.environ.get("SUBSTRATE_CAN_BOUNDARY_REPLICATES", "3"))
FRAME_SIZE = int(os.environ.get("SUBSTRATE_CAN_BOUNDARY_FRAME_SIZE", "4"))
GRANULARITY = float(os.environ.get("SUBSTRATE_CAN_BOUNDARY_GRANULARITY", "0.25"))
CAP = int(os.environ.get("SUBSTRATE_CAN_BOUNDARY_CAP", "100000"))
BETA = 2.0
THRESHOLD = math.atanh(0.5)
AUDIT_FIELDS = (
    "cand_enum", "cand_tested", "where_evals", "where_rejects",
    "leaf_visits", "bindings_cloned", "rule_enumerations",
    "term_evals_total", "term_units_total",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_pairs(n: int, topology: str):
    for a in range(n):
        for b in range(a + 1, n):
            if (topology == "complete"
                    or (topology == "path" and b == a + 1)
                    or (topology == "banded2" and b - a <= 2)
                    or (topology == "blocks4" and a // FRAME_SIZE == b // FRAME_SIZE)):
                yield a, b


def update(mode: str, h: float) -> float:
    if mode == "2state":
        return 1.0 if h >= 0.0 else -1.0
    scaled = BETA * h
    if scaled > THRESHOLD:
        return 1.0
    if scaled < -THRESHOLD:
        return -1.0
    return 0.0


def inference_manifest(seed_doc, mode):
    from substrate.seed_loader import engine_rules_only
    manifest = dict(engine_rules_only(seed_doc))
    wanted = f"can_native_update_{mode}"
    manifest["rules"] = [r for r in manifest.get("rules", []) if r.get("name") == wanted]
    if len(manifest["rules"]) != 1:
        raise RuntimeError(f"expected one update rule named {wanted}")
    return manifest


def build_engine(sr, manifest, mode, fields, weights, memberships):
    n = len(fields)
    inner = sr.Substrate()._inner
    inner.load_seed_manifest(manifest)
    count = (n + FRAME_SIZE - 1) // FRAME_SIZE if memberships == "frames" else 1
    mts = [inner.add_node("Microtheory", {
        "temperature": BETA, "discrete_mode": mode, "can_tick": 0,
    }) for _ in range(count)]
    concepts = [inner.add_node("Concept", {
        "name": f"c{i}", "state": 0.0,
        "external_field": fields[i], "identity_field": 0.0,
    }) for i in range(n)]
    for i, concept in enumerate(concepts):
        mi = i // FRAME_SIZE if memberships == "frames" else 0
        inner.add_edge(mts[mi], "has_concept", concept, {})
    for (a, b), weight in weights.items():
        inner.add_edge(concepts[a], "causal_influence", concepts[b], {"weight": weight})
    return inner, mts, concepts


def residuals(mode, fields, weights, states):
    out = []
    for a, state in enumerate(states):
        h = fields[a] + sum(weights.get((a, b), 0.0) * states[b]
                            for b in range(len(states)))
        out.append(update(mode, h) != state)
    return out


def scale_audit_snapshot(inner):
    raw = dict(inner.scale_audit_snapshot())
    return {key: raw.get(key, 0) for key in AUDIT_FIELDS}


def add_audit_counts(target, source):
    for key in AUDIT_FIELDS:
        target[key] = target.get(key, 0) + source.get(key, 0)


def audited_monolithic(sr, manifest, mode, fields, weights):
    inner, _, nodes = build_engine(sr, manifest, mode, fields, weights, "global")
    inner.scale_audit_reset()
    inner.scale_audit_set_enabled(True)
    progress = inner.run_rules(CAP)
    counts = scale_audit_snapshot(inner)
    inner.scale_audit_set_enabled(False)
    states = [float(inner.node(x)["attrs"].get("state", 0.0)) for x in nodes]
    return progress, states, counts


def audited_round_robin(sr, manifest, mode, fields, weights):
    inner, mts, nodes = build_engine(sr, manifest, mode, fields, weights, "frames")
    per_frame = [dict.fromkeys(AUDIT_FIELDS, 0) for _ in mts]
    total_steps = 0
    for _round in range(100_000):
        progress_this_round = 0
        for frame, mt in enumerate(mts):
            remaining = CAP - total_steps
            if remaining <= 0:
                break
            inner.scale_audit_reset()
            inner.scale_audit_set_enabled(True)
            steps = inner.run_rules_scoped(remaining, False, mt)
            add_audit_counts(per_frame[frame], scale_audit_snapshot(inner))
            inner.scale_audit_set_enabled(False)
            total_steps += steps
            progress_this_round += steps
        if total_steps >= CAP or progress_this_round == 0:
            break
    states = [float(inner.node(x)["attrs"].get("state", 0.0)) for x in nodes]
    return total_steps, states, per_frame


def overlap_fallback_probe(sr, seed_doc):
    """Ensure ambiguous shared membership retains the generic scope semantics."""
    from substrate.seed_loader import engine_rules_only
    manifest = dict(engine_rules_only(seed_doc))
    manifest["rules"] = [r for r in manifest.get("rules", [])
                         if r.get("name") in {"can_native_update_2state", "can_native_update_3state"}]
    inner = sr.Substrate()._inner
    inner.load_seed_manifest(manifest)
    target_mt = inner.add_node("Microtheory", {
        "temperature": BETA, "discrete_mode": "3state", "can_tick": 0,
    })
    foreign_mt = inner.add_node("Microtheory", {
        "temperature": BETA, "discrete_mode": "2state", "can_tick": 0,
    })
    shared = inner.add_node("Concept", {
        "name": "shared", "state": 0.0,
        "external_field": 0.1, "identity_field": 0.0,
    })
    inner.add_edge(target_mt, "has_concept", shared, {})
    inner.add_edge(foreign_mt, "has_concept", shared, {})
    first_steps = inner.run_rules_scoped(10, False, target_mt)
    after_first = float(inner.node(shared)["attrs"].get("state", 0.0))
    resumed_steps = inner.run_rules_scoped(1, False, target_mt)
    after_resume = float(inner.node(shared)["attrs"].get("state", 0.0))
    return {
        "overlapping_membership": True,
        "first_budget": 10, "first_steps": first_steps,
        "state_after_first": after_first,
        "resumed_budget": 1, "resumed_steps": resumed_steps,
        "state_after_resume": after_resume,
        "expected_generic_fallback_behavior": first_steps == 10 and after_first == 0.0
            and resumed_steps == 1 and after_resume == 1.0,
    }


def run_dependency_wakeups(inner, mts, nodes, weights, frame_count, audit_by_frame=None):
    """Conservative CAN-specific frame wakeups over static causal edges.

    If target state changes, wake each frame owning a source with an edge to
    that target, since the source update reads outgoing causal neighbours.
    Intra-frame dependencies are handled by scoped settlement itself.
    """
    dependents = [set() for _ in range(frame_count)]
    for source, target in weights:
        source_frame, target_frame = source // FRAME_SIZE, target // FRAME_SIZE
        if source_frame != target_frame:
            dependents[target_frame].add(source_frame)

    queue = deque(range(frame_count))
    queued = set(range(frame_count))
    total_steps = turns = notification_enqueues = changed_turns = 0
    cap_reached = False
    while queue:
        if turns >= 100_000 or total_steps >= CAP:
            cap_reached = True
            break
        frame = queue.popleft()
        queued.remove(frame)
        begin = frame * FRAME_SIZE
        before = [float(inner.node(nodes[i])["attrs"].get("state", 0.0))
                  for i in range(begin, begin + FRAME_SIZE)]
        remaining = CAP - total_steps
        if audit_by_frame is not None:
            inner.scale_audit_reset()
            inner.scale_audit_set_enabled(True)
        steps = inner.run_rules_scoped(remaining, False, mts[frame])
        if audit_by_frame is not None:
            add_audit_counts(audit_by_frame[frame], scale_audit_snapshot(inner))
            inner.scale_audit_set_enabled(False)
        turns += 1
        total_steps += steps
        after = [float(inner.node(nodes[i])["attrs"].get("state", 0.0))
                 for i in range(begin, begin + FRAME_SIZE)]
        changed = [begin + i for i, (a, b) in enumerate(zip(before, after)) if a != b]
        if changed:
            changed_turns += 1
        for target in changed:
            for dependent in dependents[target // FRAME_SIZE]:
                if dependent not in queued:
                    queue.append(dependent)
                    queued.add(dependent)
                    notification_enqueues += 1
    states = [float(inner.node(x)["attrs"].get("state", 0.0)) for x in nodes]
    terminal = [inner.run_rules_scoped(1, False, mt) for mt in mts]
    return {
        "steps": total_steps, "turns": turns,
        "notification_enqueues": notification_enqueues,
        "changed_frame_turns": changed_turns,
        "budget_complete": not cap_reached,
        "states": states, "terminal_probes": terminal,
    }


def main() -> None:
    import substrate_rs as sr
    from substrate_rs import _native

    seed_doc = json.loads(SEED_FILE.read_text())
    rows = []
    overlap_probe = overlap_fallback_probe(sr, seed_doc)
    started = time.perf_counter()
    for n in SIZES:
        if n % FRAME_SIZE:
            raise ValueError(f"N={n} must be divisible by frame size {FRAME_SIZE}")
        for topology in TOPOLOGIES:
            for mode in MODES:
                manifest = inference_manifest(seed_doc, mode)
                for replicate in range(REPLICATES):
                    seed = 20260924 + n * 1000 + replicate
                    frng = random.Random(seed * 53 + n)
                    prng = random.Random(seed * 31 + n)
                    fields = [frng.uniform(-1.0, 1.0) for _ in range(n)]
                    weights: dict[tuple[int, int], float] = {}
                    for a, b in make_pairs(n, topology):
                        w = round(prng.uniform(-1.0, 1.0) / GRANULARITY) * GRANULARITY
                        weights[a, b] = w
                        weights[b, a] = w
                    cross_directed = sum((a // FRAME_SIZE) != (b // FRAME_SIZE)
                                         for a, b in weights)

                    mono, _, mono_nodes = build_engine(
                        sr, manifest, mode, fields, weights, "global"
                    )
                    mono_t0, mono_c0 = time.perf_counter_ns(), time.process_time_ns()
                    mono_steps = mono.run_rules(CAP)
                    mono_wall = time.perf_counter_ns() - mono_t0
                    mono_cpu = time.process_time_ns() - mono_c0
                    mono_states = [float(mono.node(x)["attrs"].get("state", 0.0))
                                   for x in mono_nodes]
                    mono_terminal = mono.run_rules(1)

                    audit_mono_progress, audit_mono_states, audit_mono_counts = audited_monolithic(
                        sr, manifest, mode, fields, weights
                    )
                    audit_rr_steps, audit_rr_states, audit_rr_frames = audited_round_robin(
                        sr, manifest, mode, fields, weights
                    )

                    scoped, mts, scoped_nodes = build_engine(
                        sr, manifest, mode, fields, weights, "frames"
                    )
                    scoped_t0, scoped_c0 = time.perf_counter_ns(), time.process_time_ns()
                    rounds = 0
                    total_scoped_steps = 0
                    round_steps = []
                    cap_reached = False
                    while total_scoped_steps < CAP:
                        rounds += 1
                        progress_this_round = 0
                        per_frame = []
                        for mt in mts:
                            remaining = CAP - total_scoped_steps
                            if remaining <= 0:
                                cap_reached = True
                                break
                            steps = scoped.run_rules_scoped(remaining, False, mt)
                            per_frame.append(steps)
                            total_scoped_steps += steps
                            progress_this_round += steps
                        round_steps.append(per_frame)
                        if cap_reached or total_scoped_steps >= CAP:
                            cap_reached = True
                            break
                        if progress_this_round == 0:
                            break
                    scoped_wall = time.perf_counter_ns() - scoped_t0
                    scoped_cpu = time.process_time_ns() - scoped_c0
                    scoped_states = [float(scoped.node(x)["attrs"].get("state", 0.0))
                                     for x in scoped_nodes]
                    scoped_terminal = []
                    for mt in mts:
                        scoped_terminal.append(scoped.run_rules_scoped(1, False, mt))

                    event, event_mts, event_nodes = build_engine(
                        sr, manifest, mode, fields, weights, "frames"
                    )
                    event_t0, event_c0 = time.perf_counter_ns(), time.process_time_ns()
                    event_result = run_dependency_wakeups(
                        event, event_mts, event_nodes, weights, len(event_mts)
                    )
                    event_wall = time.perf_counter_ns() - event_t0
                    event_cpu = time.process_time_ns() - event_c0

                    audit_event, audit_event_mts, audit_event_nodes = build_engine(
                        sr, manifest, mode, fields, weights, "frames"
                    )
                    event_audit_frames = [dict.fromkeys(AUDIT_FIELDS, 0) for _ in audit_event_mts]
                    audit_event_result = run_dependency_wakeups(
                        audit_event, audit_event_mts, audit_event_nodes, weights,
                        len(audit_event_mts), event_audit_frames
                    )

                    mono_res = residuals(mode, fields, weights, mono_states)
                    scoped_res = residuals(mode, fields, weights, scoped_states)
                    event_res = residuals(mode, fields, weights, event_result["states"])
                    rows.append({
                        "n": n, "topology": topology, "mode": mode,
                        "replicate": replicate, "seed": seed,
                        "frame_size": FRAME_SIZE, "frame_count": len(mts),
                        "directed_edges": len(weights), "cross_frame_directed_edges": cross_directed,
                        "monolithic_steps": mono_steps,
                        "scoped_total_steps": total_scoped_steps,
                        "scoped_round_count": rounds,
                        "scoped_round_frame_steps": round_steps,
                        "monolithic_budget_complete": mono_steps < CAP,
                        "scoped_budget_complete": not cap_reached,
                        "monolithic_terminal_probe": mono_terminal,
                        "scoped_frame_terminal_probes": scoped_terminal,
                        "monolithic_fixed_point_residuals": sum(mono_res),
                        "scoped_fixed_point_residuals": sum(scoped_res),
                        "exact_state_match": mono_states == scoped_states,
                        "both_full_graph_fixed_points": sum(mono_res) == 0 and sum(scoped_res) == 0,
                        "monolithic_wall_ns": mono_wall, "monolithic_cpu_ns": mono_cpu,
                        "scoped_round_robin_wall_ns": scoped_wall,
                        "scoped_round_robin_cpu_ns": scoped_cpu,
                        "dependency_wakeup_total_steps": event_result["steps"],
                        "dependency_wakeup_frame_turns": event_result["turns"],
                        "dependency_wakeup_notification_enqueues": event_result["notification_enqueues"],
                        "dependency_wakeup_changed_frame_turns": event_result["changed_frame_turns"],
                        "dependency_wakeup_budget_complete": event_result["budget_complete"],
                        "dependency_wakeup_terminal_probes": event_result["terminal_probes"],
                        "dependency_wakeup_fixed_point_residuals": sum(event_res),
                        "dependency_wakeup_exact_state_match": mono_states == event_result["states"],
                        "dependency_wakeup_both_full_graph_fixed_points": sum(mono_res) == 0 and sum(event_res) == 0,
                        "dependency_wakeup_wall_ns": event_wall,
                        "dependency_wakeup_cpu_ns": event_cpu,
                        "audit_monolithic_progress_matches": audit_mono_progress == mono_steps,
                        "audit_monolithic_state_matches": audit_mono_states == mono_states,
                        "audit_round_robin_progress_matches": audit_rr_steps == total_scoped_steps,
                        "audit_round_robin_state_matches": audit_rr_states == scoped_states,
                        "audit_dependency_wakeup_state_matches": audit_event_result["states"] == event_result["states"],
                        "audit_dependency_wakeup_steps_match": audit_event_result["steps"] == event_result["steps"],
                        "audit_monolithic_counters": audit_mono_counts,
                        "audit_round_robin_frame_counters": audit_rr_frames,
                        "audit_dependency_wakeup_frame_counters": event_audit_frames,
                        "monolithic_states": [int(x) for x in mono_states],
                        "scoped_states": [int(x) for x in scoped_states],
                        "dependency_wakeup_states": [int(x) for x in event_result["states"]],
                    })
                    print(f"N={n} {topology} {mode} rep={replicate + 1}/{REPLICATES} "
                          f"cross={cross_directed} rounds={rounds} exact={mono_states == scoped_states} "
                          f"res={sum(scoped_res)}", flush=True)

    groups = []
    for n in SIZES:
        for topology in TOPOLOGIES:
            for mode in MODES:
                group = [x for x in rows if (x["n"], x["topology"], x["mode"]) == (n, topology, mode)]
                groups.append({
                    "n": n, "topology": topology, "mode": mode, "replicates": len(group),
                    "cross_frame_directed_edges": group[0]["cross_frame_directed_edges"],
                    "exact_state_match_replicates": sum(x["exact_state_match"] for x in group),
                    "both_fixed_point_replicates": sum(x["both_full_graph_fixed_points"] for x in group),
                    "dependency_wakeup_exact_state_match_replicates": sum(x["dependency_wakeup_exact_state_match"] for x in group),
                    "dependency_wakeup_both_fixed_point_replicates": sum(x["dependency_wakeup_both_full_graph_fixed_points"] for x in group),
                    "median_dependency_wakeup_turns": statistics.median(x["dependency_wakeup_frame_turns"] for x in group),
                    "all_scoped_budget_complete": all(x["scoped_budget_complete"] for x in group),
                    "all_dependency_wakeup_budget_complete": all(x["dependency_wakeup_budget_complete"] for x in group),
                    "median_scoped_rounds": statistics.median(x["scoped_round_count"] for x in group),
                    "median_monolithic_wall_ns": int(statistics.median(x["monolithic_wall_ns"] for x in group)),
                    "median_scoped_round_robin_wall_ns": int(statistics.median(x["scoped_round_robin_wall_ns"] for x in group)),
                    "median_monolithic_cpu_ns": int(statistics.median(x["monolithic_cpu_ns"] for x in group)),
                    "median_scoped_round_robin_cpu_ns": int(statistics.median(x["scoped_round_robin_cpu_ns"] for x in group)),
                    "median_dependency_wakeup_wall_ns": int(statistics.median(x["dependency_wakeup_wall_ns"] for x in group)),
                    "median_dependency_wakeup_cpu_ns": int(statistics.median(x["dependency_wakeup_cpu_ns"] for x in group)),
                    "all_audited_outcomes_match": all(
                        x["audit_monolithic_progress_matches"] and x["audit_monolithic_state_matches"]
                        and x["audit_round_robin_progress_matches"] and x["audit_round_robin_state_matches"]
                        and x["audit_dependency_wakeup_state_matches"] and x["audit_dependency_wakeup_steps_match"] for x in group
                    ),
                })
    payload = {
        "run_id": "substrate-can-boundary-frames-20260924",
        "question": "Can frame-scoped native rule settlement with live shared-graph boundary reads reach a monolithic-equivalent fixed point?",
        "scope_limit": "Sequential run_rules_scoped calls share one graph and see live boundary state. Matcher prebinding is enabled only for the proven single has_concept edge case; ambiguous memberships retain generic post-match filtering. The dependency-wakeup variant uses a CAN-specific static causal-edge dependency set and enqueues a source frame when an outgoing-neighbour target changes. This is not parallel GALS and has no explicit boundary payloads.",
        "counter_protocol": "Separate audited twins for monolithic, round-robin, and dependency-wakeup paths. Audit is reset before every frame call so per-frame candidate/where/leaf/term work is retained; audited outcomes must match unaudited outcomes. Audit timings are discarded.",
        "rules": "Only the active CAN discrete update rule for the selected mode; Hebbian mint/reweight rules are excluded.",
        "scope_pushdown_fallback_probe": overlap_probe,
        "configuration": {"sizes": SIZES, "topologies": TOPOLOGIES, "modes": MODES,
                          "replicates": REPLICATES, "frame_size": FRAME_SIZE,
                          "weight_granularity": GRANULARITY, "rule_budget_per_execution": CAP},
        "runtime": {"elapsed_seconds": time.perf_counter() - started,
                    "python": platform.python_version(), "platform": platform.platform(),
                    "processor": platform.processor()},
        "provenance": {
            "script_sha256": sha(Path(__file__).resolve()),
            "seed_manifest_sha256": sha(SEED_FILE),
            "native_extension": str(Path(_native.__file__).resolve()),
            "native_extension_sha256": sha(Path(_native.__file__).resolve()),
            "substrate_source_sha256": sha(ROOT / "runners/dsl/src/substrate.rs"),
            "rewrite_source_sha256": sha(ROOT / "runners/dsl/src/rewrite.rs"),
            "term_source_sha256": sha(ROOT / "runners/dsl/src/term.rs"),
            "pythonpath": os.environ.get("PYTHONPATH", ""), "cwd": str(ROOT),
            "command": "PYTHONPATH=<temporary-native-package>:$PWD python3 scripts/substrate_can_boundary_frames.py",
        },
        "summaries": groups, "workers": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    checks = {
        "all_monolithic_within_budget": all(x["monolithic_budget_complete"] for x in rows),
        "all_scoped_within_budget": all(x["scoped_budget_complete"] for x in rows),
        "all_dependency_wakeup_within_budget": all(x["dependency_wakeup_budget_complete"] for x in rows),
        "all_monolithic_fixed_points": all(x["monolithic_terminal_probe"] == 0 and x["monolithic_fixed_point_residuals"] == 0 for x in rows),
        "all_scoped_fixed_points": all(x["scoped_fixed_point_residuals"] == 0 and all(v == 0 for v in x["scoped_frame_terminal_probes"]) for x in rows),
        "all_dependency_wakeup_fixed_points": all(x["dependency_wakeup_fixed_point_residuals"] == 0 and all(v == 0 for v in x["dependency_wakeup_terminal_probes"]) for x in rows),
        "all_audited_outcomes_match": all(
            x["audit_monolithic_progress_matches"] and x["audit_monolithic_state_matches"]
            and x["audit_round_robin_progress_matches"] and x["audit_round_robin_state_matches"]
            and x["audit_dependency_wakeup_state_matches"] and x["audit_dependency_wakeup_steps_match"] for x in rows
        ),
        "ambiguous_membership_uses_generic_fallback": overlap_probe["expected_generic_fallback_behavior"],
    }
    print(json.dumps({"workers": len(rows), "groups": len(groups), "checks": checks, "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("one or more boundary-frame correctness gates failed")


if __name__ == "__main__":
    main()
