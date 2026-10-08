#!/usr/bin/env python3
"""Source-locked direct-Term and rule-level changing-map baseline."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/TIMEINFER_CHANGING_MAP_EXTRAPOLATION_V1_PREREG_20261006.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_timeinfer_changing_map_extrapolation_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/timeinfer_changing_map_extrapolation_v1_lock_20261006.json"
OUT = ROOT / "evaluation/reports/timeinfer_changing_map_extrapolation_v1_20261006.json"
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]
DT = ["pred", "coord:r", "coord:c", "val"]
FIELDS = ("explained", "kind", "order", "predicted")
CASES = ("translate_order2", "changing_linear_shear", "changing_quadratic_shear",
         "static_quadratic_shear", "random_translation")
SCHEDULE = [(case, rep) for case in CASES for rep in range(3)]
SOURCES = (
    "domains/engine_provenance.py", "domains/reflective_faculty.py",
    "substrate/boot_core.py", "substrate/seed_loader.py",
    "runners/dsl/src/shape_decode.rs",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "seeds/time_axis.json", "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs() -> dict:
    return {"files": {str(path.relative_to(ROOT)): sha(path)
                       for path in (RUNNER, PROTOCOL, ANALYZER, *(ROOT / p for p in SOURCES))}}


def sequence(case: str) -> tuple[list, list]:
    frames = [BASE]
    cur = BASE
    if case == "translate_order2":
        offsets = [1, 2, 3, 4, 5, 6]
        for dr in offsets:
            cur = [["cell", r + dr, c, v] for _, r, c, v in cur]
            frames.append(cur)
        dr = 7
        held = [["cell", r + dr, c, v] for _, r, c, v in cur]
        return frames, held
    if case == "random_translation":
        for dr in (1, 3, -2, 6, -1, 4):
            cur = [["cell", r + dr, c, v] for _, r, c, v in cur]
            frames.append(cur)
        dr = 2
        return frames, [["cell", r + dr, c, v] for _, r, c, v in cur]
    for k in range(1, 7):
        coeff = 1 if case == "static_quadratic_shear" else k
        if case in ("changing_linear_shear",):
            cur = [["cell", r, c + coeff * r, v] for _, r, c, v in cur]
        else:
            cur = [["cell", r, c + coeff * r * r, v] for _, r, c, v in cur]
        frames.append(cur)
    next_coeff = 1 if case == "static_quadratic_shear" else 7
    held = [["cell", r, c + next_coeff * r if case == "changing_linear_shear"
             else c + next_coeff * r * r, v] for _, r, c, v in cur]
    return frames, held


def boot():
    from domains.engine_provenance import assert_measuring_engine
    from domains import reflective_faculty as rf
    from substrate.boot_core import boot_core
    from substrate.seed_loader import manifest_for
    assert_measuring_engine()
    sub, agent = boot_core()
    native = rf._native_eval2(sub)
    rf._ensure_shape_decode_loop(sub, native, agent)
    native.load_seed_manifest(manifest_for("time_axis"), agent)
    sub.set_attr(agent, "time_infer_enabled", 1.0)
    sub.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
                 "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return sub, agent, native


def worker(case: str, replicate: int) -> dict:
    from domains.engine_provenance import provenance_line
    frames, held = sequence(case)
    sub, agent, native = boot()
    started = time.perf_counter_ns()
    direct = {}
    for field in FIELDS:
        direct[field] = native.evaluate(
            {"type": "TimeInfer", "sequence": {"type": "Lit", "value": frames},
             "codebook_type": "ShapeSignature", "max_b": 8, "field": field}, {})
    elapsed_ns = time.perf_counter_ns() - started
    predicted = direct["predicted"]
    exact_transfer = isinstance(predicted, list) and sorted(map(tuple, predicted)) == sorted(map(tuple, held))

    ruled_sub, ruled_agent, ruled_native = boot()
    observation = ruled_sub.add_node("Observation", {"frames": frames, "dim_types": DT,
                                        "status": "motion_seq", "key": [case]})
    ruled_sub.add_edge(ruled_agent, "observed", observation)
    ruled_native.run_rules()
    status = ruled_sub.node(observation)["attrs"].get("status")
    mints = []
    for node in ruled_sub.nodes("LatentDimension"):
        attrs = ruled_sub.node(node)["attrs"]
        if attrs.get("name") == "latent:time":
            mints.append({key: attrs.get(key) for key in
                          ("generator_kind", "offset", "matrix", "order", "coeffs", "window")})
    return {"case": case, "replicate": replicate, "source_stable": True,
            "engine_provenance": provenance_line(), "frame_count": len(frames),
            "frames": frames, "withheld_next_frame": held, "direct_fields": direct,
            "direct_elapsed_ns": elapsed_ns, "exact_heldout_transfer": exact_transfer,
            "rule_observation_status": status, "time_mints": mints}


def main() -> int:
    args = sys.argv[1:]
    if args == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite existing benchmark artifacts")
        LOCK.write_text(json.dumps({"schema": "TimeInferChangingMapV1Lock",
                                    "inputs": inputs(), "schedule": SCHEDULE},
                                   indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0
    if len(args) == 3 and args[0] == "--worker":
        print(json.dumps(worker(args[1], int(args[2])), sort_keys=True, separators=(",", ":")))
        return 0
    if args:
        raise SystemExit("usage: timeinfer_changing_map_extrapolation_v1.py [--lock|--worker CASE REP]")
    locked = json.loads(LOCK.read_text())
    if locked.get("inputs") != inputs() or locked.get("schedule") != [list(x) for x in SCHEDULE]:
        raise SystemExit("missing or stale source lock")
    rows = []
    for case, rep in SCHEDULE:
        env = dict(os.environ, OZMA_NO_LLM="1", OZMA_SEED_PERSIST_DISABLED="1")
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", case, str(rep)],
                              cwd=ROOT, env=env, text=True, capture_output=True, timeout=300)
        if proc.returncode:
            raise RuntimeError(f"worker failed {case}/{rep}: {proc.stderr[-1800:]}")
        rows.append(json.loads(proc.stdout))
        print(f"completed={case}/{rep}", file=sys.stderr, flush=True)
    post = inputs()
    if post != locked["inputs"] or [(r["case"], r["replicate"]) for r in rows] != SCHEDULE:
        raise RuntimeError("source stability or schedule mismatch")
    payload = {"schema": "TimeInferChangingMapV1", "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "host": platform.platform(), "locked_inputs": locked["inputs"], "post_run_inputs": post,
               "source_stable": True, "task_schedule": [list(x) for x in SCHEDULE], "workers": rows}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(), "workers": len(rows),
                      "source_stable": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
