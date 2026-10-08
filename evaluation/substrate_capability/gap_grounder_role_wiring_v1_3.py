#!/usr/bin/env python3
"""Paired current/candidate key-policy replay through extend_for_gap."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GAP_GROUNDER_ROLE_WIRING_V1_3_PREREG_20260929.md"
RUNNER = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/gap_grounder_role_wiring_v1_3_lock_20260929.json"
OUT = ROOT / "evaluation/reports/gap_grounder_role_wiring_v1_3"
CAPTURE = OUT / "capture.json"
SOURCES = (
    "domains/substrate_extension.py", "domains/reflective_faculty.py",
    "domains/self_verification.py",
    "domains/self_capability_collapse.py", "substrate/boot_core.py",
    "substrate/world_adapter.py", "substrate/graph.py", "substrate/seed_loader.py",
    "seeds/composer_faculty_pipeline.json", "seeds/shape_decode_loop.json",
    "runners/dsl/src/shape_decode.rs", "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
FACULTY = "shared_family"
GAPS = {
    "B": {"faculty": FACULTY, "observation": [
        ["spectral_value", "signal", "magnitude"],
        ["log_scale", "magnitude", "value"]],
        "needed_primitive": "spectral_value", "n_samples": 32,
        "test_frequencies": [3, 7, 11], "inputs": ["signal"], "outputs": ["spectrum"],
        "example": "per-bin log magnitude", "status": "perceived"},
    "C": {"faculty": FACULTY, "observation": [
        ["spectral_value", "magnitude_spectrum", "recovered_signal"],
        ["log_scale", "recovered_signal", "magnitude_spectrum"]],
        "needed_primitive": "recover_signal", "n_samples": 32,
        "test_frequencies": [3, 7, 11], "inputs": ["magnitude_spectrum"],
        "outputs": ["recovered_signal"],
        "example": "recover the signal from its magnitude spectrum", "status": "perceived"},
}
SEQUENCES = (
    {"id": "isolated_B", "events": ["B"]},
    {"id": "isolated_C", "events": ["C"]},
    {"id": "repeat_B", "events": ["B", "B"]},
    {"id": "B_then_C", "events": ["B", "C"]},
    {"id": "C_then_B", "events": ["C", "B"]},
)
ARMS = ("faculty", "faculty_plus_operations")


def digest(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def input_lock() -> dict:
    return {"schema_version": 1, "protocol": digest(PROTOCOL), "runner": digest(RUNNER),
            "sources": [digest(ROOT / p) for p in SOURCES], "fixtures": GAPS,
            "sequences": list(SEQUENCES), "arms": list(ARMS),
            "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                         text=True, capture_output=True, check=True).stdout.strip()}


def atomic(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2, default=str) + "\n")
    tmp.replace(path)


def rows(sub, kind: str) -> list[dict]:
    return [{"id": str(n), "attrs": dict(sub.node(n)["attrs"])} for n in sub.nodes(kind)]


def snapshot(sub, native, agent_node) -> dict:
    kinds = ("CapabilityAxis", "PrimitiveRequest", "HeldPrimitive", "Observation", "CapabilityGap")
    receipts = rows(sub, "NativeReflectiveFacultyReceipt")
    return {"codebook_epoch": sub.node(agent_node)["attrs"].get("codebook_epoch"),
            "nodes": {k: rows(sub, k) for k in kinds},
            "latest_native_steps": receipts[-1]["attrs"].get("native_steps") if receipts else None}


def run_one(arm: str, spec: dict) -> dict:
    from substrate.world_adapter import WorldAdapter
    from domains import reflective_faculty as rf
    from domains import substrate_extension as se

    agent = WorldAdapter(seeds=())
    sub, native, agent_node = rf._resolve_agent(agent)
    original = rf.induce_concern
    def patched(target, observation, *, name_hint=None):
        if arm == "faculty_plus_operations":
            heads = [x[0] for x in observation if isinstance(x, (list, tuple)) and x and isinstance(x[0], str)]
            ops = "_".join(rf._key_component(p) for p in sorted(heads))
            name_hint = f"{name_hint}__ops_{ops}"
        return original(target, observation, name_hint=name_hint)
    rf.induce_concern = patched
    events = []
    try:
        for label in spec["events"]:
            attrs = dict(GAPS[label])
            gap = sub.add_node("CapabilityGap", attrs)
            before = snapshot(sub, native, agent_node)
            started_wall, started_cpu = time.perf_counter(), time.process_time()
            result = se.extend_for_gap(agent, gap, verify=True)
            wall, cpu = time.perf_counter() - started_wall, time.process_time() - started_cpu
            after = snapshot(sub, native, agent_node)
            old_obs = {x["id"] for x in before["nodes"]["Observation"]}
            new_obs = [x for x in after["nodes"]["Observation"] if x["id"] not in old_obs]
            events.append({"case": label, "gap_attrs": attrs, "result": result,
                           "new_observations": new_obs, "before": before, "after": after,
                           "axis_delta": len(after["nodes"]["CapabilityAxis"])-len(before["nodes"]["CapabilityAxis"]),
                           "primitive_request_delta": len(after["nodes"]["PrimitiveRequest"])-len(before["nodes"]["PrimitiveRequest"]),
                           "held_primitive_delta": len(after["nodes"]["HeldPrimitive"])-len(before["nodes"]["HeldPrimitive"]),
                           "wall_seconds": wall, "cpu_seconds": cpu})
    finally:
        rf.induce_concern = original
    return {"arm": arm, "sequence_id": spec["id"], "events": events}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or CAPTURE.exists():
            raise SystemExit("refusing to overwrite existing lock/capture")
        atomic(LOCK, input_lock()); print(LOCK.relative_to(ROOT)); return
    locked = json.loads(LOCK.read_text())
    if input_lock() != locked:
        raise SystemExit("source/fixture lock drift")
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    runs = [run_one(arm, spec) for arm in ARMS for spec in SEQUENCES]
    post = input_lock()
    if post != locked:
        raise SystemExit("post-run source/fixture lock drift")
    calls = sum(len(r["events"]) for r in runs)
    capture = {"schema_version": 1, "run_id": "gap-grounder-role-wiring-v1.3-20260929",
               "status": "complete", "input_lock": locked, "post_run_input_lock": post,
               "runs": runs, "process": {"wall_seconds": time.perf_counter()-started_wall,
                                           "cpu_seconds": time.process_time()-started_cpu}}
    atomic(CAPTURE, capture)
    print(json.dumps({"capture": str(CAPTURE.relative_to(ROOT)), "arms": len(ARMS),
                      "sequences_per_arm": len(SEQUENCES), "calls": calls,
                      "wall_seconds": capture["process"]["wall_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
