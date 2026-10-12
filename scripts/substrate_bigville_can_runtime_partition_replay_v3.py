#!/usr/bin/env python3
"""Replay authored Bigville CAN resident frames through event/full settlement."""
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAST = ROOT / "seeds/bigville_cast100.json"
CAN_SEED = ROOT / "seeds/can_native_reimplementation.json"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_BIGVILLE_CAN_RUNTIME_PARTITION_REPLAY_V3_AMENDMENT_20260925.md"
OUT = ROOT / "evaluation/reports/substrate_bigville_can_runtime_partition_replay_v3_20260925.json"
TARGETS = tuple(range(0, 100, 10))
CAP = 100_000
AUDIT_FIELDS = ("cand_enum", "cand_tested", "where_evals", "where_rejects", "leaf_visits",
                "bindings_cloned", "rule_enumerations", "term_evals_total", "term_units_total")
THRESHOLD = 0.5493061443340548


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nid(value) -> int:
    return int(value.value if hasattr(value, "value") else value)


def empty_counts():
    return dict.fromkeys(AUDIT_FIELDS, 0)


def add_counts(a, b):
    for key in AUDIT_FIELDS:
        a[key] += int(b.get(key, 0))


def snap(inner):
    raw = dict(inner.scale_audit_snapshot())
    return {k: int(raw.get(k, 0)) for k in AUDIT_FIELDS}


def build(sr, cast, seed_doc, bigville):
    from substrate.seed_loader import engine_rules_only
    outer = sr.Substrate()
    inner = outer._inner
    bigville.install_productions(outer)
    residents, mts, concepts, node_owner, node_flat, ref_by_id = [], [], [], {}, {}, {}
    evidence = []
    for resident in cast:
        built = bigville.build_resident_can_mt(outer, resident)
        mt = built["mt_node"]
        inner.set_attr(mt, "discrete_mode", "3state")
        inner.set_attr(mt, "can_tick", 0.0)
        concepts_by_topic = built["concepts"]
        topic_refs = dict(concepts_by_topic)
        index = len(mts)
        for topic_index, node in enumerate(topic_refs.values()):
            node_id = nid(node)
            node_flat[node_id] = index * len(topic_refs) + topic_index
            ref_by_id[node_id] = node
        residents.append(resident)
        mts.append(mt)
        concepts.append(topic_refs)
    manifest = dict(engine_rules_only(seed_doc))
    manifest["rules"] = [r for r in manifest.get("rules", [])
                         if r.get("name") == "can_native_update_3state"]
    if len(manifest["rules"]) != 1:
        raise RuntimeError("expected exactly one 3-state CAN update rule")
    inner.load_seed_manifest(manifest)

    # Derive live ownership from has_concept, independently of builder order.
    mt_position = {nid(mt): i for i, mt in enumerate(mts)}
    for node_id, ref in ref_by_id.items():
        owners = [nid(mt_ref) for mt_ref in inner.in_neighbours(ref, "has_concept")]
        if len(owners) != 1 or owners[0] not in mt_position:
            raise RuntimeError("runtime Concept membership is not a unique cast Microtheory")
        node_owner[node_id] = mt_position[owners[0]]

    # Derive components from live graph adjacency, independently of resident indices.
    parent = {node: node for node in node_owner}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    directed_edges = []
    for node in sorted(node_owner):
        for other_ref in inner.neighbours(ref_by_id[node], "causal_influence"):
            other = nid(other_ref)
            if other not in node_owner:
                raise RuntimeError("causal edge reaches a node outside the authored CAN concepts")
            union(node, other)
            directed_edges.append((node, other))
    components = {}
    for node in parent:
        components.setdefault(find(node), []).append(node)
    mt_by_component = {}
    for frame, topic_map in enumerate(concepts):
        roots = {find(nid(node)) for node in topic_map.values()}
        if len(roots) != 1:
            raise RuntimeError("one authored Microtheory split into multiple access components")
        root = next(iter(roots))
        if root in mt_by_component:
            raise RuntimeError("multiple Microtheories share one runtime dependency component")
        mt_by_component[root] = frame
    if len(components) != len(mts) or set(components) != set(mt_by_component):
        raise RuntimeError("runtime dependency components do not biject with Microtheories")
    frames = [None] * len(mts)
    frame_nodes = [[] for _ in mts]
    node_frame = {}
    for root, members in components.items():
        frame = mt_by_component[root]
        frames[frame] = mts[frame]
        frame_nodes[frame] = sorted(members)
        for node in members:
            node_frame[node] = frame
    if any(len(nodes) != 5 for nodes in frame_nodes):
        raise RuntimeError("authored Bigville component did not contain exactly five Concepts")
    cross_edges = [(a, b) for a, b in directed_edges if node_frame[a] != node_frame[b]]
    return (outer, inner, residents, frames, concepts, frame_nodes, node_frame,
            directed_edges, cross_edges, ref_by_id, node_flat)


