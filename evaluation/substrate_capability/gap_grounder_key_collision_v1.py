#!/usr/bin/env python3
"""Source-locked shared-graph replay of same-faculty CapabilityGaps."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GAP_GROUNDER_KEY_COLLISION_V1_PREREG_20260929.md"
RUNNER = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/gap_grounder_key_collision_v1_lock_20260929.json"
OUT = ROOT / "evaluation/reports/gap_grounder_key_collision_v1"
CAPTURE = OUT / "capture.json"
SOURCES = (
    "domains/substrate_extension.py",
    "domains/reflective_faculty.py",
    "domains/self_capability_collapse.py",
    "substrate/boot_core.py",
    "substrate/world_adapter.py",
    "substrate/graph.py",
    "substrate/seed_loader.py",
    "seeds/composer_faculty_pipeline.json",
    "seeds/shape_decode_loop.json",
    "runners/dsl/src/shape_decode.rs",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
)

FACULTY = "shared_family"
GAP_SPECS = {
    "A": {
        "faculty": FACULTY,
        "observation": [["classify the item", "self", "input"],
                        ["route to a handler", "input", "handler"],
                        ["mark handled", "handler", "done"]],
        "status": "perceived",
    },
    "B": {
        "faculty": FACULTY,
        "observation": [["spectral_value", "signal", "magnitude"],
                        ["log_scale", "magnitude", "value"]],
        "needed_primitive": "spectral_value",
        "n_samples": 32,
        "test_frequencies": [3, 7, 11],
        "inputs": ["signal"],
        "outputs": ["spectrum"],
        "example": "colour as a frequency+amplitude frame: a per-bin log-magnitude",
        "status": "perceived",
    },
}
SEQUENCES = (
    {"id": "isolated_A", "events": ["A"]},
    {"id": "isolated_B", "events": ["B"]},
    {"id": "repeat_A", "events": ["A", "A"]},
    {"id": "repeat_B", "events": ["B", "B"]},
    {"id": "A_then_B", "events": ["A", "B"]},
    {"id": "B_then_A", "events": ["B", "A"]},
)


def digest(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def input_lock() -> dict:
    return {
        "schema_version": 1,
        "protocol": digest(PROTOCOL), "runner": digest(RUNNER),
        "sources": [digest(ROOT / source) for source in SOURCES],
        "fixture_definitions": GAP_SPECS,
        "sequences": list(SEQUENCES),
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                    text=True, capture_output=True,
                                    check=True).stdout.strip(),
    }


def atomic(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2, default=str) + "\n")
    tmp.replace(path)


def node_rows(sub, kind: str) -> list[dict]:
    rows = []
    for node_id in sub.nodes(kind):
        node = sub.node(node_id)
        rows.append({"id": str(node_id), "attrs": dict(node["attrs"])})
    return rows


def snapshot(agent, sub, native, agent_node) -> dict:
    type_names = ("CapabilityAxis", "PrimitiveRequest", "HeldPrimitive",
                  "Observation", "CapabilityGap")
    rules = native.export_rules()
    receipts = node_rows(sub, "NativeReflectiveFacultyReceipt")
    return {
        "codebook_epoch": sub.node(agent_node)["attrs"].get("codebook_epoch"),
        "nodes": {kind: node_rows(sub, kind) for kind in type_names},
        "rule_names": sorted(r.get("name", "") for r in rules if isinstance(r, dict)),
        "receipt_count": len(receipts),
        "latest_native_steps": receipts[-1]["attrs"].get("native_steps") if receipts else None,
    }


def run_sequence(spec: dict) -> dict:
    from substrate.world_adapter import WorldAdapter
    from domains import reflective_faculty as rf
    from domains import substrate_extension as se

    agent = WorldAdapter(seeds=())
    sub, native, agent_node = rf._resolve_agent(agent)
    before_sequence = snapshot(agent, sub, native, agent_node)
    events = []
    for ordinal, label in enumerate(spec["events"], 1):
        attrs = dict(GAP_SPECS[label])
        gap = sub.add_node("CapabilityGap", attrs)
        before = snapshot(agent, sub, native, agent_node)
        started_wall, started_cpu = time.perf_counter(), time.process_time()
        result = se.extend_for_gap(agent, gap, verify=True)
        wall, cpu = time.perf_counter() - started_wall, time.process_time() - started_cpu
        after = snapshot(agent, sub, native, agent_node)
        new_observations = [row for row in after["nodes"]["Observation"]
                            if row["id"] not in {old["id"] for old in before["nodes"]["Observation"]}]
        events.append({
            "ordinal": ordinal, "case": label, "gap_attrs": attrs,
            "derived_name_hint": "gap_" + FACULTY,
            "result": result, "new_observations": new_observations,
            "before": before, "after": after,
            "axis_delta": len(after["nodes"]["CapabilityAxis"])
                          - len(before["nodes"]["CapabilityAxis"]),
            "primitive_request_delta": len(after["nodes"]["PrimitiveRequest"])
                                       - len(before["nodes"]["PrimitiveRequest"]),
            "held_primitive_delta": len(after["nodes"]["HeldPrimitive"])
                                    - len(before["nodes"]["HeldPrimitive"]),
            "wall_seconds": wall, "cpu_seconds": cpu,
        })
    return {"id": spec["id"], "events": events, "initial": before_sequence,
            "final": snapshot(agent, sub, native, agent_node)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or CAPTURE.exists():
            raise SystemExit("refusing to overwrite lock or capture")
        atomic(LOCK, input_lock())
        print(LOCK.relative_to(ROOT))
        return
    locked = json.loads(LOCK.read_text())
    if input_lock() != locked:
        raise SystemExit("source/fixture lock drift")
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    runs = [run_sequence(spec) for spec in SEQUENCES]
    post = input_lock()
    if post != locked:
        raise SystemExit("post-run source/fixture lock drift")
    capture = {
        "schema_version": 1,
        "run_id": "gap-grounder-key-collision-v1-20260929",
        "status": "complete", "input_lock": locked,
        "post_run_input_lock": post, "sequences": runs,
        "process": {"wall_seconds": time.perf_counter() - started_wall,
                    "cpu_seconds": time.process_time() - started_cpu},
    }
    atomic(CAPTURE, capture)
    print(json.dumps({"capture": str(CAPTURE.relative_to(ROOT)),
                      "sequences": len(runs),
                      "extend_for_gap_calls": sum(len(s["events"]) for s in runs),
                      "wall_seconds": capture["process"]["wall_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
