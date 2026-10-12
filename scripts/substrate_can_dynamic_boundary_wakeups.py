#!/usr/bin/env python3
"""Measure frame wakeup recall after CAN graph and node-state perturbations.

Two copies are settled to the same full-graph fixed point. Both receive the
same mutation. One copy resumes from frames directly affected by the write and
then propagates state changes through the current causal dependency graph; the
reference fully rescans every frame. A local-update oracle checks both results.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_can_dynamic_boundary_wakeups_20260924.json"
FRAME_SIZE = 4
BETA = 2.0
THRESHOLD = math.atanh(0.5)
CAP = 100_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def update(field: float, weights: dict[tuple[int, int], float], states: list[float], node: int) -> float:
    h = field + sum(w * states[tgt] for (src, tgt), w in weights.items() if src == node)
    scaled = BETA * h
    if scaled > THRESHOLD:
        return 1.0
    if scaled < -THRESHOLD:
        return -1.0
    return 0.0


def build(sr, manifest, fields, weights):
    outer = sr.Substrate()
    inner = outer._inner
    inner.load_seed_manifest(manifest)
    mts = [inner.add_node("Microtheory", {
        "temperature": BETA, "discrete_mode": "3state", "can_tick": 0,
    }) for _ in range(2)]
    nodes = [inner.add_node("Concept", {
        "name": f"c{i}", "state": 0.0,
        "external_field": fields[i], "identity_field": 0.0,
    }) for i in range(len(fields))]
    for i, node in enumerate(nodes):
        inner.add_edge(mts[i // FRAME_SIZE], "has_concept", node, {})
    for (src, tgt), weight in weights.items():
        outer.add_edge_unchecked(nodes[src], "causal_influence", nodes[tgt], {"weight": weight})
    return outer, inner, mts, nodes


def states(inner, nodes):
    return [float(inner.node(n)["attrs"].get("state", 0.0)) for n in nodes]


def fields_now(inner, nodes):
    return [float(inner.node(n)["attrs"].get("external_field", 0.0)) for n in nodes]


def settle_all(inner, mts, cap=CAP):
    total = 0
    for _ in range(cap):
        moved = 0
        for mt in mts:
            remaining = cap - total
            if remaining <= 0:
                break
            steps = inner.run_rules_scoped(remaining, False, mt)
            moved += steps
            total += steps
            if total >= cap:
                break
        if moved == 0 or total >= cap:
            return total, moved == 0
    return total, False


def settle_event(inner, mts, nodes, weights, seed_frames, cap=CAP):
    frame_count = len(mts)
    dependents = [set() for _ in range(frame_count)]
    for src, tgt in weights:
        sf, tf = src // FRAME_SIZE, tgt // FRAME_SIZE
        if sf != tf:
            dependents[tf].add(sf)
    queue = list(sorted(set(seed_frames)))
    queued = set(queue)
    steps = turns = 0
    while queue and turns < cap and steps < cap:
        frame = queue.pop(0)
        queued.remove(frame)
        begin = frame * FRAME_SIZE
        before = [float(inner.node(nodes[i])["attrs"].get("state", 0.0))
                  for i in range(begin, min(begin + FRAME_SIZE, len(nodes)))]
        count = inner.run_rules_scoped(cap - steps, False, mts[frame])
        steps += count
        turns += 1
        after = [float(inner.node(nodes[i])["attrs"].get("state", 0.0))
                 for i in range(begin, min(begin + FRAME_SIZE, len(nodes)))]
        if before != after:
            for dependent in dependents[frame]:
                if dependent not in queued:
                    queue.append(dependent)
                    queued.add(dependent)
    return steps, not queue and steps < cap, turns


def residuals(inner, nodes, weights):
    ss, ff = states(inner, nodes), fields_now(inner, nodes)
    return [update(ff[i], weights, ss, i) != ss[i] for i in range(len(nodes))]


def make_case(sr, manifest, mutation):
    n = 8
    fields = [0.0 for _ in range(n)]
    fields[3], fields[4] = 1.0, -0.1
    weights: dict[tuple[int, int], float] = {}
    for a in range(n - 1):
        if a == 3 and mutation == "insert_boundary_edge":
            continue
        w = 0.75 if a == 3 else (0.25 if a % 2 == 0 else -0.25)
        weights[a, a + 1] = w
        weights[a + 1, a] = w
    left = build(sr, manifest, fields, weights)
    right = build(sr, manifest, fields, weights)
    louter, lin, lmts, lnodes = left
    router, rin, rmts, rnodes = right
    initial_l, ok_l = settle_all(lin, lmts)
    initial_r, ok_r = settle_all(rin, rmts)
    if not (ok_l and ok_r and states(lin, lnodes) == states(rin, rnodes)):
        raise RuntimeError("initial reference copies did not settle identically")
    miss_copy = None
    if mutation == "insert_boundary_edge":
        miss_copy = build(sr, manifest, fields, weights)
        mouter, minner, mmts, mnodes = miss_copy
        initial_m, ok_m = settle_all(minner, mmts)
        if not ok_m or states(minner, mnodes) != states(lin, lnodes):
            raise RuntimeError("missed-notification control did not share initial state")

    pre_mutation_state = states(lin, lnodes)
    direct_frames: set[int]
    if mutation in {"insert_boundary_edge", "delete_boundary_edge", "replace_boundary_weight"}:
        src, tgt, weight = 3, 4, 0.75
        copies = [(louter, lnodes), (router, rnodes)]
        if miss_copy is not None:
            copies.append((miss_copy[0], miss_copy[3]))
        for outer, nodes in copies:
            if mutation == "insert_boundary_edge":
                outer.add_edge_unchecked(nodes[src], "causal_influence", nodes[tgt], {"weight": weight})
                outer.add_edge_unchecked(nodes[tgt], "causal_influence", nodes[src], {"weight": weight})
            elif mutation == "replace_boundary_weight":
                outer.add_edge_unchecked(nodes[src], "causal_influence", nodes[tgt], {"weight": -weight})
                outer.add_edge_unchecked(nodes[tgt], "causal_influence", nodes[src], {"weight": -weight})
            else:
                outer.remove_edge(nodes[src], "causal_influence", nodes[tgt])
                outer.remove_edge(nodes[tgt], "causal_influence", nodes[src])
        if mutation == "insert_boundary_edge":
            weights[src, tgt] = weights[tgt, src] = weight
        elif mutation == "replace_boundary_weight":
            weights[src, tgt] = weights[tgt, src] = -weight
        else:
            weights.pop((src, tgt), None)
            weights.pop((tgt, src), None)
        direct_frames = {src // FRAME_SIZE, tgt // FRAME_SIZE}
    else:
        node = 0
        for outer, nodes in ((louter, lnodes), (router, rnodes)):
            outer.set_attr(nodes[node], "external_field", 1.0)
        fields[node] = 1.0
        direct_frames = {node // FRAME_SIZE}

    event_steps, event_complete, event_turns = settle_event(
        lin, lmts, lnodes, weights, direct_frames
    )
    full_steps, full_complete = settle_all(rin, rmts)
    event_state, full_state = states(lin, lnodes), states(rin, rnodes)
    event_residual, full_residual = residuals(lin, lnodes, weights), residuals(rin, rnodes, weights)
    missed_notification = None
    if miss_copy is not None:
        mouter, minner, mmts, mnodes = miss_copy
        missed_notification = {
            "seeded_frames": [],
            "steps": 0,
            "states": states(minner, mnodes),
            "residual_count": sum(residuals(minner, mnodes, weights)),
            "detects_stale_frame": states(minner, mnodes) != full_state,
        }
    return {
        "case": mutation,
        "initial_steps": {"event_copy": initial_l, "full_scan_copy": initial_r},
        "pre_mutation_states": pre_mutation_state,
        "directly_notified_frames": sorted(direct_frames),
        "event": {"steps": event_steps, "turns": event_turns, "complete": event_complete,
                  "states": event_state, "residual_count": sum(event_residual)},
        "missed_notification_control": missed_notification,
        "full_rescan": {"steps": full_steps, "complete": full_complete,
                         "states": full_state, "residual_count": sum(full_residual)},
        "equal_terminal_state": event_state == full_state,
        "mutation_changed_state": event_state != pre_mutation_state,
        "both_full_graph_fixed_points": not any(event_residual) and not any(full_residual),
    }


def main():
    import substrate_rs as sr
    from substrate.seed_loader import engine_rules_only
    from substrate_rs import _native

    seed_doc = json.loads((ROOT / "seeds/can_native_reimplementation.json").read_text())
    manifest = dict(engine_rules_only(seed_doc))
    manifest["rules"] = [r for r in manifest.get("rules", [])
                         if r.get("name") == "can_native_update_3state"]
    if len(manifest["rules"]) != 1:
        raise RuntimeError("expected exactly one 3-state CAN update rule")
    cases = [make_case(sr, manifest, name)
             for name in ("insert_boundary_edge", "delete_boundary_edge",
                          "replace_boundary_weight", "external_field_change")]
    result = {
        "protocol": "CAN dynamic boundary wakeup recall pilot v1",
        "claim_boundary": [
            "Four deterministic post-settlement perturbations on an eight-node path with two four-node frames.",
            "The event path is explicitly notified of frames directly affected by external writes; this does not test native writer-to-scheduler notification.",
            "The full-rescan copy is the schedule reference; independently computed CAN residuals check fixed-point validity.",
            "This does not establish general rule-family wakeup completeness or scale behavior.",
        ],
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "native_extension": str(Path(_native.__file__).resolve()),
                        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
                        "harness_sha256": sha(Path(__file__)),
                        "seed_manifest_sha256": sha(ROOT / "seeds/can_native_reimplementation.json"),
                        "source_sha256": {name: sha(ROOT / "runners/dsl/src" / name)
                                          for name in ("rewrite.rs", "substrate.rs", "term.rs")}},
        "cases": cases,
        "all_event_runs_match_full_rescan_and_reach_fixed_points": all(
            c["equal_terminal_state"] and c["mutation_changed_state"]
            and c["both_full_graph_fixed_points"]
            and c["event"]["complete"] and c["full_rescan"]["complete"] for c in cases
        ),
        "missed_notification_control_detects_staleness": all(
            c["missed_notification_control"] is None
            or c["missed_notification_control"]["detects_stale_frame"]
            and c["missed_notification_control"]["residual_count"] > 0
            for c in cases
        ),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)),
                      "all_pass": result["all_event_runs_match_full_rescan_and_reach_fixed_points"],
                      "missed_notification_control_detects_staleness": result["missed_notification_control_detects_staleness"],
                      "cases": [{k: c[k] for k in ("case", "equal_terminal_state", "both_full_graph_fixed_points")}
                                for c in cases]}, indent=2))
    if not (result["all_event_runs_match_full_rescan_and_reach_fixed_points"]
            and result["missed_notification_control_detects_staleness"]):
        raise SystemExit("dynamic wakeup run disagreed with full rescan or failed the fixed-point oracle")


if __name__ == "__main__":
    main()