def states(inner, concepts):
    result = []
    for topics in concepts:
        result.append({topic: float(inner.node(ref)["attrs"].get("state", 0.0))
                       for topic, ref in topics.items()})
    return result


def fields(inner, concepts):
    return [[float(inner.node(ref)["attrs"].get("external_field", 0.0)),
             float(inner.node(ref)["attrs"].get("identity_field", 0.0))]
            for topics in concepts for ref in topics.values()]


def weights_by_id(concepts, residents, bigville, node_flat):
    edges = []
    for topics, resident in zip(concepts, residents):
        params = resident["params"]
        bins = bigville.effective_resolution_bins(params["resolution_bins"], params["arousal"])
        for a, b, base, nuance in bigville.STRUCTURAL_EDGES:
            weight = bigville.quantize_j(bigville.true_edge_j(params, base, nuance), bins)
            src, dst = node_flat[nid(topics[a])], node_flat[nid(topics[b])]
            edges.extend(((src, dst, weight), (dst, src, weight)))
    return edges


def residuals(state_rows, field_rows, weight_rows):
    flat = []
    for row in state_rows:
        flat.extend(row.values())
    residual = [False] * len(flat)
    for (src, _), (external, identity) in zip(enumerate(flat), field_rows):
        h = external + identity
        for a, b, w in weight_rows:
            if a == src:
                h += w * flat[b]
        scaled = 1.5 * h
        expected = 1.0 if scaled > THRESHOLD else -1.0 if scaled < -THRESHOLD else 0.0
        residual[src] = expected != flat[src]
    return residual


def settle_full(inner, mts, audit=False):
    steps = turns = rounds = 0
    total_counts = empty_counts()
    while rounds < CAP and steps < CAP:
        moved = 0
        rounds += 1
        for mt in mts:
            if steps >= CAP:
                break
            if audit:
                inner.scale_audit_reset(); inner.scale_audit_set_enabled(True)
            count = inner.run_rules_scoped(CAP - steps, False, mt)
            if audit:
                add_counts(total_counts, snap(inner)); inner.scale_audit_set_enabled(False)
            moved += count; steps += count; turns += 1
        if moved == 0:
            return {"steps": steps, "turns": turns, "rounds": rounds,
                    "complete": True, "audit": total_counts}
    return {"steps": steps, "turns": turns, "rounds": rounds,
            "complete": False, "audit": total_counts}


