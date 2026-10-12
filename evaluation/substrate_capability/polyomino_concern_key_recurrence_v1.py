#!/usr/bin/env python3
"""Measure recurrence and key collisions through induce_concern in shared graphs."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_POLYOMINO_CONCERN_KEY_RECURRENCE_V1_PREREG_20260929.md"
RUNNER = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/polyomino_concern_key_recurrence_v1_lock_20260929.json"
OUT = ROOT / "evaluation/reports/polyomino_concern_key_recurrence_v1"
CAPTURE = OUT / "capture.json"
SOURCES = (
    "domains/reflective_faculty.py",
    "substrate/boot_core.py",
    "substrate/graph.py",
    "worlds/arc_ls20_scenario.py",
    "worlds/arc.py",
    "seeds/shape_decode_loop.json",
    "runners/dsl/src/shape_decode.rs",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
COLOR = 9
SHAPES = {
    "H06_A": ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3)),
    "H06_B": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),
    "H06_C": ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 1)),
    "H06_D": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (3, 1)),
    "H06_E": ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 3)),
}
RING = ("H06_A", "H06_B", "H06_C", "H06_D", "H06_E")
SEQUENCES = tuple(
    [{"id": f"repeat_{sid}", "first": sid, "second": sid,
      "condition": "exact_repeat"} for sid in RING]
    + [{"id": f"distinct_{a}_{b}", "first": a, "second": b,
        "condition": "distinct_same_key"}
       for a, b in sum(([(RING[i], RING[(i + 1) % len(RING)]),
                         (RING[(i + 1) % len(RING)], RING[i])]
                        for i in range(len(RING))), [])]
)


def digest(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def input_lock() -> dict:
    return {
        "schema_version": 1,
        "protocol": digest(PROTOCOL), "runner": digest(RUNNER),
        "sources": [digest(ROOT / source) for source in SOURCES],
        "cases": {key: [list(point) for point in points]
                  for key, points in SHAPES.items()},
        "sequences": list(SEQUENCES), "color": COLOR,
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                    text=True, capture_output=True,
                                    check=True).stdout.strip(),
    }


def atomic(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    tmp.replace(path)


def make_cells(shape_id: str) -> list[tuple[int, int, int]]:
    coords = SHAPES[shape_id]
    max_row = max(r for r, _ in coords)
    bottom_cols = [c for r, c in coords if r == max_row]
    extra = (max_row + 1, min(bottom_cols))
    return [(r, c, COLOR) for r, c in coords] + [(extra[0], extra[1], COLOR)]


def snapshot(sub, agent, observation_result=None) -> dict:
    axes = [{"id": str(node_id), "attrs": dict(sub.node(node_id)["attrs"])}
            for node_id in sub.nodes("CapabilityAxis")]
    return {
        "agent_attrs": dict(sub.node(agent)["attrs"]),
        "axis_count": len(axes), "axes": axes,
        "observation_count": len(list(sub.nodes("Observation"))),
        "shape_signature_count": len(list(sub.nodes("ShapeSignature"))),
        "result": observation_result,
    }


def run_sequence(spec: dict) -> dict:
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    from worlds.arc import cells_to_signature

    sub, agent = boot_core()
    native = rf._native_eval2(sub)
    rf._ensure_shape_decode_loop(sub, native, agent)
    base_sig = cells_to_signature([(r, c, COLOR)
                                   for r, c in SHAPES[spec["first"]]])
    sub.add_node("ShapeSignature", {
        "name": "sequence_base", "signature": json.dumps(base_sig),
        "kind": "faculty", "faculty": "sequence_base",
        "dim_types": ["pred", "coord:r", "coord:c", "val"],
    })
    events = []
    for ordinal, shape_id in enumerate((spec["first"], spec["second"]), 1):
        before = snapshot(sub, agent)
        goal = cells_to_signature(make_cells(shape_id))
        started_wall, started_cpu = time.perf_counter(), time.process_time()
        result = rf.induce_concern(sub, goal)
        wall, cpu = time.perf_counter() - started_wall, time.process_time() - started_cpu
        after = snapshot(sub, agent, result)
        # `induce_concern` appends one Observation per call; preserve that order
        # instead of assuming a particular string format for native node IDs.
        obs_node = list(sub.nodes("Observation"))[-1]
        obs_attrs = dict(sub.node(obs_node)["attrs"])
        minted_targets = [dict(sub.node(n)["attrs"])
                          for n in sub.neighbours(obs_node, "minted")]
        transforms = [dict(sub.node(n)["attrs"])
                      for n in sub.neighbours(obs_node, "has_transform")]
        events.append({
            "ordinal": ordinal, "shape_id": shape_id,
            "signature": goal,
            "signature_sha256": hashlib.sha256(json.dumps(
                goal, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "capability_key": result.get("capability_key"),
            "status": obs_attrs.get("status"),
            "observation_attrs": obs_attrs,
            "minted_edge_targets": minted_targets,
            "has_transform_targets": transforms,
            "before": before, "after": after,
            "axis_delta": after["axis_count"] - before["axis_count"],
            "native_steps": next((attrs.get("native_steps")
                                  for n in reversed(list(sub.nodes("NativeReflectiveFacultyReceipt")))
                                  for attrs in [sub.node(n)["attrs"]]
                                  if attrs.get("cluster") == "reflective_faculty.concern_decode_settlement"), None),
            "wall_seconds": wall, "cpu_seconds": cpu,
        })
    return {**spec, "events": events}


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
        raise SystemExit("source/case lock drift")
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    sequences = [run_sequence(spec) for spec in SEQUENCES]
    post = input_lock()
    if post != locked:
        raise SystemExit("post-run source/case lock drift")
    capture = {
        "schema_version": 1,
        "run_id": "polyomino-concern-key-recurrence-v1-20260929",
        "status": "complete", "input_lock": locked,
        "post_run_input_lock": post, "sequences": sequences,
        "process": {"wall_seconds": time.perf_counter() - started_wall,
                    "cpu_seconds": time.process_time() - started_cpu},
    }
    atomic(CAPTURE, capture)
    print(json.dumps({"capture": str(CAPTURE.relative_to(ROOT)),
                      "sequences": len(sequences),
                      "observations": sum(len(s["events"]) for s in sequences),
                      "wall_seconds": capture["process"]["wall_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
