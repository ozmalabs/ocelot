#!/usr/bin/env python3
"""Locked forward/inverse spectral-gap runs with independent numerical oracle."""
from __future__ import annotations

import cmath
import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_SPECTRAL_IO_ORACLE_V1_5_PREREG_20260929.md"
RUNNER = Path(__file__).resolve()
LOCK = ROOT / "evaluation/substrate_capability/spectral_io_oracle_v1_5_lock_20260929.json"
OUT = ROOT / "evaluation/reports/spectral_io_oracle_v1_5"
CAPTURE = OUT / "capture.json"
SOURCES = (
    "domains/substrate_extension.py", "domains/reflective_faculty.py",
    "domains/self_verification.py", "domains/self_capability_collapse.py",
    "substrate/boot_core.py", "substrate/world_adapter.py", "substrate/graph.py",
    "substrate/seed_loader.py", "seeds/composer_faculty_pipeline.json",
    "seeds/shape_decode_loop.json", "runners/dsl/src/shape_decode.rs",
    "runners/dsl/src/term.rs", "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
N = 32
FACULTY = "shared_family"
GAPS = {
    "B": {"faculty": FACULTY, "observation": [
        ["spectral_value", "signal", "magnitude"],
        ["log_scale", "magnitude", "value"]],
        "needed_primitive": "spectral_value", "n_samples": N,
        "test_frequencies": [3, 7, 11], "inputs": ["signal"], "outputs": ["spectrum"],
        "example": "per-bin log magnitude", "status": "perceived"},
    "C": {"faculty": FACULTY, "observation": [
        ["spectral_value", "magnitude_spectrum", "recovered_signal"],
        ["log_scale", "recovered_signal", "magnitude_spectrum"]],
        "needed_primitive": "recover_signal", "n_samples": N,
        "test_frequencies": [3, 7, 11], "inputs": ["magnitude_spectrum"],
        "outputs": ["recovered_signal"],
        "example": "recover the signal from its magnitude spectrum", "status": "perceived"},
}
ARMS = ("faculty", "faculty_plus_operations")
CASES = tuple({"id": f"{label}_rep{rep}", "label": label, "replicate": rep}
              for label in ("B", "C") for rep in (1, 2, 3))


def digest(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def input_lock() -> dict:
    return {"schema_version": 1, "protocol": digest(PROTOCOL), "runner": digest(RUNNER),
            "sources": [digest(ROOT / p) for p in SOURCES], "fixtures": GAPS,
            "arms": list(ARMS), "cases": list(CASES), "n_samples": N,
            "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                         text=True, capture_output=True, check=True).stdout.strip()}


def atomic(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2, default=str) + "\n")
    tmp.replace(path)


def signals() -> dict[str, list[float]]:
    tone = [math.cos(2 * math.pi * 3 * n / N) for n in range(N)]
    mixed = [0.8 * math.cos(2 * math.pi * 3 * n / N)
             + 0.3 * math.cos(2 * math.pi * 7 * n / N) for n in range(N)]
    impulse = [1.0 if n == 5 else 0.0 for n in range(N)]
    return {"tone_3": tone, "mixed_3_7": mixed, "shifted_impulse": impulse}


def expected_logmag(values: list[float]) -> list[float]:
    return [math.log(abs(sum(float(x) * cmath.exp(-2j * math.pi * k * n / len(values))
                             for n, x in enumerate(values))) + 1e-9)
            for k in range(len(values) // 2 + 1)]


def observations(tree: dict) -> tuple[list[str], list[str]]:
    vars_seen, ops_seen = set(), set()
    def walk(x):
        if isinstance(x, dict):
            if x.get("type") == "Var" and isinstance(x.get("name"), str):
                vars_seen.add(x["name"])
            if isinstance(x.get("type"), str):
                ops_seen.add(x["type"])
            for v in x.values(): walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x: walk(v)
    walk(tree)
    return sorted(vars_seen), sorted(ops_seen)


def direct_oracle(native, tree: dict) -> dict:
    reports = {}
    for name, x in signals().items():
        pairs = [(float(n), float(v)) for n, v in enumerate(x)]
        got = [float(native.evaluate(tree, {"sig": pairs, "k": float(k), "N": float(N)}))
               for k in range(N // 2 + 1)]
        want = expected_logmag(x)
        errors = [abs(a - b) for a, b in zip(got, want)]
        reports[name] = {"actual": got, "expected": want,
                         "max_abs_error": max(errors, default=0.0),
                         "passed": len(got) == len(want) and max(errors, default=0.0) <= 1e-6}
    return reports


def inverse_witness() -> dict:
    x = [0.0] * N
    x[0], x[1] = 1.0, 2.0
    y = [0.0] * N
    y[0], y[-1] = 1.0, 2.0
    mx, my = expected_magnitude(x), expected_magnitude(y)
    return {"x": x, "y": y, "x_not_equal_y": x != y,
            "magnitude_x": mx, "magnitude_y": my,
            "max_abs_magnitude_difference": max(abs(a-b) for a,b in zip(mx,my))}


def expected_magnitude(values: list[float]) -> list[float]:
    return [abs(sum(float(x) * cmath.exp(-2j * math.pi * k * n / len(values))
                    for n, x in enumerate(values)))
            for k in range(len(values) // 2 + 1)]


def run_one(arm: str, case: dict) -> dict:
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
    try:
        gap = sub.add_node("CapabilityGap", dict(GAPS[case["label"]]))
        start_wall, start_cpu = time.perf_counter(), time.process_time()
        result = se.extend_for_gap(agent, gap, verify=True)
        wall, cpu = time.perf_counter()-start_wall, time.process_time()-start_cpu
    finally:
        rf.induce_concern = original
    tree = result.get("term_tree")
    oracle = direct_oracle(native, tree) if isinstance(tree, dict) else {}
    vars_seen, ops_seen = observations(tree) if isinstance(tree, dict) else ([], [])
    return {"arm": arm, "case": case, "gap_attrs": GAPS[case["label"]],
            "result": result, "returned_term_vars": vars_seen,
            "returned_term_ops": ops_seen, "independent_forward_oracle": oracle,
            "graph": {"axis_count": len(list(sub.nodes("CapabilityAxis"))),
                      "held_primitive_count": len(list(sub.nodes("HeldPrimitive"))),
                      "primitive_request_count": len(list(sub.nodes("PrimitiveRequest"))),
                      "held_primitive_names": [sub.node(n)["attrs"].get("name") for n in sub.nodes("HeldPrimitive")],
                      "primitive_request_names": [sub.node(n)["attrs"].get("name") for n in sub.nodes("PrimitiveRequest")],
                      "codebook_epoch": sub.node(agent_node)["attrs"].get("codebook_epoch")},
            "wall_seconds": wall, "cpu_seconds": cpu}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or CAPTURE.exists(): raise SystemExit("refusing to overwrite existing lock/capture")
        atomic(LOCK, input_lock()); print(LOCK.relative_to(ROOT)); return
    lock = json.loads(LOCK.read_text())
    if input_lock() != lock: raise SystemExit("source/fixture lock drift")
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    rows = [run_one(arm, case) for arm in ARMS for case in CASES]
    witness = inverse_witness()
    post = input_lock()
    if post != lock: raise SystemExit("post-run source/fixture lock drift")
    capture = {"schema_version": 1, "run_id": "spectral-io-oracle-v1.5-20260929",
               "status": "complete", "input_lock": lock, "post_run_input_lock": post,
               "cases": rows, "inverse_nonidentifiability_witness": witness,
               "process": {"wall_seconds": time.perf_counter()-started_wall,
                           "cpu_seconds": time.process_time()-started_cpu}}
    atomic(CAPTURE, capture)
    print(json.dumps({"capture": str(CAPTURE.relative_to(ROOT)), "cases": len(rows),
                      "wall_seconds": capture["process"]["wall_seconds"]}, indent=2))


if __name__ == "__main__": main()