def settle_event(inner, mts, frame_nodes, node_frame, edges, ref_by_id, seed_frames, audit=False):
    dependents = [set() for _ in mts]
    for source, target in edges:
        sf, tf = node_frame[source], node_frame[target]
        if sf != tf:
            dependents[tf].add(sf)
    queue = deque(sorted(set(seed_frames)))
    queued = set(queue)
    steps = turns = enqueues = changed_frames = 0
    total_counts = empty_counts()
    while queue and turns < CAP and steps < CAP:
        frame = queue.popleft(); queued.remove(frame)
        before = [float(inner.node(ref_by_id[node])["attrs"].get("state", 0.0)) for node in frame_nodes[frame]]
        if audit:
            inner.scale_audit_reset(); inner.scale_audit_set_enabled(True)
        count = inner.run_rules_scoped(CAP - steps, False, mts[frame])
        if audit:
            add_counts(total_counts, snap(inner)); inner.scale_audit_set_enabled(False)
        steps += count; turns += 1
        after = [float(inner.node(ref_by_id[node])["attrs"].get("state", 0.0)) for node in frame_nodes[frame]]
        if before != after:
            changed_frames += 1
            for dependent in dependents[frame]:
                if dependent not in queued:
                    queue.append(dependent); queued.add(dependent); enqueues += 1
    return {"steps": steps, "turns": turns, "enqueues": enqueues,
            "changed_frames": changed_frames, "complete": not queue and steps < CAP,
            "audit": total_counts}


def mutate(inner, concepts, residents, bigville, target):
    topics = concepts[target]
    for topic, evidence, alpha in bigville.SCENARIO_EVIDENCE:
        inner.concept_apply_evidence(topics[topic], evidence, alpha)


def run_arm(sr, cast, seed_doc, bigville, policy):
    outer, inner, residents, mts, concepts, frame_nodes, node_frame, edges, cross, ref_by_id, node_flat = build(
        sr, cast, seed_doc, bigville)
    initial = settle_full(inner, mts)
    base_states = states(inner, concepts)
    if not initial["complete"]:
        raise RuntimeError(f"{policy} baseline failed to settle")
    weights = weights_by_id(concepts, residents, bigville, node_flat)
    checkpoints = []
    audit_records = []
    for target in TARGETS:
        mutate(inner, concepts, residents, bigville, target)
        if policy == "event":
            record = settle_event(inner, mts, frame_nodes, node_frame, edges, ref_by_id,
                                  {target}, audit=True)
        else:
            record = settle_full(inner, mts, audit=True)
        if not record["complete"]:
            raise RuntimeError(f"{policy} update failed to settle at resident {target}")
        projection = states(inner, concepts)
        field_rows = fields(inner, concepts)
        res = residuals(projection, field_rows, weights)
        checkpoints.append({"target_resident_position": target, "states": projection,
                            "fields": field_rows, "residual_count": sum(res),
                            "settlement": record})
        audit_records.append(record["audit"])
    return {"initial": initial, "initial_states": base_states, "checkpoints": checkpoints,
            "component_count": len(frame_nodes),
            "component_sizes": [len(nodes) for nodes in frame_nodes],
            "cross_frame_edges": len(cross), "node_frame": node_frame,
            "weights": weights}


def run_omitted_notification_control(sr, cast, seed_doc, bigville, expected_after):
    (outer, inner, residents, mts, concepts, frame_nodes, node_frame, edges, cross,
     ref_by_id, node_flat) = build(sr, cast, seed_doc, bigville)
    baseline = settle_full(inner, mts)
    before = states(inner, concepts)
    for target in TARGETS:
        mutate(inner, concepts, residents, bigville, target)
    stale = states(inner, concepts)
    stale_fields = fields(inner, concepts)
    residual = residuals(stale, stale_fields,
                         weights_by_id(concepts, residents, bigville, node_flat))
    event_changes_state = before != expected_after
    stale_differs = stale != expected_after
    return {
        "baseline_settled": baseline["complete"],
        "notified_sequence_changes_state": event_changes_state,
        "stale_states_equal_notified_terminal": not stale_differs,
        "residual_count": sum(residual),
        "detects_stale": event_changes_state and stale_differs and any(residual),
    }


