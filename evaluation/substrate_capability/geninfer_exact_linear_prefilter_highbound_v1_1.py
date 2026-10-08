#!/usr/bin/env python3
"""Source-manifested paired high-bound prefilter smoke with worker timeouts."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/nonlinear_quadratic_geninfer_v2_2.py"
NATIVE = Path("/tmp/ocelot-prefilter-target/release/libsubstrate_rs.so")
OUT = ROOT / "evaluation/reports/geninfer_exact_linear_prefilter_highbound_v1_1_20261006.json"
TIMEOUT_S = 300


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources() -> dict[str, str]:
    paths = [
        Path(__file__).resolve(), RUNNER,
        ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_PREREG_20261006.md",
        ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_1_AMENDMENT_20261006.md",
        ROOT / "runners/dsl/Cargo.toml", ROOT / "runners/dsl/Cargo.lock",
        ROOT / "runners/dsl/src/shape_decode.rs", ROOT / "runners/dsl/src/scale_audit.rs",
        ROOT / "runners/dsl/src/term.rs", ROOT / "runners/dsl/src/jsonio.rs",
        ROOT / "runners/dsl/src/reflect.rs", ROOT / "seeds/shape_decode_loop.json",
    ]
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}


def patched_worker():
    source = RUNNER.read_text()
    needle = 'sub.set_attr(agent, "gen_quadratic_enabled", 1.0)'
    replacement = needle + '\n        sub.set_attr(agent, "gen_linear_exact_enabled", 1.0)'
    if source.count(needle) != 1:
        raise RuntimeError("v2.2 worker insertion point changed")
    spec = importlib.util.spec_from_file_location("prefilter_highbound_child", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load native worker")
    module = importlib.util.module_from_spec(spec)
    exec(compile(source.replace(needle, replacement), str(RUNNER), "exec"), module.__dict__)
    return module


def child(audit: bool) -> int:
    row = patched_worker().worker({
        "condition": "cubic_out_of_family", "repeat": 1, "feature": "on",
        "audit": audit, "worker_id": f"prefilter_highbound_v11_a{int(audit)}",
    }, NATIVE)
    print(json.dumps(row, sort_keys=True, separators=(",", ":")))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child-audit", type=int, choices=(0, 1))
    args = parser.parse_args()
    if args.child_audit is not None:
        return child(bool(args.child_audit))
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    if not NATIVE.is_file():
        raise SystemExit(f"missing prefilter native binary: {NATIVE}")
    lock_sources = sources()
    binary_sha = sha(NATIVE)
    rows = []
    for audit in (False, True):
        start = time.perf_counter_ns()
        try:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--child-audit", str(int(audit))],
                                  cwd=ROOT, text=True, capture_output=True, timeout=TIMEOUT_S, check=False)
            elapsed = time.perf_counter_ns() - start
            row = json.loads(proc.stdout.strip()) if proc.returncode == 0 else None
            rows.append({"audit": audit, "exit_code": proc.returncode, "elapsed_ns": elapsed,
                         "worker": row, "stderr": proc.stderr[-4000:]})
        except subprocess.TimeoutExpired as exc:
            rows.append({"audit": audit, "exit_code": "timeout", "elapsed_ns": time.perf_counter_ns() - start,
                         "worker": None, "stdout_tail": (exc.stdout or b"")[-2000:].decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")[-2000:]})
    if sources() != lock_sources or sha(NATIVE) != binary_sha:
        raise SystemExit("source or native binary changed during the high-bound run")
    report = {
        "schema": "GenInferExactLinearPrefilterHighBoundV1_1",
        "status": "raw_capture",
        "condition": "cubic_out_of_family",
        "timeout_seconds_per_worker": TIMEOUT_S,
        "comparison": "same prefilter-enabled binary; runtime gate on; audit-off timing and audit-on counter worker",
        "build_command": "CARGO_TARGET_DIR=/tmp/ocelot-prefilter-target cargo build --release --lib --features geninfer_quadratic_map_solver,geninfer_linear_exact_prefilter",
        "native_binary": {"path": str(NATIVE), "sha256": binary_sha},
        "rustc": subprocess.run(["rustc", "--version"], check=True, capture_output=True, text=True).stdout.strip(),
        "platform": platform.platform(), "sources_sha256": lock_sources,
        "workers": rows,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
