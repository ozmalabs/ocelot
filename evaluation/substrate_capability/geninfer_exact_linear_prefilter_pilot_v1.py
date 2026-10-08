#!/usr/bin/env python3
"""Paired runtime-gate pilot for the opt-in exact-linear GenInfer prefilter.

This is an engineering smoke capture, not the preregistered v1 admission run.
It reuses the v2.2 worker's frame construction, closure, reload and transfer
checks, but compares the prefilter gate off/on inside one feature-on binary.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import random
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/nonlinear_quadratic_geninfer_v2_2.py"
NATIVE = Path(os.environ.get("GENINFER_PREFILTER_NATIVE", "/tmp/ocelot-prefilter-target/release/libsubstrate_rs.so"))
OUT = ROOT / "evaluation/reports/geninfer_exact_linear_prefilter_pilot_v1_20261006.json"
REPEATS = 10
CONDITION = "linear_positive"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def worker_module():
    src = RUNNER.read_text()
    old = 'sub.set_attr(agent, "gen_quadratic_enabled", 1.0)'
    replacement = old + '\n        if case.get("prefilter_gate"):\n            sub.set_attr(agent, "gen_linear_exact_enabled", 1.0)'
    if src.count(old) != 1:
        raise RuntimeError("v2.2 worker gate insertion point changed")
    spec = importlib.util.spec_from_file_location("prefilter_pilot_v2_2_worker", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load v2.2 worker module")
    module = importlib.util.module_from_spec(spec)
    exec(compile(src.replace(old, replacement), str(RUNNER), "exec"), module.__dict__)
    return module


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    if not NATIVE.is_file():
        raise SystemExit(f"feature-on native binary missing: {NATIVE}")
    module = worker_module()
    schedule = [{"repeat": i, "gate": gate, "audit": audit}
                for i in range(1, REPEATS + 1) for gate in (False, True) for audit in (False, True)]
    random.Random(20261006).shuffle(schedule)
    rows = []
    started = time.time()
    for i, item in enumerate(schedule):
        case = {"condition": CONDITION, "repeat": item["repeat"], "feature": "on",
                "audit": item["audit"], "worker_id": f"prefilter_pilot_{i:02d}",
                "prefilter_gate": item["gate"]}
        row = module.worker(case, NATIVE)
        row["prefilter_gate"] = item["gate"]
        row["pilot_repeat"] = item["repeat"]
        rows.append(row)
    source_paths = [
        Path(__file__).resolve(),
        ROOT / "evaluation/substrate_capability/analyze_geninfer_exact_linear_prefilter_pilot_v1.py",
        RUNNER,
        ROOT / "runners/dsl/Cargo.toml",
        ROOT / "runners/dsl/Cargo.lock",
        ROOT / "runners/dsl/src/shape_decode.rs",
        ROOT / "runners/dsl/src/term.rs",
        ROOT / "runners/dsl/src/jsonio.rs",
        ROOT / "runners/dsl/src/reflect.rs",
        ROOT / "runners/dsl/src/scale_audit.rs",
        ROOT / "seeds/shape_decode_loop.json",
    ]
    payload = {
        "schema": "GenInferExactLinearPrefilterPilotV1",
        "status": "pilot_not_admission",
        "condition": CONDITION,
        "repeats_per_gate": REPEATS,
        "schedule": schedule,
        "environment": {"platform": platform.platform(), "python": platform.python_version(),
                        "rustc": subprocess.run(["rustc", "--version"], check=True, capture_output=True, text=True).stdout.strip(),
                        "build_command": "CARGO_TARGET_DIR=/tmp/ocelot-prefilter-target cargo build --release --lib --features geninfer_quadratic_map_solver,geninfer_linear_exact_prefilter",
                        "started_unix": started, "elapsed_s": time.time() - started},
        "native_binary": {"path": str(NATIVE.resolve()), "sha256": sha(NATIVE)},
        "sources_sha256": {str(p.relative_to(ROOT)): sha(p) for p in source_paths},
        "comparison": "same feature-on binary; runtime prefilter gate off versus on",
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
