#!/usr/bin/env python3
"""Run the preregistered CAN cross-frame mutation matrix."""
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_can_boundary_mutation_matrix_20260925.json"
FRAME_SIZE = 4
BETA = 2.0
THRESHOLD = math.atanh(0.5)
CAP = 100_000
MUTATIONS = (
    "insert_boundary_edge", "delete_boundary_edge", "replace_boundary_weight",
    "external_field_change", "identity_field_change", "node_birth",
    "node_deletion", "mixed_weight_and_field_change",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(sr, manifest, n: int, fields: list[float], weights: dict):
    outer = sr.Substrate()
    inner = outer._inner
    inner.load_seed_manifest(manifest)
    mts = [inner.add_node("Microtheory", {
        "temperature": BETA, "discrete_mode": "3state", "can_tick": 0,
    }) for _ in range(n // FRAME_SIZE)]
    nodes = [inner.add_node("Concept", {
        "name": f"c{i}", "state": 0.0,
        "external_field": fields[i], "identity_field": 0.0,
    }) for i in range(n)]
    node_frames = [i // FRAME_SIZE for i in range(n)]
    active = [True] * n
    for i, node in enumerate(nodes):
        inner.add_edge(mts[node_frames[i]], "has_concept", node, {})
    for (src, tgt), weight in weights.items():
        outer.add_edge_unchecked(nodes[src], "causal_influence", nodes[tgt], {"weight": weight})
    return outer, inner, mts, nodes, node_frames, active


def state_vector(inner, nodes, active):
    return [float(inner.node(node)["attrs"].get("state", 0.0)) if live else None
            for node, live in zip(nodes, active)]


def effective_fields(inner, nodes, active):
    values = []
    for node, live in zip(nodes, active):
        if not live:
            values.append(None)
            continue
        attrs = inner.node(node)["attrs"]
        values.append(float(attrs.get("external_field", 0.0))
                      + float(attrs.get("identity_field", 0.0)))
    return values


def settle_all(inner, mts, cap=CAP):
    total = 0
    rounds = 0
    for _ in range(cap):
        moved = 0
        rounds += 1
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
            return total, moved == 0, rounds
    return total, False, rounds


def settle_event(inner, mts, nodes, node_frames, active, weights, seed_frames, cap=CAP):
    frame_count = len(mts)
    dependents = [set() for _ in range(frame_count)]
    for src, tgt in weights:
        sf, tf = node_frames[src], node_frames[tgt]
        if sf != tf:
            dependents[tf].add(sf)
    queue = list(sorted(set(seed_frames)))
    queued = set(queue)
    steps = turns = 0
    while queue and turns < cap and steps < cap:
        frame = queue.pop(0)
        queued.remove(frame)
        before = [value for i, value in enumerate(state_vector(inner, nodes, active))
                  if node_frames[i] == frame]
        count = inner.run_rules_scoped(cap - steps, False, mts[frame])
        steps += count
        turns += 1
        after = [value for i, value in enumerate(state_vector(inner, nodes, active))
                 if node_frames[i] == frame]
        if before != after:
            for dependent in dependents[frame]:
                if dependent not in queued:
                    queue.append(dependent)
                    queued.add(dependent)
    return steps, not queue and steps < cap, turns


def residuals(inner, nodes, active, weights):
    state = state_vector(inner, nodes, active)
    fields = effective_fields(inner, nodes, active)
    result = []
    for node, live in enumerate(active):
        if not live:
            result.append(False)
            continue
        h = fields[node] + sum(weight * state[tgt]
                               for (src, tgt), weight in weights.items() if src == node)
        scaled = BETA * h
        expected = 1.0 if scaled > THRESHOLD else -1.0 if scaled < -THRESHOLD else 0.0
        result.append(expected != state[node])
    return result


def initial_model(n: int):
    fields = [0.0] * n
    fields[3], fields[4] = 1.0, -0.1
    weights = {}
    for a in range(n - 1):
        w = 0.75 if a == 3 else (0.25 if a % 2 == 0 else -0.25)
        weights[a, a + 1] = weights[a + 1, a] = w
    return fields, weights


def mutate_one(outer, inner, mts, nodes, node_frames, active, weights, mutation, n):
    def edge(src, tgt, weight):
        outer.add_edge_unchecked(nodes[src], "causal_influence", nodes[tgt], {"weight": weight})

    if mutation in {"insert_boundary_edge", "replace_boundary_weight", "mixed_weight_and_field_change"}:
        weight = 0.75 if mutation == "insert_boundary_edge" else -0.75
        edge(3, 4, weight)
        edge(4, 3, weight)
        weights[3, 4] = weights[4, 3] = weight
        frames = {node_frames[3], node_frames[4]}
        if mutation == "mixed_weight_and_field_change":
            outer.set_attr(nodes[0], "external_field", 1.0)
            frames.add(node_frames[0])
        return frames
    if mutation == "delete_boundary_edge":
        outer.remove_edge(nodes[3], "causal_influence", nodes[4])
        outer.remove_edge(nodes[4], "causal_influence", nodes[3])
        weights.pop((3, 4), None)
        weights.pop((4, 3), None)
        return {node_frames[3], node_frames[4]}
    if mutation == "external_field_change":
        outer.set_attr(nodes[0], "external_field", 1.0)
        return {node_frames[0]}
    if mutation == "identity_field_change":
        outer.set_attr(nodes[0], "identity_field", 1.0)
        return {node_frames[0]}
    if mutation == "node_birth":
        new_frame = len(mts)
        new_mt = inner.add_node("Microtheory", {
            "temperature": BETA, "discrete_mode": "3state", "can_tick": 0,
        })
        mts.append(new_mt)
        new_node = inner.add_node("Concept", {
            "name": f"c{n}", "state": 0.0,
            "external_field": 1.0, "identity_field": 0.0,
        })
        inner.add_edge(new_mt, "has_concept", new_node, {})
        nodes.append(new_node)
        node_frames.append(new_frame)
        active.append(True)
        src = n - 1
        edge(src, n, 0.75)
        edge(n, src, 0.75)
        weights[src, n] = weights[n, src] = 0.75
        return {node_frames[src], new_frame}
    if mutation == "node_deletion":
        doomed = 4
        neighbor_frames = {node_frames[src if tgt == doomed else tgt]
                           for (src, tgt) in weights if src == doomed or tgt == doomed}
        changed = inner.remove_node(nodes[doomed])
        if not changed:
            raise RuntimeError("registered node deletion did not remove its target")
        active[doomed] = False
        for key in [key for key in weights if doomed in key]:
            weights.pop(key)
        return neighbor_frames | {node_frames[doomed]}
    raise ValueError(f"unknown mutation: {mutation}")


def run_case(sr, manifest, n, mutation, negative_control=False):
    fields, base_weights = initial_model(n)
    event_graph = build(sr, manifest, n, fields, dict(base_weights))
    full_graph = build(sr, manifest, n, fields, dict(base_weights))
    event_outer, event_inner, event_mts, event_nodes, event_frames, event_active = event_graph
    full_outer, full_inner, full_mts, full_nodes, full_frames, full_active = full_graph
    initial_event, event_ok, _ = settle_all(event_inner, event_mts)
    initial_full, full_ok, _ = settle_all(full_inner, full_mts)
    if not (event_ok and full_ok and state_vector(event_inner, event_nodes, event_active)
            == state_vector(full_inner, full_nodes, full_active)):
        raise RuntimeError("paired initial graphs failed to settle to the same state")
    miss_graph = None
    if negative_control:
        miss_graph = build(sr, manifest, n, fields, dict(base_weights))
        _, miss_inner, miss_mts, miss_nodes, miss_frames, miss_active = miss_graph
        miss_steps, miss_ok, _ = settle_all(miss_inner, miss_mts)
        if not miss_ok or state_vector(miss_inner, miss_nodes, miss_active) != state_vector(event_inner, event_nodes, event_active):
            raise RuntimeError("negative control did not match the initial fixed point")

    pre_state = state_vector(event_inner, event_nodes, event_active)
    event_weights, full_weights = dict(base_weights), dict(base_weights)
    seed_frames = mutate_one(event_outer, event_inner, event_mts, event_nodes,
                             event_frames, event_active, event_weights, mutation, n)
    full_seed_frames = mutate_one(full_outer, full_inner, full_mts, full_nodes,
                                  full_frames, full_active, full_weights, mutation, n)
    if seed_frames != full_seed_frames:
        raise RuntimeError("paired mutation notification sets differ")

    miss_record = None
    if miss_graph is not None:
        miss_outer, miss_inner, miss_mts, miss_nodes, miss_frames, miss_active = miss_graph
        miss_weights = dict(base_weights)
        mutate_one(miss_outer, miss_inner, miss_mts, miss_nodes, miss_frames,
                   miss_active, miss_weights, mutation, n)
        miss_state = state_vector(miss_inner, miss_nodes, miss_active)
        miss_residual = residuals(miss_inner, miss_nodes, miss_active, miss_weights)
        miss_record = {
            "states": miss_state,
            "residual_count": sum(miss_residual),
        }

    event_steps, event_complete, event_turns = settle_event(
        event_inner, event_mts, event_nodes, event_frames, event_active,
        event_weights, seed_frames,
    )
    full_steps, full_complete, full_rounds = settle_all(full_inner, full_mts)
    event_state = state_vector(event_inner, event_nodes, event_active)
    full_state = state_vector(full_inner, full_nodes, full_active)
    if miss_record is not None:
        miss_record["detects_stale"] = miss_record["states"] != full_state
    event_res = residuals(event_inner, event_nodes, event_active, event_weights)
    full_res = residuals(full_inner, full_nodes, full_active, full_weights)
    model_fields = effective_fields(full_inner, full_nodes, full_active)
    final_edges = [[src, tgt, weight] for (src, tgt), weight in sorted(full_weights.items())]
    return {
        "n": n, "case": mutation,
        "active_nodes_after_mutation": sum(full_active),
        "frame_count": len(full_mts),
        "node_frames": list(full_frames),
        "active_mask": list(full_active),
        "final_effective_fields": model_fields,
        "final_directed_weights": final_edges,
        "initial_steps": {"event": initial_event, "full": initial_full},
        "pre_mutation_state": pre_state,
        "directly_notified_frames": sorted(seed_frames),
        "event": {"steps": event_steps, "turns": event_turns,
                  "complete": event_complete, "states": event_state,
                  "residual_count": sum(event_res)},
        "full_rescan": {"steps": full_steps, "rounds": full_rounds,
                         "complete": full_complete, "states": full_state,
                         "residual_count": sum(full_res)},
        "negative_control": miss_record,
        "mutation_changed_state_or_active_projection": event_state != pre_state,
        "equal_terminal_projection": event_state == full_state,
        "both_fixed_points": not any(event_res) and not any(full_res),
    }


def main():
    import substrate_rs as sr
    from substrate.seed_loader import engine_rules_only
    from substrate_rs import _native
    from domains.engine_provenance import engine_provenance

    seed_path = ROOT / "seeds/can_native_reimplementation.json"
    seed_doc = json.loads(seed_path.read_text())
    manifest = dict(engine_rules_only(seed_doc))
    manifest["rules"] = [r for r in manifest.get("rules", [])
                         if r.get("name") == "can_native_update_3state"]
    if len(manifest["rules"]) != 1:
        raise RuntimeError("expected exactly one native 3-state CAN update rule")
    cases = []
    for n in (8, 16, 32):
        for mutation in MUTATIONS:
            cases.append(run_case(sr, manifest, n, mutation,
                                  negative_control=(n == 8 and mutation in {
                                      "insert_boundary_edge", "node_birth", "node_deletion"})))
    result = {
        "protocol": "CAN cross-frame mutation matrix preregistered v1",
        "case_count": len(cases),
        "cases": cases,
        "all_event_cases_match_full_rescan_and_fixed_point": all(
            c["equal_terminal_projection"] and c["both_fixed_points"]
            and c["event"]["complete"] and c["full_rescan"]["complete"]
            and c["mutation_changed_state_or_active_projection"] for c in cases
        ),
        "all_negative_controls_detect_staleness": all(
            c["negative_control"] is None
            or c["negative_control"]["detects_stale"]
            and c["negative_control"]["residual_count"] > 0 for c in cases
        ),
        "provenance": {
            "python": sys.version, "platform": platform.platform(),
            "native_extension_path": str(Path(_native.__file__).resolve()),
            "native_extension_sha256": sha(Path(_native.__file__).resolve()),
            "engine_provenance": engine_provenance(),
            "harness_sha256": sha(Path(__file__)),
            "seed_manifest_sha256": sha(seed_path),
            "source_sha256": {name: sha(ROOT / "runners/dsl/src" / name)
                              for name in ("rewrite.rs", "substrate.rs", "term.rs")},
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUT.relative_to(ROOT)),
        "all_event_cases_match_full_rescan_and_fixed_point": result["all_event_cases_match_full_rescan_and_fixed_point"],
        "all_negative_controls_detect_staleness": result["all_negative_controls_detect_staleness"],
        "cases": [{"n": c["n"], "case": c["case"],
                   "equal": c["equal_terminal_projection"],
                   "fixed": c["both_fixed_points"],
                   "event_steps": c["event"]["steps"],
                   "full_steps": c["full_rescan"]["steps"],
                   "event_turns": c["event"]["turns"],
                   "full_rounds": c["full_rescan"]["rounds"]} for c in cases],
    }, indent=2))
    if not (result["all_event_cases_match_full_rescan_and_fixed_point"]
            and result["all_negative_controls_detect_staleness"]):
        raise SystemExit("mutation matrix failed a registered case/control")


if __name__ == "__main__":
    main()
