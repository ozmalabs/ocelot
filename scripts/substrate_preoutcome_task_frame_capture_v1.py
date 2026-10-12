#!/usr/bin/env python3
"""Capture outcome-blind ingress frames and post-checkpoint rule accesses."""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_PREOUTCOME_TASK_FRAME_CAPTURE_V1_PREREG_20261005.md"
BASE_PATH = ROOT / "scripts/substrate_live_held_topic_evidence_v1_6.py"
RUNNER = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/preoutcome_task_frame_capture_v1_20261005_lock.json"
OUTDIR = ROOT / "evaluation/reports/preoutcome_task_frame_capture_v1_20261005"
CAPTURE = OUTDIR / "capture.json.gz"


def sha(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("held_topic_base_v1_6", BASE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lock_payload():
    from substrate_rs import _native
    base = load_base()
    return {
        "schema_version": 1,
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(RUNNER),
        "base_runner_sha256": sha(BASE_PATH),
        "base_inputs": base.fingerprint(),
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "design": {"workers": 3, "turns_per_worker": 7,
                   "checkpoint": "after _record_live_communication_state, before first native closure",
                   "ownership": "fixed typed ingress projection in preregistration"},
    }


def nid(value):
    return int(value.value if hasattr(value, "value") else value)


def shape(value):
    if value is None:
        return {"type": "null", "size": 0}
    if isinstance(value, bool):
        return {"type": "bool", "size": 2}
    if isinstance(value, (int, float, str)):
        return {"type": type(value).__name__}
    if isinstance(value, (list, dict)):
        return {"type": type(value).__name__, "size": len(value)}
    return {"type": type(value).__name__}


def frame_at_checkpoint(base, agent, mid):
    graph = agent.s.graph_to_dict()
    nodes = {int(row["id"]): row for row in graph.get("nodes", [])}
    edges = [(int(row["src"]), str(row["type"]), int(row["tgt"]))
             for row in graph.get("edges", [])]
    root = nid(mid)
    owned = {root}
    for src, rel, tgt in edges:
        other = None
        if src == root and rel == "has_mention" and nodes.get(tgt, {}).get("type") == "Mention":
            other = tgt
        elif root in (src, tgt):
            candidate = tgt if src == root else src
            typ = nodes.get(candidate, {}).get("type")
            if ((rel in {"has_interpretation", "interprets"} and typ == "CommunicationInterpretation")
                    or (rel in {"represents_message", "for_message"} and typ == "DiscourseEvent")):
                other = candidate
        if other is not None:
            owned.add(other)
    incident = [edge for edge in edges if edge[0] in owned or edge[2] in owned]
    internal = [edge for edge in incident if edge[0] in owned and edge[2] in owned]
    boundary = [edge for edge in incident if (edge[0] in owned) != (edge[2] in owned)]
    external = {edge[2] if edge[0] in owned else edge[0] for edge in boundary}
    types = Counter(nodes[n]["type"] for n in owned)
    ext_types = Counter(nodes[n]["type"] for n in external if n in nodes)
    edge_types = Counter(edge[1] for edge in boundary)
    attrs = {str(n): {str(k): shape(v) for k, v in sorted(nodes[n].get("attrs", {}).items())}
             for n in sorted(owned)}
    return {
        "root_message_id": root,
        "node_count": len(nodes), "edge_count": len(edges),
        "owned_ids": sorted(owned), "owned_node_count": len(owned),
        "owned_type_counts": dict(sorted(types.items())),
        "boundary_unique_external_node_count": len(external),
        "boundary_external_type_counts": dict(sorted(ext_types.items())),
        "boundary_incidence_count": len(boundary),
        "boundary_edge_type_counts": dict(sorted(edge_types.items())),
        "internal_edge_count": len(internal),
        "owned_attribute_shapes": attrs,
        "owned_induced_state_treewidth_upper_bound": base.min_fill_width_upper_bound(owned, internal),
        "internal_edges": [list(row) for row in sorted(internal)],
        "boundary_edges": [list(row) for row in sorted(boundary)],
    }


def instrument(base):
    from substrate.world_adapter import WorldAdapter
    original_converse = WorldAdapter.converse
    original_record = WorldAdapter._record_live_communication_state
    checkpoint_rows = []
    traces = []
    static_access = {}

    def record(self, mid, *args, **kwargs):
        result = original_record(self, mid, *args, **kwargs)
        if getattr(self, "_preoutcome_capture_active", False):
            frame = frame_at_checkpoint(base, self, mid)
            checkpoint_rows.append(frame)
            self.inner.runtime_access_trace_reset()
        return result

    def converse(self, *args, **kwargs):
        self._preoutcome_capture_active = True
        self.inner.runtime_access_trace_set_enabled(False)
        self.inner.runtime_access_trace_reset()
        self.inner.runtime_access_trace_set_enabled(True)
        try:
            return original_converse(self, *args, **kwargs)
        finally:
            self._preoutcome_capture_active = False
            self.inner.runtime_access_trace_set_enabled(False)
            rows, dropped = self.inner.runtime_access_trace_snapshot()
            events = [{"rule_uid": int(uid), "kind": str(kind),
                       "node": None if node is None else int(node),
                       "resource": None if resource is None else str(resource),
                       "peer": None if peer is None else int(peer), "count": int(count)}
                      for uid, kind, node, resource, peer, count in rows]
            traces.append({"events": events, "dropped": int(dropped)})
            for row in self.inner.rule_access_sets():
                meta = self.inner.rule_metadata(int(row[0]))
                uid = int(meta["rule_uid"])
                static_access[uid] = {"name": str(row[1]), "reads": list(row[3]),
                                      "term_edge_reads": list(row[4]), "writes": list(row[5]),
                                      "reads_any": bool(row[6]), "writes_any": bool(row[7])}

    WorldAdapter.converse = converse
    WorldAdapter._record_live_communication_state = record
    return checkpoint_rows, traces, static_access, original_converse, original_record


def worker(rep):
    base = load_base()
    from substrate.world_adapter import WorldAdapter
    checkpoints, traces, static_access, old_converse, old_record = instrument(base)
    try:
        result = base.worker(rep)
    finally:
        WorldAdapter.converse = old_converse
        WorldAdapter._record_live_communication_state = old_record
    if len(checkpoints) != len(result["turns"]) or len(traces) != len(result["turns"]):
        raise RuntimeError(f"checkpoint/trace/turn mismatch: {len(checkpoints)}/{len(traces)}/{len(result['turns'])}")
    for turn, frame, trace in zip(result["turns"], checkpoints, traces):
        owned = set(frame["owned_ids"])
        external = {int(edge[2]) if int(edge[0]) in owned else int(edge[0])
                    for edge in frame["boundary_edges"]}
        totals, roles, touched = Counter(), Counter(), {"frame": set(), "boundary_external": set(), "outside_cut": set()}
        for event in trace["events"]:
            event["rule_name"] = static_access.get(event["rule_uid"], {}).get("name", "<unmapped>")
            event_roles = set()
            for node in (event["node"], event["peer"]):
                if node is None:
                    continue
                role = "frame" if node in owned else "boundary_external" if node in external else "outside_cut"
                event_roles.add(role)
                touched[role].add(node)
            event["scope_roles"] = sorted(event_roles or {"node_free"})
            for role in event["scope_roles"]:
                roles[(role, event["kind"])] += event["count"]
            totals[event["kind"]] += event["count"]
        observed = {event["rule_uid"] for event in trace["events"]}
        turn["preoutcome_frame"] = frame
        turn["postcheckpoint_rule_access"] = {
            "dropped": trace["dropped"], "event_count": sum(totals.values()),
            "distinct_rows": len(trace["events"]),
            "access_counts_by_kind": dict(sorted(totals.items())),
            "access_counts_by_scope_and_kind": {f"{role}/{kind}": value
                for (role, kind), value in sorted(roles.items())},
            "touched_nodes_by_scope": {role: len(values) for role, values in touched.items()},
            "unmapped_rule_uids": sorted(uid for uid in observed if uid not in static_access),
            "events": trace["events"],
        }
    result["preoutcome_capture_gate"] = all(
        turn["postcheckpoint_rule_access"]["dropped"] == 0
        and not turn["postcheckpoint_rule_access"]["unmapped_rule_uids"]
        for turn in result["turns"])
    return result


def main():
    if sys.argv[1:] == ["--lock"]:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(lock_payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, default=str))
        return
    locked = lock_payload()
    if not LOCK.exists() or json.loads(LOCK.read_text()) != locked:
        raise SystemExit("source lock absent or stale")
    if CAPTURE.exists():
        raise SystemExit(f"refusing to overwrite {CAPTURE}")
    OUTDIR.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), env.get("PYTHONPATH", "")])
    runs = []
    for rep in range(3):
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(rep)], cwd=ROOT,
                              env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(proc.stdout))
    post = lock_payload()
    capture = {"schema": "PreOutcomeTaskFrameCaptureV1", "locked_inputs": locked,
               "post_run_inputs": post, "runs": runs}
    CAPTURE.write_bytes(gzip.compress(json.dumps(capture, sort_keys=True, separators=(",", ":"), default=str).encode(), compresslevel=6, mtime=0))
    print(json.dumps({"capture": str(CAPTURE.relative_to(ROOT)), "workers": len(runs),
                      "turns": sum(len(r["turns"]) for r in runs),
                      "all_trace_gates_pass": all(r["preoutcome_capture_gate"] for r in runs),
                      "source_stable": locked == post}, indent=2))
    if locked != post or not all(r["preoutcome_capture_gate"] for r in runs):
        raise SystemExit("capture gate failed")


if __name__ == "__main__":
    main()