def main():
    import substrate_rs as sr
    from substrate_rs import _native
    from domains.engine_provenance import engine_provenance
    from worlds import bigville_can_beliefs as bigville
    cast_doc, seed_doc = json.loads(CAST.read_text()), json.loads(CAN_SEED.read_text())
    cast = cast_doc["residents"]
    if len(cast) != 100:
        raise RuntimeError("registered Bigville cast must contain exactly 100 residents")
    event = run_arm(sr, cast, seed_doc, bigville, "event")
    full = run_arm(sr, cast, seed_doc, bigville, "full")
    omitted = run_omitted_notification_control(
        sr, cast, seed_doc, bigville, event["checkpoints"][0]["states"])
    same_baseline = event["initial_states"] == full["initial_states"]
    checkpoints = []
    for i, target in enumerate(TARGETS):
        ev, ref = event["checkpoints"][i], full["checkpoints"][i]
        checkpoints.append({
            "target_resident_position": target,
            "event_states": ev["states"], "full_states": ref["states"],
            "event_fields": ev["fields"], "full_fields": ref["fields"],
            "event_residual_count": ev["residual_count"],
            "full_residual_count": ref["residual_count"],
            "event_settlement": ev["settlement"], "full_settlement": ref["settlement"],
            "states_equal": ev["states"] == ref["states"],
        })
    weights = event["weights"]
    # Save weights and node-frame map once so the separate analyzer can rebuild residuals.
    result = {
        "protocol": "Bigville CAN runtime partition replay diagnostic v3",
        "target_positions": list(TARGETS), "resident_count": len(cast),
        "component_count": event["component_count"], "component_sizes": event["component_sizes"],
        "cross_frame_edge_count": event["cross_frame_edges"],
        "event_baseline": event["initial"], "full_baseline": full["initial"],
        "baseline_states_equal": same_baseline,
        "checkpoints": checkpoints,
        "runtime_node_frame": event["node_frame"],
        "directed_weights_by_flat_index": [[a, b, w] for a, b, w in weights],
        "all_event_checkpoints_equal_full": same_baseline and all(c["states_equal"] for c in checkpoints),
        "all_settled": event["initial"]["complete"] and full["initial"]["complete"] and
                       all(c["event_settlement"]["complete"] and c["full_settlement"]["complete"]
                           for c in checkpoints),
        "omitted_notification_control": omitted,
        "provenance": {
            "python": sys.version, "platform": platform.platform(),
            "runner_sha256": sha(Path(__file__)), "protocol_sha256": sha(PREREG),
            "cast_sha256": sha(CAST), "can_seed_sha256": sha(CAN_SEED),
            "bigville_builder_sha256": sha(ROOT / "worlds/bigville_can_beliefs.py"),
            "native_extension_path": str(Path(_native.__file__).resolve()),
            "native_extension_sha256": sha(Path(_native.__file__).resolve()),
            "engine_provenance": engine_provenance(),
            "source_sha256": {name: sha(ROOT / "runners/dsl/src" / name)
                              for name in ("rewrite.rs", "substrate.rs", "term.rs", "py.rs")},
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUT.relative_to(ROOT)),
        "components": result["component_count"],
        "component_size_set": sorted(set(result["component_sizes"])),
        "cross_frame_edges": result["cross_frame_edge_count"],
        "baseline_equal": same_baseline,
        "event_full_parity": result["all_event_checkpoints_equal_full"],
        "all_settled": result["all_settled"],
        "omitted_notification_control": omitted,
        "checkpoints": [{"target": c["target_resident_position"],
                         "states_equal": c["states_equal"],
                         "event_turns": c["event_settlement"]["turns"],
                         "full_turns": c["full_settlement"]["turns"],
                         "event_candidates": c["event_settlement"]["audit"]["cand_enum"],
                         "full_candidates": c["full_settlement"]["audit"]["cand_enum"],
                         "event_residual": c["event_residual_count"],
                         "full_residual": c["full_residual_count"]} for c in checkpoints],
    }, indent=2))
    if not (result["all_event_checkpoints_equal_full"] and result["all_settled"]
            and omitted["mutation_changed_state"] and omitted["detects_stale"]):
        raise SystemExit("Bigville runtime partition replay failed registered parity/settlement criteria")


if __name__ == "__main__":
    main()
